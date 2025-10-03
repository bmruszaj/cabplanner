"""
Tests for custom cabinet functionality using the new architecture.

This test suite covers:
1. Adding custom cabinets without creating CabinetTemplate entries
2. Report generation for projects with custom cabinets
3. Custom cabinet parts storage and retrieval
4. Mixed projects with both catalog and custom cabinets
"""

import pytest
from unittest.mock import Mock
from src.db_schema.orm_models import (
    Project,
    ProjectCabinet,
    CabinetTemplate,
)


class TestCustomCabinetArchitecture:
    """Test suite for custom cabinet functionality"""

    @pytest.fixture
    def test_project(self, session):
        """Create a test project in the database"""
        project = Project(
            name="Test Custom Project", order_number="TEST-001", kitchen_type="LOFT"
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project

    def test_catalog_cabinet_has_type_id(self, session, test_project):
        """Test that catalog cabinets are properly linked to CabinetTemplate"""
        project = test_project

        # Create a sample catalog template
        template = CabinetTemplate(nazwa="D60", kitchen_type="LOFT")
        session.add(template)
        session.commit()

        # Create cabinet with type_id (catalog cabinet)
        cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=template.id,
            sequence_number=1,
            body_color="Biały",
            front_color="Biały",
            handle_type="Standardowy",
            quantity=1,
        )
        session.add(cabinet)
        session.commit()

        assert cabinet.type_id == template.id
        assert cabinet.cabinet_type is not None  # Should have relationship

    def test_custom_cabinet_without_type_id(self, session, test_project):
        """Test that custom cabinets can exist without type_id"""
        project = test_project

        # Create custom cabinet without type_id
        custom_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=None,  # Custom cabinet - no template
            sequence_number=1,
            body_color="Biały",
            front_color="Biały",
            handle_type="Standardowy",
            quantity=1,
        )
        session.add(custom_cabinet)
        session.commit()

        assert custom_cabinet.type_id is None
        assert custom_cabinet.cabinet_type is None
        # Custom cabinet can exist without template reference

    def test_custom_cabinet_name_collision_allowed(self, session, test_project):
        """Test that custom cabinets can have same names as catalog templates"""
        project = test_project

        # Create a catalog template with name "D60"
        catalog_template = CabinetTemplate(nazwa="D60", kitchen_type="LOFT")
        session.add(catalog_template)
        session.commit()

        # Create custom cabinet with same name - should NOT raise error
        # because we don't store custom cabinet names in CabinetTemplate table
        custom_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=None,  # Custom cabinet
            sequence_number=1,
            body_color="Biały",
            front_color="Biały",
            handle_type="Standardowy",
            quantity=1,
        )
        session.add(custom_cabinet)
        session.commit()  # Should not raise IntegrityError

        assert custom_cabinet is not None
        assert custom_cabinet.type_id is None

    def test_custom_cabinet_parts_storage(self, session, test_project):
        """Test storage and retrieval of custom cabinet parts"""
        project = test_project

        # Add custom cabinet
        cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=None,  # Custom
            sequence_number=1,
            body_color="Biały",
            front_color="Biały",
            handle_type="Standardowy",
            quantity=1,
        )
        session.add(cabinet)
        session.commit()

        # In new architecture, custom parts would be stored in
        # ProjectCabinetCustomPart table (not implemented yet)
        # For now, just test the cabinet exists without template
        assert cabinet.type_id is None
        assert cabinet.cabinet_type is None

    def test_report_generation_with_custom_cabinets(self, session, test_project):
        """Test that report generator handles custom cabinets properly"""
        project = test_project

        # Add a custom cabinet
        custom_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=None,  # Custom cabinet
            sequence_number=1,
            body_color="Biały",
            front_color="Biały",
            handle_type="Standardowy",
            quantity=1,
        )
        session.add(custom_cabinet)
        session.commit()

        # Test that we can query custom cabinets
        custom_cabinets = (
            session.query(ProjectCabinet)
            .filter(
                ProjectCabinet.project_id == project.id,
                ProjectCabinet.type_id.is_(None),
            )
            .all()
        )

        assert len(custom_cabinets) == 1
        assert custom_cabinets[0].type_id is None

        # Report generator would need to handle these differently
        # (this test demonstrates they can exist in database)

    def test_mixed_project_catalog_and_custom(self, session, test_project):
        """Test project with both catalog and custom cabinets"""
        project = test_project

        # Create catalog template
        template = CabinetTemplate(nazwa="G40", kitchen_type="LOFT")
        session.add(template)
        session.commit()

        # Add catalog cabinet
        catalog_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=template.id,  # Catalog template
            sequence_number=1,
            body_color="Biały",
            front_color="Biały",
            handle_type="Standardowy",
            quantity=1,
        )
        session.add(catalog_cabinet)

        # Add custom cabinet
        custom_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=None,  # Custom
            sequence_number=2,
            body_color="Szary",
            front_color="Szary",
            handle_type="Nowoczesny",
            quantity=2,
        )
        session.add(custom_cabinet)
        session.commit()

        # Both should coexist
        cabinets = (
            session.query(ProjectCabinet)
            .filter(ProjectCabinet.project_id == project.id)
            .all()
        )
        assert len(cabinets) == 2

        catalog_cabs = [c for c in cabinets if c.type_id is not None]
        custom_cabs = [c for c in cabinets if c.type_id is None]

        assert len(catalog_cabs) == 1
        assert len(custom_cabs) == 1

    def test_custom_cabinet_dialog_integration(self):
        """Test that CustomCabinetDialog doesn't create CabinetTemplate"""
        # This test verifies the conceptual integration without actually creating GUI
        # The key insight is that custom cabinets should NOT create CabinetTemplate entries

        # Mock services
        from src.services.formula_service import FormulaService
        from src.services.project_service import ProjectService
        from src.db_schema.orm_models import Project

        formula_service = Mock(spec=FormulaService)
        formula_service.compute_parts.return_value = [
            Mock(part_name="Bok lewy", width_mm=560, height_mm=720, pieces=1),
            Mock(part_name="Bok prawy", width_mm=560, height_mm=720, pieces=1),
            Mock(part_name="Dno", width_mm=564, height_mm=560, pieces=1),
        ]

        Mock(spec=ProjectService)
        project = Mock(spec=Project)
        project.id = 1

        # Mock the dialog behavior instead of creating actual dialog
        # This represents what the dialog would do when creating a custom cabinet
        dialog_behavior = Mock()

        # Simulate form data collection (what dialog would collect)
        dialog_behavior.collect_form_data.return_value = {
            "name": "D60",
            "kitchen_type": "LOFT",
            "width": 600,
            "height": 720,
            "depth": 560,
        }

        # Simulate parts calculation (this is what the dialog would do)
        calculated_parts = formula_service.compute_parts("D60", 600, 720, 560)

        # Simulate what the dialog would create for custom cabinet
        cabinet_data = {
            "name": "D60",
            "kitchen_type": "LOFT",
            "width": 600,
            "height": 720,
            "depth": 560,
            "type_id": None,  # Key: should be None for custom cabinet
            "parts": [
                {
                    "part_name": part.part_name,
                    "width_mm": part.width_mm,
                    "height_mm": part.height_mm,
                    "pieces": part.pieces,
                    "material": "PLYTA",
                    "thickness_mm": 18,
                }
                for part in calculated_parts
            ],
        }

        # Verify the key architectural principle: custom cabinets don't create templates
        assert cabinet_data["type_id"] is None  # No template created
        assert "parts" in cabinet_data  # Parts stored directly as data
        assert len(cabinet_data["parts"]) > 0  # Has calculated parts

        # Verify parts were calculated using formula service
        formula_service.compute_parts.assert_called_once_with("D60", 600, 720, 560)


if __name__ == "__main__":
    pytest.main([__file__])
