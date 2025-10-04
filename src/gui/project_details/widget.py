"""
Project Details Widget

A widget-based version of project details that doesn't inherit from QDialog.
This eliminates any possibility of dialog flashing.
"""

import logging
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QTimer
from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project
from src.gui.project_details.view import ProjectDetailsView

logger = logging.getLogger(__name__)


class ProjectDetailsWidget(QWidget):
    """
    A widget-based wrapper for project details that doesn't inherit from QDialog.
    This completely eliminates any dialog flashing issues.
    """

    # Signals to communicate with parent
    closed = Signal()

    def __init__(self, session: Session, project: Project, parent=None):
        print(
            f"[WIDGET DEBUG] Creating ProjectDetailsWidget for project: {project.name}"
        )
        super().__init__(parent)
        self.session = session
        self.project = project

        # Start timing for widget setup
        import time as _time

        self._dbg_start_time = _time.perf_counter()

        # Start completely hidden to prevent any flash during setup
        self.setVisible(False)
        self.hide()

        print(
            f"[WIDGET DEBUG][{(_time.perf_counter() - self._dbg_start_time) * 1000:.1f}ms] Creating minimal UI..."
        )
        # Create minimal UI immediately - just a layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Make this placeholder expand to fill the stacked widget area so
        # it doesn't render as a small 'mini window' while heavy UI is deferred.
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create a simple loading label initially
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QSpacerItem

        self.loading_label = QLabel("Ładowanie szczegółów projektu...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #666; font-size: 14px; padding: 50px;")
        # Let the label expand to take available space
        self.loading_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.loading_label)
        # Add an explicit spacer we can remove later (prevents leftover top gap)
        self._loading_spacer = QSpacerItem(
            0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        layout.addItem(self._loading_spacer)

        # Defer the heavy UI setup to prevent flash
        self.details_view = None
        print(
            f"[WIDGET DEBUG][{(_time.perf_counter() - self._dbg_start_time) * 1000:.1f}ms] Minimal UI created, deferring heavy setup..."
        )

        QTimer.singleShot(10, self._setup_heavy_ui)  # Very small delay

    def _setup_heavy_ui(self):
        """Set up the actual heavy UI components after initial widget is shown."""
        import time as _time

        print(
            f"[WIDGET DEBUG][{(_time.perf_counter() - self._dbg_start_time) * 1000:.1f}ms] Setting up heavy UI..."
        )

        # Remove loading label and spacer so content starts at top
        if hasattr(self, "loading_label"):
            try:
                self.loading_label.hide()
                self.layout().removeWidget(self.loading_label)
                self.loading_label.deleteLater()
            except Exception:
                pass

        if hasattr(self, "_loading_spacer") and self._loading_spacer:
            try:
                self.layout().removeItem(self._loading_spacer)
            except Exception:
                pass
            self._loading_spacer = None

        # NOW create the actual ProjectDetailsView
        self.details_view = ProjectDetailsView(
            session=self.session,
            project=self.project,
            modal=False,
            parent=self,
        )

        # Ensure the embedded view starts hidden too
        self.details_view.setVisible(False)
        self.details_view.hide()

        # Force it to behave as a widget, not a dialog
        self.details_view.setWindowFlags(Qt.Widget)

        # Hide the dialog button box since we're embedding it
        if hasattr(self.details_view, "button_box"):
            try:
                self.details_view.button_box.hide()
            except Exception:
                pass

        # Add the details view to our layout
        try:
            self.layout().addWidget(self.details_view)
        except Exception:
            pass

        # Show the details view
        try:
            self.details_view.setVisible(True)
            self.details_view.show()
        except Exception:
            pass

        import time as _time2

        print(
            f"[WIDGET DEBUG][{(_time2.perf_counter() - self._dbg_start_time) * 1000:.1f}ms] Heavy UI setup complete"
        )

    def closeEvent(self, event):
        """Handle close event."""
        self.closed.emit()
        super().closeEvent(event)

    def showEvent(self, event):
        """Trigger data loading when widget is shown."""
        super().showEvent(event)

        # Only trigger embedded view's showEvent if details_view exists and data hasn't been pre-loaded
        if (
            self.details_view
            and hasattr(self.details_view, "showEvent")
            and hasattr(self.details_view, "_data_loaded")
            and not self.details_view._data_loaded
        ):
            # Create a mock QShowEvent and trigger it
            from PySide6.QtGui import QShowEvent

            mock_event = QShowEvent()
            self.details_view.showEvent(mock_event)
