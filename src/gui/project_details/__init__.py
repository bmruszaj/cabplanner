"""
Project Details Package

Modular components for project cabinet management dialog.
Extracted from monolithic project_details.py for better maintainability.
"""

from .constants import (
    ICON_SIZE,
    CARD_WIDTH,
    CARD_MIN_WIDTH,
    CARD_MAX_WIDTH,
    CARD_HEIGHT,
    CARD_MARGIN,
    CARD_SPACING,
    CARD_PADDING,
    HEADER_HEIGHT,
    TOOLBAR_HEIGHT,
    SEARCH_WIDTH,
    BUTTON_MIN_WIDTH,
    CARD_MIN_H,
    VIEW_MODE_CARDS,
    VIEW_MODE_TABLE,
    SORT_BY_SEQ,
    SORT_BY_NAME,
    SORT_BY_SIZE,
    SORT_BY_QTY,
    SORT_ASCENDING,
    SORT_DESCENDING,
    SELECTION_PRIMARY,
    SELECTION_SECONDARY,
    HOVER_ALPHA,
    FOCUS_WIDTH,
    MIN_SEARCH_CHARS,
    UPDATE_DELAY_MS,
    TOOLTIP_DELAY_MS,
    ANIMATION_DURATION_MS,
    DOUBLE_CLICK_INTERVAL_MS,
    MAX_RECENT_ITEMS,
    DEFAULT_PAGE_SIZE,
)
from .utils import open_or_print
from .layouts import ResponsiveFlowLayout
from .widgets import (
    ColorChip,
    QuantityStepper,
    SequenceNumberInput,
    CabinetCard,
    HeaderBar,
    Toolbar,
    BannerManager,
)
from .models import CabinetTableModel, CabinetProxyModel
from .view import ProjectDetailsView, UiState, EmptyStateWidget

__all__ = [
    # Constants
    "ICON_SIZE",
    "CARD_WIDTH",
    "CARD_MIN_WIDTH",
    "CARD_MAX_WIDTH",
    "CARD_HEIGHT",
    "CARD_MARGIN",
    "CARD_SPACING",
    "CARD_PADDING",
    "HEADER_HEIGHT",
    "TOOLBAR_HEIGHT",
    "CARD_MIN_H",
    "SEARCH_WIDTH",
    "BUTTON_MIN_WIDTH",
    "VIEW_MODE_CARDS",
    "VIEW_MODE_TABLE",
    "SORT_BY_SEQ",
    "SORT_BY_NAME",
    "SORT_BY_SIZE",
    "SORT_BY_QTY",
    "SORT_ASCENDING",
    "SORT_DESCENDING",
    "SELECTION_PRIMARY",
    "SELECTION_SECONDARY",
    "HOVER_ALPHA",
    "FOCUS_WIDTH",
    "MIN_SEARCH_CHARS",
    "UPDATE_DELAY_MS",
    "TOOLTIP_DELAY_MS",
    "ANIMATION_DURATION_MS",
    "DOUBLE_CLICK_INTERVAL_MS",
    "MAX_RECENT_ITEMS",
    "DEFAULT_PAGE_SIZE",
    # Utils
    "open_or_print",
    # Layouts
    "ResponsiveFlowLayout",
    # Widgets
    "ColorChip",
    "QuantityStepper",
    "SequenceNumberInput",
    "CabinetCard",
    "HeaderBar",
    "Toolbar",
    "BannerManager",
    "Banner",
    # Models
    "CabinetTableModel",
    "CabinetProxyModel",
    # Views and State
    "ProjectDetailsView",
    "UiState",
    "EmptyStateWidget",
]
