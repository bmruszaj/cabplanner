import pytest

from src.services.catalog_service import CatalogCabinetType


@pytest.fixture
def sample_catalog_templates(template_service):
    """Create sample cabinet templates for testing."""
    templates = [
        template_service.create_template(kitchen_type="LOFT", name="CatalogD60"),
        template_service.create_template(kitchen_type="LOFT", name="CatalogG40"),
        template_service.create_template(kitchen_type="PARIS", name="CatalogD80"),
        template_service.create_template(kitchen_type="WINO", name="CatalogN60"),
    ]

    # Add some parts to templates
    template_service.add_part(
        cabinet_type_id=templates[0].id,
        part_name="bok",
        height_mm=720,
        width_mm=560,
        pieces=2,
    )
    template_service.add_part(
        cabinet_type_id=templates[0].id,
        part_name="półka",
        height_mm=560,
        width_mm=540,
        pieces=1,
    )

    return templates


class TestCatalogService:
    def test_list_types_no_filter(self, catalog_service, sample_catalog_templates):
        """Test listing all cabinet types without filters."""
        types = catalog_service.list_types()

        assert len(types) >= 4
        names = [t.name for t in types]
        assert "CatalogD60" in names
        assert "CatalogG40" in names
        assert "CatalogD80" in names
        assert "CatalogN60" in names

    def test_list_types_with_query(self, catalog_service, sample_catalog_templates):
        """Test listing cabinet types with search query."""
        # Search for "D" types (base cabinets)
        types = catalog_service.list_types(query="CatalogD")
        assert len(types) >= 2
        names = [t.name for t in types]
        assert "CatalogD60" in names
        assert "CatalogD80" in names

        # Search for specific name
        types = catalog_service.list_types(query="CatalogG40")
        filtered_types = [t for t in types if "CatalogG40" in t.name]
        assert len(filtered_types) >= 1

    def test_list_types_with_kitchen_type_filter(
        self, catalog_service, sample_catalog_templates
    ):
        """Test listing cabinet types filtered by kitchen type."""
        filters = {"kitchen_type": "LOFT"}
        types = catalog_service.list_types(filters=filters)

        loft_types = [t for t in types if t.kitchen_type == "LOFT"]
        assert len(loft_types) >= 2

    def test_list_types_combined_filters(
        self, catalog_service, sample_catalog_templates
    ):
        """Test listing with combined query and filters."""
        filters = {"kitchen_type": "LOFT"}
        types = catalog_service.list_types(query="CatalogD", filters=filters)

        matching_types = [
            t for t in types if "CatalogD" in t.name and t.kitchen_type == "LOFT"
        ]
        assert len(matching_types) >= 1

    def test_get_type_existing(self, catalog_service, sample_catalog_templates):
        """Test getting an existing cabinet type."""
        template_id = sample_catalog_templates[0].id
        catalog_type = catalog_service.get_type(template_id)

        assert catalog_type is not None
        assert catalog_type.id == template_id
        assert catalog_type.name == "CatalogD60"
        assert catalog_type.kitchen_type == "LOFT"

    def test_get_type_nonexistent(self, catalog_service):
        """Test getting a non-existent cabinet type."""
        catalog_type = catalog_service.get_type(99999)
        assert catalog_type is None

    def test_create_type_basic(self, catalog_service):
        """Test creating a new cabinet type."""
        data = {"name": "TestCabinet", "kitchen_type": "LOFT"}

        catalog_type = catalog_service.create_type(data)

        assert catalog_type.name == "TestCabinet"
        assert catalog_type.kitchen_type == "LOFT"

    def test_create_type_with_parts(self, catalog_service):
        """Test creating cabinet type with parts."""
        data = {
            "name": "CabinetWithParts",
            "kitchen_type": "PARIS",
            "parts": [
                {
                    "part_name": "bok",
                    "height_mm": 720,
                    "width_mm": 560,
                    "pieces": 2,
                    "material": "PLYTA",
                },
                {
                    "part_name": "półka",
                    "height_mm": 560,
                    "width_mm": 540,
                    "pieces": 1,
                    "material": "PLYTA",
                },
            ],
        }

        catalog_type = catalog_service.create_type(data)

        assert catalog_type.name == "CabinetWithParts"
        assert catalog_type.kitchen_type == "PARIS"

    def test_update_type_basic_fields(self, catalog_service, sample_catalog_templates):
        """Test updating basic cabinet type fields."""
        template_id = sample_catalog_templates[0].id

        data = {"name": "UpdatedCatalogD60", "kitchen_type": "PARIS"}

        updated_type = catalog_service.update_type(template_id, data)

        assert updated_type.name == "UpdatedCatalogD60"
        assert updated_type.kitchen_type == "PARIS"

    def test_update_type_nonexistent(self, catalog_service):
        """Test updating a non-existent cabinet type."""
        data = {"name": "NewName"}

        with pytest.raises(ValueError, match="nie został znaleziony"):
            catalog_service.update_type(99999, data)

    def test_delete_type_existing(self, catalog_service, sample_catalog_templates):
        """Test deleting an existing cabinet type."""
        template_id = sample_catalog_templates[
            -1
        ].id  # Use last one to avoid affecting other tests

        result = catalog_service.delete_type(template_id)
        assert result is True

        # Verify it's deleted
        deleted_type = catalog_service.get_type(template_id)
        assert deleted_type is None

    def test_delete_type_nonexistent(self, catalog_service):
        """Test deleting a non-existent cabinet type."""
        result = catalog_service.delete_type(99999)
        assert result is False

    def test_get_kitchen_types(self, catalog_service):
        """Test getting available kitchen types."""
        kitchen_types = catalog_service.get_kitchen_types()

        assert isinstance(kitchen_types, list)
        assert "LOFT" in kitchen_types
        assert "PARIS" in kitchen_types
        assert "WINO" in kitchen_types

    def test_catalog_cabinet_type_conversion(
        self, catalog_service, sample_catalog_templates
    ):
        """Test that templates are properly converted to CatalogCabinetType."""
        catalog_type = catalog_service.get_type(sample_catalog_templates[0].id)

        assert isinstance(catalog_type, CatalogCabinetType)
        assert hasattr(catalog_type, "id")
        assert hasattr(catalog_type, "name")
        assert hasattr(catalog_type, "kitchen_type")
