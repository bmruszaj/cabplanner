"""
GUI constants package.
"""

from .colors import CABINET_COLORS, COLOR_MAP, POPULAR_COLORS, get_color_hex

# Re-export constants from the parent constants.py file to maintain compatibility
from PySide6.QtCore import QSize

# UX: Reduced card height and consistent spacing for better density
CARD_HEIGHT = 200
CARD_WIDTH = 350
ICON_SIZE = QSize(24, 24)
CONTENT_MARGINS = (12, 12, 12, 12)
LAYOUT_SPACING = 8

__all__ = [
    "CABINET_COLORS",
    "COLOR_MAP",
    "POPULAR_COLORS",
    "get_color_hex",
    "CARD_HEIGHT",
    "CARD_WIDTH",
    "ICON_SIZE",
    "CONTENT_MARGINS",
    "LAYOUT_SPACING",
]
