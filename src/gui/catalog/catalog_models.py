"""
Data models for the catalog system.

Defines the data structures used for catalog browsing, filtering, and selection.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class SortOrder(Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


class SortField(Enum):
    """Available sort fields."""

    NAME = "name"
    CODE = "code"
    WIDTH = "width"
    HEIGHT = "height"
    DEPTH = "depth"


class ViewMode(Enum):
    """View mode for catalog display."""

    GRID = "grid"
    LIST = "list"


@dataclass
class Category:
    """Catalog category definition."""

    id: int
    name: str
    parent_id: Optional[int] = None
    children: List["Category"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class CatalogItem:
    """Catalog item (cabinet type) definition."""

    id: int
    name: str
    code: str
    category_id: int
    width: int
    height: int
    depth: int
    description: str = ""
    image_path: Optional[str] = None
    variants: List[str] = None
    body_colors: List[str] = None
    front_colors: List[str] = None
    handles: List[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.variants is None:
            self.variants = []
        if self.body_colors is None:
            self.body_colors = ["Biały", "Czarny", "Szary"]
        if self.front_colors is None:
            self.front_colors = ["Biały", "Czarny", "Szary", "Dąb", "Orzech"]
        if self.handles is None:
            self.handles = ["Standardowy", "Nowoczesny", "Klasyczny"]
        if self.tags is None:
            self.tags = []

    def preview_label(self) -> str:
        """Generate preview label for the item."""
        return f"{self.name}\n{self.code}\n{self.width}×{self.height}×{self.depth} mm"

    def matches_filter(self, filters: Dict[str, Any]) -> bool:
        """Check if item matches the given filters."""
        # Category filter (single id or expanded list of ids)
        category_ids = filters.get("category_ids")
        if category_ids:
            try:
                valid_ids = {int(cid) for cid in category_ids}
            except (TypeError, ValueError):
                valid_ids = set()
            if valid_ids and self.category_id not in valid_ids:
                return False
        elif filters.get("category_id"):
            try:
                if self.category_id != int(filters["category_id"]):
                    return False
            except (TypeError, ValueError):
                return False

        # Width filter
        if filters.get("width") and filters["width"] != "Szer.: dowolna":
            try:
                filter_width = int(filters["width"])
                if self.width != filter_width:
                    return False
            except ValueError:
                pass

        # Type filter (based on name or tags)
        if filters.get("kind") and filters["kind"] != "Typ: dowolny":
            filter_type = filters["kind"].lower()
            name_lower = self.name.lower()
            if filter_type not in name_lower and filter_type not in [
                tag.lower() for tag in self.tags
            ]:
                return False

        # Height filter
        if filters.get("height") and filters["height"] != "Wys.: dowolna":
            try:
                filter_height = int(filters["height"])
                if self.height != filter_height:
                    return False
            except ValueError:
                pass

        return True


@dataclass
class FilterState:
    """Current filter state."""

    search_query: str = ""
    category_id: Optional[int] = None
    width: Optional[str] = None
    height: Optional[str] = None
    depth: Optional[str] = None
    cabinet_type: Optional[str] = None
    sort_field: SortField = SortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    view_mode: ViewMode = ViewMode.GRID

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter state to dictionary."""
        return {
            "search_query": self.search_query,
            "category_id": self.category_id,
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "cabinet_type": self.cabinet_type,
            "sort_field": self.sort_field.value,
            "sort_order": self.sort_order.value,
            "view_mode": self.view_mode.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterState":
        """Create filter state from dictionary."""
        return cls(
            search_query=data.get("search_query", ""),
            category_id=data.get("category_id"),
            width=data.get("width"),
            height=data.get("height"),
            depth=data.get("depth"),
            cabinet_type=data.get("cabinet_type"),
            sort_field=SortField(data.get("sort_field", "name")),
            sort_order=SortOrder(data.get("sort_order", "asc")),
            view_mode=ViewMode(data.get("view_mode", "grid")),
        )


@dataclass
class SearchResult:
    """Search result with pagination info."""

    items: List[CatalogItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool

    @classmethod
    def empty(cls) -> "SearchResult":
        """Create empty search result."""
        return cls(items=[], total_count=0, page=1, page_size=20, has_more=False)
