"""Small UI utilities and helpers."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap


def dot(color: QColor, diameter: int = 10) -> QPixmap:
    """Small colored dot pixmap used as a status chip."""
    pm = QPixmap(diameter, diameter)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, diameter, diameter)
    painter.end()
    return pm
