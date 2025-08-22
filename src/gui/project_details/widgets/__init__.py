"""
Widgets package for project details UI components.

This package contains all the specialized widgets used in the project details interface.
Each widget is focused on a specific UI concern and can be reused across different contexts.
"""

from .header_bar import HeaderBar
from .toolbar import Toolbar
from .cabinet_card import CabinetCard, QuantityStepper, ColorChip
from .card_grid import CardGrid
from .client_sidebar import ClientSidebar
from .banners import BannerManager, Banner
from .empty_states import (
    EmptyHint,
    EmptyCardGrid,
    EmptySearchResults,
    EmptyProject,
    EmptyAccessories,
    EmptyTableData,
)

__all__ = [
    "HeaderBar",
    "Toolbar",
    "CabinetCard",
    "QuantityStepper",
    "ColorChip",
    "CardGrid",
    "ClientSidebar",
    "BannerManager",
    "Banner",
    "EmptyHint",
    "EmptyCardGrid",
    "EmptySearchResults",
    "EmptyProject",
    "EmptyAccessories",
    "EmptyTableData",
]
