"""
Banner widgets for displaying status messages and notifications.

These widgets provide consistent UI feedback for user actions and system states.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsOpacityEffect,
)

from ..constants import (
    COLORS,
)

logger = logging.getLogger(__name__)


class Banner(QWidget):
    """
    Individual banner widget for status messages.

    Features:
    - Auto-hide after timeout
    - Fade in/out animations
    - Different styling for message types
    """

    # Signal for when banner is closed
    closed = Signal()

    def __init__(
        self,
        message: str,
        banner_type: str = "info",
        timeout_ms: int = 2500,
        parent=None,
    ):
        """
        Initialize the banner.

        Args:
            message: The message to display
            banner_type: Type of banner ("info", "success", "warning", "error")
            timeout_ms: Auto-hide timeout in milliseconds
            parent: Parent widget
        """
        super().__init__(parent)
        self.message = message
        self.banner_type = banner_type
        self.timeout_ms = timeout_ms

        self._setup_ui()
        self._setup_animations()

        # Auto-hide timer
        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, self.hide_with_animation)

    def _setup_ui(self) -> None:
        """Set up the banner UI."""
        self.setFixedHeight(40)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Message label
        self.message_label = QLabel(self.message)
        message_font = QFont()
        message_font.setPointSize(12)
        self.message_label.setFont(message_font)
        layout.addWidget(self.message_label)

        layout.addStretch()

        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: rgba(255, 255, 255, 0.7);
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.hide_with_animation)
        layout.addWidget(self.close_btn)

        # Apply styling based on banner type
        self._apply_styling()

    def _apply_styling(self) -> None:
        """Apply styling based on banner type."""
        style_map = {
            "info": {"background": COLORS.get("info", "#3498db"), "text": "white"},
            "success": {
                "background": COLORS.get("success", "#27ae60"),
                "text": "white",
            },
            "warning": {
                "background": COLORS.get("warning", "#f39c12"),
                "text": "white",
            },
            "error": {"background": COLORS.get("error", "#e74c3c"), "text": "white"},
        }

        style = style_map.get(self.banner_type, style_map["info"])

        self.setStyleSheet(f"""
            Banner {{
                background-color: {style["background"]};
                border-radius: 4px;
                border: none;
            }}
        """)

        self.message_label.setStyleSheet(f"color: {style['text']};")

    def _setup_animations(self) -> None:
        """Set up fade animations."""
        # Opacity effect for animations
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out_animation.finished.connect(self._on_fade_out_finished)

    def show_with_animation(self) -> None:
        """Show the banner with fade in animation."""
        self.show()
        self.fade_in_animation.start()

    def hide_with_animation(self) -> None:
        """Hide the banner with fade out animation."""
        self.fade_out_animation.start()

    def _on_fade_out_finished(self) -> None:
        """Handle fade out animation completion."""
        self.hide()
        self.closed.emit()


class BannerManager(QWidget):
    """
    Manager widget for displaying and managing multiple banners.

    Features:
    - Stack multiple banners vertically
    - Auto-removal when banners close
    - Simple API for showing different banner types
    - Stacked-banner safe (renew timer for same banner type and message)
    """

    def __init__(self, parent=None):
        """Initialize the banner manager."""
        super().__init__(parent)
        self.banners = []
        self.banner_cache = {}  # Track active banners by message+type

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the banner manager UI."""
        # Main layout - vertical stack of banners
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        # Initially hidden
        self.hide()

    def show_banner(
        self, message: str, banner_type: str = "info", timeout_ms: int = 2500
    ) -> None:
        """
        Show a banner with the specified message.

        Args:
            message: The message to display
            banner_type: Type of banner ("info", "success", "warning", "error")
            timeout_ms: Auto-hide timeout in milliseconds (0 = no auto-hide)
        """
        banner_key = f"{banner_type}:{message}"

        # Check if we already have this exact banner
        existing_banner = self.banner_cache.get(banner_key)
        if existing_banner and existing_banner in self.banners:
            # Renew the timer for the existing banner
            if timeout_ms > 0:
                QTimer.singleShot(timeout_ms, existing_banner.hide_with_animation)
            logger.debug(f"Renewed timer for existing {banner_type} banner: {message}")
            return

        # Create new banner
        banner = Banner(message, banner_type, timeout_ms)
        banner.closed.connect(lambda: self._remove_banner(banner))

        # Add to layout, list, and cache
        self.layout.addWidget(banner)
        self.banners.append(banner)
        self.banner_cache[banner_key] = banner

        # Show the banner with animation
        banner.show_with_animation()

        # Show the manager widget if it was hidden
        if not self.isVisible():
            self.show()

        logger.debug(f"Showed {banner_type} banner: {message}")

    def show_info(self, message: str, timeout_ms: int = 2500) -> None:
        """Show an info banner."""
        self.show_banner(message, "info", timeout_ms)

    def show_success(self, message: str, timeout_ms: int = 2500) -> None:
        """Show a success banner."""
        self.show_banner(message, "success", timeout_ms)

    def show_warning(self, message: str, timeout_ms: int = 3500) -> None:
        """Show a warning banner."""
        self.show_banner(message, "warning", timeout_ms)

    def show_error(self, message: str, timeout_ms: int = 0) -> None:
        """Show an error banner (no auto-hide by default)."""
        self.show_banner(message, "error", timeout_ms)

    def clear_all(self) -> None:
        """Clear all banners."""
        for banner in self.banners.copy():
            banner.hide_with_animation()

    def clear_by_type(self, banner_type: str) -> None:
        """Clear all banners of a specific type."""
        for banner in self.banners.copy():
            if banner.banner_type == banner_type:
                banner.hide_with_animation()

    def _remove_banner(self, banner: Banner) -> None:
        """Remove a banner from the manager."""
        if banner in self.banners:
            self.banners.remove(banner)
            self.layout.removeWidget(banner)
            banner.setParent(None)

            # Remove from cache
            banner_key = f"{banner.banner_type}:{banner.message}"
            if banner_key in self.banner_cache:
                del self.banner_cache[banner_key]

        # Hide the manager if no banners left
        if not self.banners:
            self.hide()

    def has_banners(self) -> bool:
        """Check if there are any active banners."""
        return len(self.banners) > 0

    def get_banner_count(self) -> int:
        """Get the number of active banners."""
        return len(self.banners)

    def has_error_banners(self) -> bool:
        """Check if there are any error banners."""
        return any(banner.banner_type == "error" for banner in self.banners)
