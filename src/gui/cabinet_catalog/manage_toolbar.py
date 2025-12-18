"""
Manage toolbar for catalog operations.

Provides New, Edit, Delete actions for catalog management.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction

from src.gui.resources.styles import get_theme, PRIMARY
from src.gui.resources.resources import get_icon


class ManageToolbar(QWidget):
    """Toolbar for catalog management actions."""

    # Signals
    sig_new = Signal()
    sig_edit = Signal()
    sig_delete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()
        self._apply_styles()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Create action buttons
        self.btn_new = self._create_tool_button("add", "Nowy", "Utwórz nowy typ szafki")
        self.btn_edit = self._create_tool_button(
            "edit", "Edytuj", "Edytuj wybrany typ szafki"
        )
        self.btn_delete = self._create_tool_button(
            "delete", "Usuń", "Usuń wybrany typ szafki"
        )

        # Add buttons to layout
        layout.addWidget(self.btn_new)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Import placeholder (for future)
        self.btn_import = self._create_tool_button(
            "catalog", "Import", "Import cabinet types from file"
        )
        self.btn_import.setEnabled(False)  # Placeholder for future implementation
        layout.addWidget(self.btn_import)

        # Add stretch to align buttons left
        layout.addStretch()

        # Store actions for external access
        self.act_new = QAction("New", self)
        self.act_edit = QAction("Edit", self)
        self.act_delete = QAction("Delete", self)

        # Set initial enabled state
        self.set_enabled_for_selection(False)

    def _create_tool_button(
        self, icon_name: str, text: str, tooltip: str
    ) -> QToolButton:
        """Create a tool button with icon and text."""
        button = QToolButton()
        button.setIcon(get_icon(icon_name))
        button.setText(text)
        button.setToolTip(tooltip)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setIconSize(QSize(16, 16))
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return button

    def _setup_connections(self):
        """Setup signal connections."""
        self.btn_new.clicked.connect(self.sig_new.emit)
        self.btn_edit.clicked.connect(self.sig_edit.emit)
        self.btn_delete.clicked.connect(self.sig_delete.emit)

        # Connect actions
        self.act_new.triggered.connect(self.sig_new.emit)
        self.act_edit.triggered.connect(self.sig_edit.emit)
        self.act_delete.triggered.connect(self.sig_delete.emit)

    def _apply_styles(self):
        """Apply styling to the toolbar."""
        self.setStyleSheet(
            get_theme()
            + f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px 12px;
                margin: 2px;
                font-size: 10pt;
                color: #333333;
            }}
            QToolButton:hover {{
                background-color: #F0F0F0;
                border-color: #D0D0D0;
            }}
            QToolButton:pressed {{
                background-color: #E0E0E0;
                border-color: {PRIMARY};
            }}
            QToolButton:disabled {{
                color: #999999;
                background-color: transparent;
            }}
            QFrame {{
                color: #D0D0D0;
                margin: 4px 8px;
            }}
        """
        )

    def set_enabled_for_selection(self, has_selection: bool):
        """Enable/disable actions based on selection."""
        # New is always enabled
        self.btn_new.setEnabled(True)
        self.act_new.setEnabled(True)

        # Edit, Delete require selection
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

        self.act_edit.setEnabled(has_selection)
        self.act_delete.setEnabled(has_selection)
