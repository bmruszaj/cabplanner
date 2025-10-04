"""
Catalog Card Widget

Individual card widget for displaying catalog items in the grid view.
Supports selection, double-click activation, and quick add functionality.
"""

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtGui import QFont, QMouseEvent

from .catalog_models import CatalogItem
from ..resources.styles import (
    PRIMARY,
    PRIMARY_DARK,
    PRIMARY_LIGHT,
    BG_LIGHT_ALT,
    BORDER_LIGHT,
)


class CatalogCard(QWidget):
    """
    Card widget for displaying a catalog item.

    Features:
    - Single click for selection
    - Double click for quick add
    - Quick add button
    - Hover effects
    """

    sig_select = Signal(int)  # item_id - emitted on single click
    sig_activate = Signal(int)  # item_id - emitted on double click or quick add

    def __init__(self, item: CatalogItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.item_id = item.id
        self._selected = False

        self.setObjectName("catalogCard")
        self.setFixedSize(QSize(280, 160))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._setup_ui()
        self._setup_styling()

    def _setup_ui(self):
        """Set up the card UI layout."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header with title and quick add button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Title
        self.title_label = QLabel(self.item.name)
        title_font = QFont()
        title_font.setWeight(QFont.Weight.Medium)
        title_font.setPointSize(11)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)

        # Quick add button
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(QSize(24, 24))
        self.add_button.setProperty("class", "quick-add-btn")
        self.add_button.setToolTip("Szybko dodaj do projektu")
        self.add_button.clicked.connect(lambda: self.sig_activate.emit(self.item_id))

        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.add_button)
        layout.addLayout(header_layout)

        # Code and dimensions
        self.code_label = QLabel(self.item.code)
        code_font = QFont()
        code_font.setPointSize(9)
        code_font.setWeight(QFont.Weight.Normal)
        self.code_label.setFont(code_font)
        self.code_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.code_label)

        # Dimensions
        dimensions_text = (
            f"{self.item.width} × {self.item.height} × {self.item.depth} mm"
        )
        self.dimensions_label = QLabel(dimensions_text)
        dim_font = QFont()
        dim_font.setPointSize(9)
        self.dimensions_label.setFont(dim_font)
        self.dimensions_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.dimensions_label)

        # Description (if available)
        if self.item.description:
            self.description_label = QLabel(self.item.description)
            desc_font = QFont()
            desc_font.setPointSize(8)
            self.description_label.setFont(desc_font)
            self.description_label.setStyleSheet("color: #999999;")
            self.description_label.setWordWrap(True)
            self.description_label.setMaximumHeight(30)
            layout.addWidget(self.description_label)

        # Add stretch to push content to top
        layout.addStretch()

        # Tags (if available)
        if self.item.tags:
            tags_text = " • ".join(self.item.tags[:3])  # Show max 3 tags
            self.tags_label = QLabel(tags_text)
            tags_font = QFont()
            tags_font.setPointSize(8)
            self.tags_label.setFont(tags_font)
            self.tags_label.setStyleSheet(f"color: {PRIMARY}; font-style: italic;")
            self.tags_label.setMaximumHeight(16)
            layout.addWidget(self.tags_label)

    def _setup_styling(self):
        """Set up card styling."""
        self.setStyleSheet(f"""
            QWidget#catalogCard {{
                background-color: {BG_LIGHT_ALT};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 8px;
            }}
            QWidget#catalogCard:hover {{
                border-color: {PRIMARY};
                box-shadow: 0 2px 8px rgba(10, 118, 108, 0.15);
            }}
            QPushButton[class="quick-add-btn"] {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton[class="quick-add-btn"]:hover {{
                background-color: {PRIMARY_DARK};
            }}
            QPushButton[class="quick-add-btn"]:pressed {{
                background-color: {PRIMARY_DARK};
            }}
        """)

    def set_selected(self, selected: bool):
        """Set card selection state."""
        self._selected = selected
        if selected:
            self.setStyleSheet(
                self.styleSheet()
                + f"""
                QWidget#catalogCard {{
                    border-color: {PRIMARY};
                    background-color: {PRIMARY_LIGHT}22;
                    box-shadow: 0 2px 8px rgba(10, 118, 108, 0.2);
                }}
            """
            )
        else:
            self._setup_styling()  # Reset to default styling

    def is_selected(self) -> bool:
        """Check if card is selected."""
        return self._selected

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.sig_select.emit(self.item_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double click for activation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.sig_activate.emit(self.item_id)
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.sig_activate.emit(self.item_id)
        super().keyPressEvent(event)
