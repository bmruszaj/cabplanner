"""
Cabinet catalog components - now modularized.
This file provides backward compatibility by re-exporting the refactored components.
For new code, import directly from the appropriate modules.
"""

# Re-export all the refactored components for backward compatibility
from src.gui.cabinet_type_model import CabinetTypeModel, Col
from src.gui.cabinet_type_proxy import CabinetTypeProxyModel
from src.gui.dialogs.cabinet_type_dialog import CabinetTypeDialog
from src.gui.utils.ui_bits import dot
from src.gui.widgets.cabinet_type_card import CabinetTypeCard
from src.gui.windows.cabinet_catalog_window import CabinetCatalogWindow

# For new applications, use the factory function
from src.app.cabinet_catalog_app import create_cabinet_catalog_window

__all__ = [
    "CabinetTypeModel",
    "Col",
    "CabinetTypeProxyModel",
    "CabinetTypeDialog",
    "CabinetTypeCard",
    "CabinetCatalogWindow",
    "dot",
    "create_cabinet_catalog_window",
]
