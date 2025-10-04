"""
Catalog module for cabinet selection and browsing.

This module provides a modern catalog dialog for browsing and selecting
cabinets from the available catalog, with filtering, searching, and
detailed configuration options.
"""

from .catalog_dialog import CatalogDialog
from .catalog_card import CatalogCard
from .catalog_models import CatalogItem, Category, FilterState
from .catalog_service import CatalogService

__all__ = [
    "CatalogDialog",
    "CatalogCard",
    "CatalogItem",
    "Category",
    "FilterState",
    "CatalogService",
]
