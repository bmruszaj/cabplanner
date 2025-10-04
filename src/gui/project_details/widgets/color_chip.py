"""
Color chip widget for displaying cabinet colors.
"""

from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from PySide6.QtWidgets import QWidget

from ..constants import COLOR_CHIP_SIZE
from ...constants.colors import get_color_hex


class ColorChip(QWidget):
    """Small color chip widget for displaying cabinet colors."""

    def __init__(self, color: str, label: str = "", parent=None):
        super().__init__(parent)
        self.color = color
        self.label = label
        self.setFixedSize(COLOR_CHIP_SIZE, COLOR_CHIP_SIZE)
        self.setToolTip(f"{label}: {color}" if label else color)

    def set_color(self, color: str):
        """Update the color and refresh the display."""
        self.color = color
        self.setToolTip(f"{self.label}: {color}" if self.label else color)
        self.update()  # Trigger repaint

    def _get_qt_color(self, color: str) -> QColor:
        """Convert color name to QColor, handling Polish color names."""
        hex_color = get_color_hex(color)
        qt_color = QColor(hex_color)

        if not qt_color.isValid():
            print(
                f"Warning: Invalid color '{color}' -> '{hex_color}', using white as fallback"
            )
            return QColor("#FFFFFF")

        return qt_color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self._get_qt_color(self.color)))
        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.drawRoundedRect(0, 0, COLOR_CHIP_SIZE, COLOR_CHIP_SIZE, 4, 4)
