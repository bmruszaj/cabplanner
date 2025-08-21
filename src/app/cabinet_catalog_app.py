"""Factory helpers for creating cabinet catalog components."""

from sqlalchemy.orm import Session

from src.gui.windows.cabinet_catalog_window import CabinetCatalogWindow


def create_cabinet_catalog_window(session: Session) -> CabinetCatalogWindow:
    """Create and configure a cabinet catalog window.
    
    Args:
        session: Database session for the cabinet type service
        
    Returns:
        Configured CabinetCatalogWindow instance
    """
    return CabinetCatalogWindow(session)
