"""
Header Bar Widget

A professional header bar displaying project information and action buttons.
Shows back button, project title, metadata, and provides export functionality.
"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from src.gui.resources.resources import get_icon
from ..constants import HEADER_HEIGHT, ICON_SIZE


class HeaderBar(QWidget):
    """
    Header bar widget displaying project information and actions.

    Layout:
    - Left: Back button + Project title (large) + metadata row
    - Right: Client and Export buttons
    """

    sig_export = Signal()
    sig_client = Signal()
    sig_back = Signal()  # New signal for back navigation

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_name = ""
        self.order_number = ""
        self.kitchen_type = ""
        self.created_date = ""
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Set up the header bar UI layout."""
        self.setMinimumHeight(
            HEADER_HEIGHT + 20
        )  # Slightly taller for better hierarchy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setProperty("class", "header-bar")

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Left section: Back button
        self._create_back_button(layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #e0e0e0; }")
        layout.addWidget(separator)

        # Center section: Project info
        self._create_info_section(layout)

        # Stretch to push buttons to right
        layout.addStretch()

        # Right section: Action buttons
        self._create_action_buttons(layout)

    def _create_back_button(self, parent_layout: QHBoxLayout):
        """Create the back navigation button."""
        self.back_btn = QPushButton("← Projekty")
        self.back_btn.setProperty("class", "back-button")
        self.back_btn.setToolTip("Wróć do listy projektów")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.sig_back.emit)
        self.back_btn.setMinimumWidth(100)
        parent_layout.addWidget(self.back_btn)

    def _create_info_section(self, parent_layout: QHBoxLayout):
        """Create the project information section."""
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        # Project title (large, prominent)
        self.title_label = QLabel("Projekt")
        self.title_label.setProperty("class", "project-title")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        info_layout.addWidget(self.title_label)

        # Metadata row (smaller, secondary)
        metadata_layout = QHBoxLayout()
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(20)

        # Order number with label
        self.order_label = QLabel("Nr zamówienia: -")
        self.order_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.order_label)

        # Kitchen type with label
        self.type_label = QLabel("Typ: -")
        self.type_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.type_label)

        # Created date with label
        self.date_label = QLabel("Utworzono: -")
        self.date_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.date_label)

        # Add stretch to metadata
        metadata_layout.addStretch()

        info_layout.addLayout(metadata_layout)
        parent_layout.addLayout(info_layout)

    def _create_action_buttons(self, parent_layout: QHBoxLayout):
        """Create the action buttons section."""
        # Client button
        self.client_btn = QPushButton("Klient")
        self.client_btn.setIcon(get_icon("info"))
        self.client_btn.setIconSize(ICON_SIZE)
        self.client_btn.setProperty("class", "secondary")
        self.client_btn.setToolTip("Informacje o kliencie")
        self.client_btn.clicked.connect(self.sig_client.emit)
        parent_layout.addWidget(self.client_btn)

        # Export button
        self.export_btn = QPushButton("Eksport")
        self.export_btn.setIcon(get_icon("export"))
        self.export_btn.setIconSize(ICON_SIZE)
        self.export_btn.setProperty("class", "primary")
        self.export_btn.setToolTip("Eksportuj projekt do Word")
        self.export_btn.clicked.connect(self.sig_export.emit)
        parent_layout.addWidget(self.export_btn)

    def _apply_styling(self):
        """Apply styling to the header bar."""
        self.setStyleSheet("""
            HeaderBar {
                background-color: #ffffff;
                border-bottom: 2px solid #e2e8f0;
            }
            QPushButton[class="back-button"] {
                background-color: transparent;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px 16px;
                color: #475569;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton[class="back-button"]:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
                color: #1e293b;
            }
            QPushButton[class="back-button"]:pressed {
                background-color: #e2e8f0;
            }
            QLabel[class="project-title"] {
                color: #0f172a;
                font-weight: 700;
            }
            QLabel[class="metadata"] {
                color: #64748b;
                font-size: 12px;
            }
            QPushButton[class="secondary"] {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 16px;
                color: #475569;
                font-weight: 500;
            }
            QPushButton[class="secondary"]:hover {
                background-color: #f1f5f9;
                border-color: #cbd5e1;
            }
            QPushButton[class="primary"] {
                background-color: #0d9488;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
            }
            QPushButton[class="primary"]:hover {
                background-color: #0f766e;
            }
        """)

    def set_project_info(
        self,
        name: str,
        order_number: str = "",
        kitchen_type: str = "",
        created_date: str = "",
    ):
        """Update project information display."""
        self.project_name = name
        self.order_number = order_number
        self.kitchen_type = kitchen_type
        self.created_date = created_date

        # Update title - just the name, prominent
        self.title_label.setText(name or "Projekt")

        # Update metadata labels
        self.order_label.setText(f"Nr zamówienia: {order_number or '-'}")
        self.type_label.setText(f"Typ: {kitchen_type or '-'}")
        self.date_label.setText(f"Utworzono: {created_date or '-'}")
