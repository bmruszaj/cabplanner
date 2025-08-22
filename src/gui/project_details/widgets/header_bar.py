"""
Header Bar widget for project details.

This widget displays project title, metadata, and action buttons like export and print.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
)

from ..constants import (
    HEADER_HEIGHT,
    COLORS,
    ICON_SIZE,
    CONTENT_MARGINS,
    LAYOUT_SPACING,
    CSS_HEADER_BAR,
    HEADER_STYLESHEET,
    SHORTCUTS,
    TOOLTIP_EXPORT,
    TOOLTIP_PRINT,
)

logger = logging.getLogger(__name__)


class HeaderBar(QWidget):
    """
    Header bar widget displaying project information and actions.

    Shows:
    - Project title (h2 styling)
    - Order number, kitchen type, created date
    - Action buttons (export, print)
    """

    # Signals
    sig_export = Signal()
    sig_print = Signal()

    def __init__(self, parent=None):
        """
        Initialize the header bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Set object name for CSS styling
        self.setObjectName(CSS_HEADER_BAR)
        self.setFixedHeight(HEADER_HEIGHT)

        # Apply modern header stylesheet
        self.setStyleSheet(HEADER_STYLESHEET)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the header bar UI with modern styling."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*CONTENT_MARGINS)
        layout.setSpacing(LAYOUT_SPACING * 2)  # Double spacing for header

        # Left side - Project information
        info_widget = self._create_info_section()
        layout.addWidget(info_widget)

        layout.addStretch()

        # Right side - Action buttons
        actions_widget = self._create_actions_section()
        layout.addWidget(actions_widget)

    def _create_info_section(self) -> QWidget:
        """Create the project information section with modern typography."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(LAYOUT_SPACING // 2)

        # Project title (h2 style)
        self.title_label = QLabel("Project Title")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.title_label)

        # Metadata row with consistent spacing
        metadata_layout = QHBoxLayout()
        metadata_layout.setSpacing(LAYOUT_SPACING * 2)

        # Order number
        self.order_label = QLabel("Order: —")
        self.order_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        metadata_layout.addWidget(self.order_label)

        # Kitchen type
        self.kitchen_type_label = QLabel("Type: —")
        self.kitchen_type_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        metadata_layout.addWidget(self.kitchen_type_label)

        # Created date
        self.created_date_label = QLabel("Created: —")
        self.created_date_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        metadata_layout.addWidget(self.created_date_label)

        metadata_layout.addStretch()
        layout.addLayout(metadata_layout)

        return widget

    def _create_actions_section(self) -> QWidget:
        """Create the action buttons section with modern styling and shortcuts."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(LAYOUT_SPACING)

        # Export button with keyboard shortcut
        self.export_btn = QPushButton("Export")
        self.export_btn.setShortcut(SHORTCUTS["export"])
        self.export_btn.setToolTip(f"{TOOLTIP_EXPORT} ({SHORTCUTS['export']})")
        self.export_btn.setIconSize(ICON_SIZE)
        layout.addWidget(self.export_btn)

        # Print button with keyboard shortcut
        self.print_btn = QPushButton("Print")
        self.print_btn.setShortcut(SHORTCUTS["print"])
        self.print_btn.setToolTip(f"{TOOLTIP_PRINT} ({SHORTCUTS['print']})")
        self.print_btn.setIconSize(ICON_SIZE)
        layout.addWidget(self.print_btn)

        return widget

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.export_btn.clicked.connect(self.sig_export.emit)
        self.print_btn.clicked.connect(self.sig_print.emit)

    def set_project_info(
        self,
        title: str,
        order_number: str = "",
        kitchen_type: str = "",
        created_date: str = "",
    ) -> None:
        """
        Set the project information to display.

        Args:
            title: Project title
            order_number: Project order number
            kitchen_type: Kitchen type (e.g. 'LOFT', 'CLASSIC')
            created_date: Created date string
        """
        self.title_label.setText(title)
        self.order_label.setText(
            f"Order: {order_number}" if order_number else "Order: —"
        )
        self.kitchen_type_label.setText(
            f"Type: {kitchen_type}" if kitchen_type else "Type: —"
        )
        self.created_date_label.setText(
            f"Created: {created_date}" if created_date else "Created: —"
        )

    def get_title(self) -> str:
        """Get the current project title."""
        return self.title_label.text()
