"""
Banner Manager Widget

A notification system for displaying success, info, warning, and error messages
with automatic timeout and manual dismissal capabilities.
"""

from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer


class BannerManager(QWidget):
    """Banner manager for showing notifications."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.banners: List[QLabel] = []

    def show_success(self, message: str, timeout_ms: int = 2500):
        """Show a success banner with green styling."""
        self._show_banner(message, "success", timeout_ms)

    def show_info(self, message: str, timeout_ms: int = 2500):
        """Show an info banner with blue styling."""
        self._show_banner(message, "info", timeout_ms)

    def show_warning(self, message: str, timeout_ms: int = 3500):
        """Show a warning banner with yellow styling."""
        self._show_banner(message, "warning", timeout_ms)

    def show_error(self, message: str, timeout_ms: int = 0):
        """Show an error banner with red styling. Persists by default."""
        self._show_banner(message, "error", timeout_ms)

    def _show_banner(self, message: str, banner_type: str, timeout_ms: int):
        """Create and display a banner with the specified type and timeout."""
        banner = QLabel(message)
        banner.setWordWrap(True)
        banner.setStyleSheet(f"""
            QLabel {{
                background-color: {"#d4edda" if banner_type == "success" else "#f8d7da" if banner_type == "error" else "#fff3cd"};
                border: 1px solid {"#c3e6cb" if banner_type == "success" else "#f5c6cb" if banner_type == "error" else "#ffeaa7"};
                color: {"#155724" if banner_type == "success" else "#721c24" if banner_type == "error" else "#856404"};
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px 0px;
            }}
        """)

        self.layout.addWidget(banner)
        self.banners.append(banner)

        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, lambda: self._remove_banner(banner))

    def _remove_banner(self, banner: QLabel):
        """Remove a specific banner from the display."""
        if banner in self.banners:
            self.banners.remove(banner)
            banner.setParent(None)

    def clear_all(self):
        """Remove all active banners."""
        for banner in self.banners[:]:
            self._remove_banner(banner)
