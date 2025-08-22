"""
Models package for project details data handling.

This package contains data models and state management for the project details interface.
"""

from .cabinet_table import (
    CabinetTableModel,
    CabinetProxyModel,
    make_proxy,
    ColorChipDelegate,
    setup_color_chip_delegate,
)
from .state import ProjectDetailsState, UiState
from .actions import ProjectDetailsActions
from .printing import PrintHelper, open_or_print

__all__ = [
    "CabinetTableModel",
    "CabinetProxyModel",
    "make_proxy",
    "ColorChipDelegate",
    "setup_color_chip_delegate",
    "ProjectDetailsState",
    "UiState",
    "ProjectDetailsActions",
    "PrintHelper",
    "open_or_print",
]
