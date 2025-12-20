"""
Banner Manager Widget

A notification system for displaying success, info, warning, and error messages
with automatic timeout and manual dismissal capabilities.
"""

from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer

# Import colors from the app's theme system
from src.gui.resources.styles import PRIMARY


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
        # Define colors based on banner type using app theme
        if banner_type == "success":
            bg_color = "transparent"
            border_color = PRIMARY
            text_color = "#000000"
        elif banner_type == "error":
            bg_color = "transparent"
            border_color = "#f44336"
            text_color = "#000000"
        elif banner_type == "warning":
            bg_color = "transparent"
            border_color = "#ff9800"
            text_color = "#000000"
        else:  # info
            bg_color = "transparent"
            border_color = "#2196F3"
            text_color = "#000000"

        banner.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                color: {text_color};
                padding: 12px 16px;
                border-radius: 6px;
                margin: 8px 4px;
                font-size: 11pt;
                font-weight: 500;
                min-height: 40px;
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
            try:
                # Check if the C++ object still exists before manipulating
                if banner is not None:
                    banner.setParent(None)
                    banner.deleteLater()
            except RuntimeError:
                # Widget already deleted, ignore
                pass

    def clear_all(self):
        """Remove all active banners."""
        for banner in self.banners[:]:
            self._remove_banner(banner)
