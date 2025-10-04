"""
Catalog Service - interface to cabinet catalog data.

Provides methods for browsing, searching, and filtering the cabinet catalog.
Currently uses mock data but can be extended to use database or external API.
"""

from typing import List, Dict, Any, Tuple, Optional
import logging
from sqlalchemy.orm import Session

from .catalog_models import (
    CatalogItem,
    Category,
)

logger = logging.getLogger(__name__)


class CatalogService:
    """Service for catalog operations."""

    def __init__(self, session: Session = None):
        """Initialize catalog service.

        Args:
            session: Database session (for future database integration)
        """
        self.session = session
        self._catalog_cache = None
        self._categories_cache = None

    def get_categories(self) -> List[Category]:
        """Get all available categories."""
        if self._categories_cache is None:
            self._categories_cache = self._load_mock_categories()
        return self._categories_cache

    def search_items(
        self,
        query: str = "",
        filters: Dict[str, Any] = None,
        sort: Tuple[str, str] = ("name", "asc"),
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[CatalogItem], bool]:
        """
        Search catalog items with filters and pagination.

        Args:
            query: Search query string
            filters: Filter dictionary
            sort: Tuple of (field, order)
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Tuple of (items, has_more)
        """
        try:
            all_items = self._get_all_items()

            # Apply search query
            if query:
                query_lower = query.lower()
                all_items = [
                    item
                    for item in all_items
                    if (
                        query_lower in item.name.lower()
                        or query_lower in item.code.lower()
                        or query_lower in item.description.lower()
                    )
                ]

            # Apply filters
            if filters:
                all_items = [item for item in all_items if item.matches_filter(filters)]

            # Apply sorting
            sort_field, sort_order = sort
            reverse = sort_order == "desc"

            if sort_field == "name":
                all_items.sort(key=lambda x: x.name.lower(), reverse=reverse)
            elif sort_field == "code":
                all_items.sort(key=lambda x: x.code, reverse=reverse)
            elif sort_field == "width":
                all_items.sort(key=lambda x: x.width, reverse=reverse)
            elif sort_field == "height":
                all_items.sort(key=lambda x: x.height, reverse=reverse)
            elif sort_field == "depth":
                all_items.sort(key=lambda x: x.depth, reverse=reverse)

            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_items = all_items[start_idx:end_idx]
            has_more = end_idx < len(all_items)

            return page_items, has_more

        except Exception:
            logger.exception("Error searching catalog items")
            return [], False

    def get_item(self, item_id: int) -> Optional[CatalogItem]:
        """Get catalog item by ID."""
        try:
            all_items = self._get_all_items()
            for item in all_items:
                if item.id == item_id:
                    return item
            return None
        except Exception:
            logger.exception(f"Error getting catalog item {item_id}")
            return None

    def _get_all_items(self) -> List[CatalogItem]:
        """Get all catalog items (cached)."""
        if self._catalog_cache is None:
            self._catalog_cache = self._load_mock_catalog()
        return self._catalog_cache

    def _load_mock_categories(self) -> List[Category]:
        """Load mock categories for development."""
        return [
            Category(id=1, name="Szafki bazowe", parent_id=None),
            Category(id=2, name="Szafki wiszące", parent_id=None),
            Category(id=3, name="Słupki", parent_id=None),
            Category(id=4, name="Szafki narożne", parent_id=None),
            Category(id=5, name="Akcesoria", parent_id=None),
            # Subcategories
            Category(id=11, name="Bazowe standardowe", parent_id=1),
            Category(id=12, name="Bazowe z szufladami", parent_id=1),
            Category(id=13, name="Bazowe pod zlewozmywak", parent_id=1),
            Category(id=21, name="Wiszące standardowe", parent_id=2),
            Category(id=22, name="Wiszące ze szkłem", parent_id=2),
            Category(id=23, name="Wiszące okapy", parent_id=2),
        ]

    def _load_mock_catalog(self) -> List[CatalogItem]:
        """Load mock catalog data for development."""
        # Mock cabinet data - in real implementation this would come from database
        mock_items = [
            # Bazowe
            CatalogItem(
                id=1,
                name="Szafka bazowa 30cm",
                code="SB30",
                category_id=11,
                width=300,
                height=720,
                depth=560,
                description="Standardowa szafka bazowa z półką regulowaną",
                tags=["bazowa", "standardowa"],
            ),
            CatalogItem(
                id=2,
                name="Szafka bazowa 40cm",
                code="SB40",
                category_id=11,
                width=400,
                height=720,
                depth=560,
                description="Standardowa szafka bazowa z półką regulowaną",
                tags=["bazowa", "standardowa"],
            ),
            CatalogItem(
                id=3,
                name="Szafka bazowa 45cm",
                code="SB45",
                category_id=11,
                width=450,
                height=720,
                depth=560,
                description="Standardowa szafka bazowa z półką regulowaną",
                tags=["bazowa", "standardowa"],
            ),
            CatalogItem(
                id=4,
                name="Szafka bazowa 50cm",
                code="SB50",
                category_id=11,
                width=500,
                height=720,
                depth=560,
                description="Standardowa szafka bazowa z półką regulowaną",
                tags=["bazowa", "standardowa"],
            ),
            CatalogItem(
                id=5,
                name="Szafka bazowa 60cm",
                code="SB60",
                category_id=11,
                width=600,
                height=720,
                depth=560,
                description="Standardowa szafka bazowa z półką regulowaną",
                tags=["bazowa", "standardowa"],
            ),
            CatalogItem(
                id=6,
                name="Szafka bazowa 80cm",
                code="SB80",
                category_id=11,
                width=800,
                height=720,
                depth=560,
                description="Standardowa szafka bazowa z półką regulowaną",
                tags=["bazowa", "standardowa"],
            ),
            CatalogItem(
                id=7,
                name="Szafka bazowa 90cm",
                code="SB90",
                category_id=11,
                width=900,
                height=720,
                depth=560,
                description="Standardowa szafka bazowa z półką regulowaną",
                tags=["bazowa", "standardowa"],
            ),
            # Szuflady
            CatalogItem(
                id=11,
                name="Szafka z szufladami 40cm",
                code="SS40",
                category_id=12,
                width=400,
                height=720,
                depth=560,
                description="Szafka bazowa z trzema szufladami",
                tags=["bazowa", "szuflady"],
            ),
            CatalogItem(
                id=12,
                name="Szafka z szufladami 50cm",
                code="SS50",
                category_id=12,
                width=500,
                height=720,
                depth=560,
                description="Szafka bazowa z trzema szufladami",
                tags=["bazowa", "szuflady"],
            ),
            CatalogItem(
                id=13,
                name="Szafka z szufladami 60cm",
                code="SS60",
                category_id=12,
                width=600,
                height=720,
                depth=560,
                description="Szafka bazowa z trzema szufladami",
                tags=["bazowa", "szuflady"],
            ),
            # Wiszące
            CatalogItem(
                id=21,
                name="Szafka wisząca 30cm",
                code="SW30",
                category_id=21,
                width=300,
                height=720,
                depth=320,
                description="Standardowa szafka wisząca z półką",
                tags=["wisząca", "standardowa"],
            ),
            CatalogItem(
                id=22,
                name="Szafka wisząca 40cm",
                code="SW40",
                category_id=21,
                width=400,
                height=720,
                depth=320,
                description="Standardowa szafka wisząca z półką",
                tags=["wisząca", "standardowa"],
            ),
            CatalogItem(
                id=23,
                name="Szafka wisząca 50cm",
                code="SW50",
                category_id=21,
                width=500,
                height=720,
                depth=320,
                description="Standardowa szafka wisząca z półką",
                tags=["wisząca", "standardowa"],
            ),
            CatalogItem(
                id=24,
                name="Szafka wisząca 60cm",
                code="SW60",
                category_id=21,
                width=600,
                height=720,
                depth=320,
                description="Standardowa szafka wisząca z półką",
                tags=["wisząca", "standardowa"],
            ),
            CatalogItem(
                id=25,
                name="Szafka wisząca 80cm",
                code="SW80",
                category_id=21,
                width=800,
                height=720,
                depth=320,
                description="Standardowa szafka wisząca z półką",
                tags=["wisząca", "standardowa"],
            ),
            # Słupki
            CatalogItem(
                id=31,
                name="Słupek 50cm",
                code="SL50",
                category_id=3,
                width=500,
                height=2000,
                depth=560,
                description="Słupek wysoki z półkami",
                tags=["słupek", "wysoki"],
            ),
            CatalogItem(
                id=32,
                name="Słupek 60cm",
                code="SL60",
                category_id=3,
                width=600,
                height=2000,
                depth=560,
                description="Słupek wysoki z półkami",
                tags=["słupek", "wysoki"],
            ),
            # Pod zlewozmywak
            CatalogItem(
                id=41,
                name="Szafka pod zlewozmywak 60cm",
                code="SZ60",
                category_id=13,
                width=600,
                height=720,
                depth=560,
                description="Szafka pod zlewozmywak jednokomorowa",
                tags=["bazowa", "zlewozmywak"],
            ),
            CatalogItem(
                id=42,
                name="Szafka pod zlewozmywak 80cm",
                code="SZ80",
                category_id=13,
                width=800,
                height=720,
                depth=560,
                description="Szafka pod zlewozmywak dwukomorowa",
                tags=["bazowa", "zlewozmywak"],
            ),
        ]

        return mock_items
