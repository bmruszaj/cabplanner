"""
Empty state widgets for displaying helpful hints when no content is available.

These widgets provide consistent empty state messaging across the application.
"""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)

from ..constants import COLORS

logger = logging.getLogger(__name__)


class EmptyHint(QWidget):
    """
    Reusable empty state widget with customizable message and optional action.

    Features:
    - Centered layout with icon and message
    - Optional action button
    - Consistent styling
    """

    def __init__(self, message: str, action_text: str = "", parent=None):
        """
        Initialize the empty hint widget.

        Args:
            message: The message to display
            action_text: Optional action button text
            parent: Parent widget
        """
        super().__init__(parent)
        self.message = message
        self.action_text = action_text

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the empty hint UI."""
        # Main layout - center everything
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(16)

        # Icon (simple graphic)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(64, 64)
        self._create_icon()
        main_layout.addWidget(self.icon_label)

        # Message
        self.message_label = QLabel(self.message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setWordWrap(True)

        # Style the message
        message_font = QFont()
        message_font.setPointSize(14)
        self.message_label.setFont(message_font)
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS["text_secondary"]};
                font-weight: 500;
            }}
        """)
        main_layout.addWidget(self.message_label)

        # Optional action button
        if self.action_text:
            self.action_btn = QPushButton(self.action_text)
            self.action_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS["button_primary"]};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["button_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS["button_pressed"]};
                }}
            """)
            main_layout.addWidget(self.action_btn)

        # Add some padding around the content
        main_layout.setContentsMargins(32, 32, 32, 32)

    def _create_icon(self) -> None:
        """Create a simple icon for the empty state."""
        # Create a simple empty box icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw a dashed rectangle
        painter.setPen(QColor(COLORS["text_secondary"]))
        painter.setOpacity(0.3)

        # Draw dashed border
        dash_length = 4
        gap_length = 4
        rect_size = 48
        start_x = (64 - rect_size) // 2
        start_y = (64 - rect_size) // 2

        # Top line
        for x in range(start_x, start_x + rect_size, dash_length + gap_length):
            painter.drawLine(
                x, start_y, min(x + dash_length, start_x + rect_size), start_y
            )

        # Bottom line
        for x in range(start_x, start_x + rect_size, dash_length + gap_length):
            painter.drawLine(
                x,
                start_y + rect_size,
                min(x + dash_length, start_x + rect_size),
                start_y + rect_size,
            )

        # Left line
        for y in range(start_y, start_y + rect_size, dash_length + gap_length):
            painter.drawLine(
                start_x, y, start_x, min(y + dash_length, start_y + rect_size)
            )

        # Right line
        for y in range(start_y, start_y + rect_size, dash_length + gap_length):
            painter.drawLine(
                start_x + rect_size,
                y,
                start_x + rect_size,
                min(y + dash_length, start_y + rect_size),
            )

        painter.end()

        self.icon_label.setPixmap(pixmap)

    def set_message(self, message: str) -> None:
        """Update the message text."""
        self.message = message
        self.message_label.setText(message)

    def get_action_button(self) -> Optional[QPushButton]:
        """Get the action button if it exists."""
        return getattr(self, "action_btn", None)


class EmptyCardGrid(EmptyHint):
    """Empty state for the card grid."""

    def __init__(self, parent=None):
        super().__init__(
            "Brak szafek w projekcie\nDodaj szafki używając przycisku 'Dodaj z listy' lub 'Szafka niestandardowa'",
            "Dodaj z listy",
            parent,
        )


class EmptySearchResults(EmptyHint):
    """Empty state for search results."""

    def __init__(self, search_term: str = "", parent=None):
        if search_term:
            message = f"Brak wyników dla '{search_term}'\nSpróbuj zmienić kryteria wyszukiwania"
        else:
            message = "Brak wyników\nSpróbuj zmienić kryteria wyszukiwania"
        super().__init__(message, "", parent)


class EmptyProject(EmptyHint):
    """Empty state for a project with no content."""

    def __init__(self, parent=None):
        super().__init__(
            "Ten projekt jest pusty\nZacznij od dodania szafek z katalogu",
            "Otwórz katalog",
            parent,
        )


class EmptyAccessories(EmptyHint):
    """Empty state for accessories when no cabinet is selected."""

    def __init__(self, parent=None):
        super().__init__(
            "Wybierz szafkę, aby zobaczyć dostępne akcesoria\nAkcesoria są specyficzne dla każdego typu szafki",
            "",
            parent,
        )


class EmptyTableData(EmptyHint):
    """Empty state for table view when no data is available."""

    def __init__(self, parent=None):
        super().__init__(
            "Brak danych do wyświetlenia\nDodaj szafki, aby zobaczyć je w widoku tabeli",
            "Dodaj szafkę",
            parent,
        )
