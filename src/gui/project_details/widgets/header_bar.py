"""
Header Bar Widget

A professional header bar displaying project information and action buttons.
Shows project title, metadata, and provides export/print functionality.
"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Signal

from src.gui.resources.resources import get_icon
from ..constants import HEADER_HEIGHT, ICON_SIZE


class HeaderBar(QWidget):
    """
    Header bar widget displaying project information and actions.

    Layout:
    - Left: Project title (h2) + metadata row (Order, Typ, Created)
    - Right: Export and Print buttons with proper tooltips
    """

    sig_export = Signal()
    sig_print = Signal()
    sig_client = Signal()

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
        self.setMinimumHeight(HEADER_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setProperty("class", "header-bar")

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # Left section: Project info
        self._create_info_section(layout)

        # Stretch to push buttons to right
        layout.addStretch()

        # Right section: Action buttons
        self._create_action_buttons(layout)

    def _create_info_section(self, parent_layout: QHBoxLayout):
        """Create the project information section."""
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        # Project title (h2 style)
        self.title_label = QLabel("Projekt")
        self.title_label.setProperty("class", "project-title")
        font = self.title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        info_layout.addWidget(self.title_label)

        # Metadata row
        metadata_layout = QHBoxLayout()
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(16)

        # Order number
        self.order_label = QLabel("Order: -")
        self.order_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.order_label)

        # Kitchen type
        self.type_label = QLabel("Typ: -")
        self.type_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.type_label)

        # Created date
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
        self.export_btn.setProperty("class", "secondary")
        self.export_btn.setToolTip("Eksportuj projekt")
        self.export_btn.clicked.connect(self.sig_export.emit)
        parent_layout.addWidget(self.export_btn)

        # Print button
        self.print_btn = QPushButton("Drukuj")
        self.print_btn.setIcon(get_icon("print"))
        self.print_btn.setIconSize(ICON_SIZE)
        self.print_btn.setProperty("class", "secondary")
        self.print_btn.setToolTip("Drukuj projekt")
        self.print_btn.clicked.connect(self.sig_print.emit)
        parent_layout.addWidget(self.print_btn)

    def _apply_styling(self):
        """Apply styling to the header bar."""
        self.setStyleSheet("""
            HeaderBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
            }
            QLabel[class="project-title"] {
                color: #1a202c;
                font-weight: 600;
            }
            QLabel[class="metadata"] {
                color: #64748b;
                font-size: 12px;
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

        # Update labels
        title = f"{name}"
        if order_number:
            title += f" - #{order_number}"
        self.title_label.setText(title)

        self.order_label.setText(f"Order: {order_number or '-'}")
        self.type_label.setText(f"Typ: {kitchen_type or '-'}")
        self.date_label.setText(f"Utworzono: {created_date or '-'}")
