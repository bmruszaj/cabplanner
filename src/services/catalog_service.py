"""
Catalog service for managing cabinet types.

This service provides an interface for browsing, searching, and managing cabinet types
in the catalog. It uses the TemplateService to provide the catalog interface.
"""

from dataclasses import dataclass
from sqlalchemy.orm import Session

from src.db_schema.orm_models import CabinetTemplate
from src.services.template_service import TemplateService


@dataclass
class CatalogCabinetType:
    """Cabinet type adapted for catalog display."""

    id: int
    name: str
    sku: str | None
    width_mm: int | None
    height_mm: int | None
    depth_mm: int | None
    preview_path: str | None
    kitchen_type: str
    description: str = ""

    @classmethod
    def from_cabinet_type(cls, ct: CabinetTemplate) -> "CatalogCabinetType":
        """Convert CabinetType ORM model to catalog display model."""
        # Calculate dimensions from parts if available; fallback to legacy fields
        width_mm = None
        height_mm = None
        depth_mm = None

        # Calculate dimensions from parts if available
        if hasattr(ct, "parts") and ct.parts:
            # Use max width/height among parts as representative cabinet dimensions
            max_w = None
            max_h = None
            for p in ct.parts:
                if p.width_mm is not None:
                    max_w = (
                        int(p.width_mm)
                        if max_w is None
                        else max(max_w, int(p.width_mm))
                    )
                if p.height_mm is not None:
                    max_h = (
                        int(p.height_mm)
                        if max_h is None
                        else max(max_h, int(p.height_mm))
                    )
            width_mm = max_w
            height_mm = max_h
        else:
            # No parts available, use default dimensions
            width_mm = 600  # Default width
            height_mm = 720  # Default height

        # Default depth for kitchen cabinets
        depth_mm = 560 if ct.kitchen_type in ["LOFT", "PARIS", "WINO"] else 320

        # Generate SKU from kitchen type and name
        sku = f"{ct.kitchen_type}-{ct.id:03d}"

        return cls(
            id=ct.id,
            name=ct.name,
            sku=sku,
            width_mm=width_mm,
            height_mm=height_mm,
            depth_mm=depth_mm,
            preview_path=None,  # TODO: Add preview path support
            kitchen_type=ct.kitchen_type,
            description=f"{ct.name} - {ct.kitchen_type} series",
        )


class CatalogService:
    """Service for catalog operations."""

    def __init__(self, session: Session):
        """Initialize catalog service.

        Args:
            session: Database session for cabinet type operations
        """
        self.session = session
        self.cabinet_type_service = TemplateService(session)

    def list_types(
        self, query: str = "", filters: dict | None = None
    ) -> list[CatalogCabinetType]:
        """List cabinet types matching query and filters.

        Args:
            query: Search query to filter by name
            filters: Optional filters (kitchen_type, etc.)

        Returns:
            List of catalog cabinet types
        """
        # Get kitchen type filter if specified
        kitchen_type = None
        if filters and "kitchen_type" in filters:
            kitchen_type = filters["kitchen_type"]

        # Get all cabinet types from service
        cabinet_types = self.cabinet_type_service.list_templates(
            kitchen_type=kitchen_type
        )

        # Apply query filter
        if query:
            query_lower = query.lower()
            cabinet_types = [
                ct
                for ct in cabinet_types
                if query_lower in ct.name.lower()
                or query_lower in ct.kitchen_type.lower()
            ]

        # Convert to catalog display model
        return [CatalogCabinetType.from_cabinet_type(ct) for ct in cabinet_types]

    def get_type(self, type_id: int) -> CatalogCabinetType | None:
        """Get cabinet type by ID.

        Args:
            type_id: Cabinet type ID

        Returns:
            Catalog cabinet type or None if not found
        """
        cabinet_type = self.cabinet_type_service.get_template(type_id)
        if not cabinet_type:
            return None
        return CatalogCabinetType.from_cabinet_type(cabinet_type)

    def create_type(self, data: dict) -> CatalogCabinetType:
        """Create new cabinet type.

        Args:
            data: Cabinet type data

        Returns:
            Created catalog cabinet type
        """
        # Extract required fields
        kitchen_type = data.get("kitchen_type", "LOFT")
        name = data.get("name", "Nowy typ")

        try:
            # Create cabinet type through service
            cabinet_type = self.cabinet_type_service.create_template(
                kitchen_type=kitchen_type,
                name=name,
            )
            return CatalogCabinetType.from_cabinet_type(cabinet_type)
        except ValueError as e:
            # Re-raise ValueError (constraint violations) with user-friendly message
            raise e
        except Exception as e:
            # Handle other unexpected errors
            raise ValueError(f"Nie udało się utworzyć typu szafki: {str(e)}")

    def update_type(self, type_id: int, data: dict) -> CatalogCabinetType:
        """Update cabinet type.

        Args:
            type_id: Cabinet type ID
            data: Updated cabinet type data

        Returns:
            Updated catalog cabinet type
        """
        # Get the existing cabinet type to preserve existing values
        existing = self.cabinet_type_service.get_template(type_id)
        if not existing:
            raise ValueError(f"Typ szafki o ID {type_id} nie został znaleziony")

        # Only name and kitchen type are updatable at template level here.
        # Part-level changes should go through part APIs.
        update_fields = {}
        if "name" in data and data["name"] is not None:
            update_fields["name"] = data["name"]
        if "kitchen_type" in data and data["kitchen_type"] is not None:
            update_fields["kitchen_type"] = data["kitchen_type"]

        try:
            cabinet_type = self.cabinet_type_service.update_template(
                type_id, **update_fields
            )
            if not cabinet_type:
                raise ValueError(f"Typ szafki o ID {type_id} nie został znaleziony")
            return CatalogCabinetType.from_cabinet_type(cabinet_type)
        except ValueError as e:
            # Re-raise ValueError (constraint violations) with user-friendly message
            raise e
        except Exception as e:
            # Handle other unexpected errors
            raise ValueError(f"Nie udało się zaktualizować typu szafki: {str(e)}")

    def duplicate_type(self, type_id: int) -> CatalogCabinetType:
        """Duplicate cabinet type.

        Args:
            type_id: Cabinet type ID to duplicate

        Returns:
            Duplicated catalog cabinet type
        """
        # Get original cabinet type
        original = self.cabinet_type_service.get_template(type_id)
        if not original:
            raise ValueError(f"Cabinet type {type_id} not found")

        # Calculate dimensions from parts if available
        if hasattr(original, "parts") and original.parts:
            max_w = None
            max_h = None
            for part in original.parts:
                if part.width_mm is not None:
                    max_w = (
                        int(part.width_mm)
                        if max_w is None
                        else max(max_w, int(part.width_mm))
                    )
                if part.height_mm is not None:
                    max_h = (
                        int(part.height_mm)
                        if max_h is None
                        else max(max_h, int(part.height_mm))
                    )
        else:
            # No parts available, use default dimensions
            pass

        # Create duplicate with modified name
        duplicate_data = {
            "kitchen_type": original.kitchen_type,
            "name": f"{original.name} (Copy)",
        }

        return self.create_type(duplicate_data)

    def delete_type(self, type_id: int) -> bool:
        """Delete cabinet type.

        Args:
            type_id: Cabinet type ID to delete

        Returns:
            True if deleted successfully
        """
        return self.cabinet_type_service.delete_template(type_id)

    def get_kitchen_types(self) -> list[str]:
        """Get available kitchen types.

        Returns:
            List of kitchen type names
        """
        return ["LOFT", "PARIS", "WINO"]
