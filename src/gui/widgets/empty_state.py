# src/gui/widgets/empty_state.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

from ..resources.resources import get_icon


class EmptyStateWidget(QWidget):
    """UX: Empty state widget for when no projects exist or search yields no results"""

    newProjectRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("new_project").pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title = QLabel()
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("emptyStateTitle")
        layout.addWidget(title)

        # Description
        desc = QLabel()
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setObjectName("emptyStateDesc")
        layout.addWidget(desc)

        # Action button
        self.action_btn = QPushButton()
        self.action_btn.setIcon(get_icon("new_project"))
        self.action_btn.clicked.connect(self.newProjectRequested.emit)
        layout.addWidget(self.action_btn, 0, Qt.AlignCenter)

        self.title_label = title
        self.desc_label = desc

    def set_empty_projects_state(self):
        """Show state for when no projects exist"""
        self.title_label.setText(self.tr("Brak projektów"))
        self.desc_label.setText(
            self.tr(
                "Nie masz jeszcze żadnych projektów. Utwórz swój pierwszy projekt, aby rozpocząć."
            )
        )
        self.action_btn.setText(self.tr("Nowy projekt"))

    def set_no_results_state(self):
        """Show state for when search/filter yields no results"""
        self.title_label.setText(self.tr("Brak wyników"))
        self.desc_label.setText(
            self.tr(
                "Nie znaleziono projektów pasujących do kryteriów wyszukiwania. Spróbuj zmienić filtry."
            )
        )
        self.action_btn.setText(self.tr("Wyczyść filtry"))
