"""
Color chip widget for displaying cabinet colors.
"""

from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from PySide6.QtWidgets import QWidget

from ..constants import COLOR_CHIP_SIZE


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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(self.color)))
        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.drawRoundedRect(0, 0, COLOR_CHIP_SIZE, COLOR_CHIP_SIZE, 4, 4)
