"""
Banner Manager Widget

A notification system for displaying success, info, warning, and error messages
with automatic timeout and manual dismissal capabilities.
"""

from typing import List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPalette

# Import colors from the app's theme system
from src.gui.resources.styles import PRIMARY, PRIMARY_LIGHT


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
        is_dark = self.palette().color(QPalette.ColorRole.Window).lightness() < 128
        if is_dark:
            palette = {
                "success": ("#0f2a24", PRIMARY_LIGHT, "#d8fff7"),
                "error": ("#2b1212", "#f87171", "#ffe0e0"),
                "warning": ("#2c2210", "#fbbf24", "#fff4cf"),
                "info": ("#102739", "#60a5fa", "#dbeeff"),
            }
        else:
            palette = {
                "success": ("#e8f7f5", PRIMARY, "#133c38"),
                "error": ("#fdecec", "#f44336", "#611717"),
                "warning": ("#fff7e8", "#ff9800", "#5c3c00"),
                "info": ("#eaf4ff", "#2196F3", "#0a3552"),
            }
        bg_color, border_color, text_color = palette.get(banner_type, palette["info"])

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
