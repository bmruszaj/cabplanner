"""
Compatibility Banner widget for tests and legacy callers.

Provides a simple `Banner` QWidget that displays a message styled by type
(info/success/warning/error). Tests import `Banner` from this module.
"""

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt


class Banner(QWidget):
    """Simple banner widget used by tests and demo code."""

    def __init__(self, text: str, banner_type: str = "info", parent=None):
        super().__init__(parent)
        self._label = QLabel(text)
        self._label.setWordWrap(True)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(self._label)

        # Simple styling map
        bg = (
            "#e6f7ff"
            if banner_type == "info"
            else "#dff0d8"
            if banner_type == "success"
            else "#fff3cd"
            if banner_type == "warning"
            else "#f8d7da"
        )
        border = (
            "#b6e0ff"
            if banner_type == "info"
            else "#c3e6cb"
            if banner_type == "success"
            else "#ffeaa7"
            if banner_type == "warning"
            else "#f5c6cb"
        )
        color = (
            "#0a766c"
            if banner_type == "info"
            else "#155724"
            if banner_type == "success"
            else "#856404"
            if banner_type == "warning"
            else "#721c24"
        )

        self._label.setStyleSheet(
            f"background-color: {bg}; border: 1px solid {border}; color: {color}; padding: 6px 10px; border-radius: 6px;"
        )

    def setText(self, text: str):
        self._label.setText(text)

    def text(self) -> str:
        return self._label.text()
