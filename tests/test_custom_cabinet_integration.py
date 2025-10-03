"""
Integration test for custom cabinet functionality with new architecture.

This test verifies that custom cabinets can be added without creating
CabinetTemplate entries and that name conflicts are resolved.
"""

import pytest
from src.db_schema.orm_models import (
    Project,
    ProjectCabinet,
    CabinetTemplate,
    ProjectCabinetPart,
)
from src.controllers.project_details_controller import ProjectDetailsController
from src.services.project_service import ProjectService


class TestCustomCabinetIntegration:
    """Integration test for custom cabinet functionality"""

    def test_add_custom_cabinet_d60_no_conflict(self, session):
        """Test adding custom cabinet D60 doesn't conflict with existing catalog template"""
        # Create a project
        project = Project(
            name="Test Project", order_number="TEST-001", kitchen_type="LOFT"
        )
        session.add(project)
        session.commit()

        # Create existing catalog template with same name "D60"
        catalog_template = CabinetTemplate(nazwa="D60", kitchen_type="LOFT")
        session.add(catalog_template)
        session.commit()

        # Verify catalog template exists
        assert (
            session.query(CabinetTemplate)
            .filter(CabinetTemplate.nazwa == "D60")
            .first()
            is not None
        )

        # Create controller
        project_service = ProjectService(session)
        controller = ProjectDetailsController(session, project_service)
        controller.project = project

        # Prepare custom cabinet data with name "D60" (same as catalog)
        custom_cabinet_data = {
            "name": "D60",  # Same name as catalog template
            "kitchen_type": "LOFT",
            "width": 600,
            "height": 720,
            "depth": 560,
            "parts": [
                {
                    "part_name": "Bok lewy",
                    "width_mm": 560,
                    "height_mm": 720,
                    "pieces": 1,
                    "material": "PLYTA",
                    "thickness_mm": 18,
                },
                {
                    "part_name": "Bok prawy",
                    "width_mm": 560,
                    "height_mm": 720,
                    "pieces": 1,
                    "material": "PLYTA",
                    "thickness_mm": 18,
                },
                {
                    "part_name": "Dno",
                    "width_mm": 564,
                    "height_mm": 560,
                    "pieces": 1,
                    "material": "PLYTA",
                    "thickness_mm": 18,
                },
            ],
        }

        # This should NOT fail even though "D60" catalog template exists
        custom_cabinet = controller.add_cabinet(project.id, **custom_cabinet_data)

        # Verify custom cabinet was created
        assert custom_cabinet is not None
        assert custom_cabinet.type_id is None  # Custom cabinet
        assert custom_cabinet.project_id == project.id

        # Verify custom parts were created
        custom_parts = (
            session.query(ProjectCabinetPart)
            .filter(ProjectCabinetPart.project_cabinet_id == custom_cabinet.id)
            .all()
        )

        assert len(custom_parts) == 3
        part_names = [part.part_name for part in custom_parts]
        assert "Bok lewy" in part_names
        assert "Bok prawy" in part_names
        assert "Dno" in part_names

        # Verify catalog template still exists and wasn't affected
        catalog_templates = (
            session.query(CabinetTemplate).filter(CabinetTemplate.nazwa == "D60").all()
        )
        assert len(catalog_templates) == 1  # Only the original catalog template

        # Verify no additional CabinetTemplate was created for custom cabinet
        all_templates = session.query(CabinetTemplate).all()
        assert len(all_templates) == 1  # Only the original catalog template

    def test_project_with_both_catalog_and_custom_d60(self, session):
        """Test project can have both catalog D60 and custom D60 cabinets"""
        # Create a project
        project = Project(
            name="Mixed Project", order_number="MIXED-001", kitchen_type="LOFT"
        )
        session.add(project)
        session.commit()

        # Create catalog template D60
        catalog_template = CabinetTemplate(nazwa="D60", kitchen_type="LOFT")
        session.add(catalog_template)
        session.commit()

        # Create catalog cabinet using template
        catalog_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=catalog_template.id,
            sequence_number=1,
            body_color="Biały",
            front_color="Biały",
            handle_type="Standardowy",
            quantity=1,
        )
        session.add(catalog_cabinet)

        # Create custom cabinet with same "D60" name using controller
        project_service = ProjectService(session)
        controller = ProjectDetailsController(session, project_service)
        controller.project = project

        custom_cabinet_data = {
            "name": "D60",  # Same name but different implementation
            "kitchen_type": "LOFT",
            "parts": [
                {
                    "part_name": "Custom Bok",
                    "width_mm": 580,  # Different dimensions
                    "height_mm": 740,
                    "pieces": 2,
                    "material": "HDF",
                    "thickness_mm": 12,
                }
            ],
        }

        controller.add_cabinet(project.id, **custom_cabinet_data)

        # Verify both cabinets exist in project
        project_cabinets = (
            session.query(ProjectCabinet)
            .filter(ProjectCabinet.project_id == project.id)
            .all()
        )

        assert len(project_cabinets) == 2

        # Verify catalog cabinet
        catalog_cabs = [cab for cab in project_cabinets if cab.type_id is not None]
        assert len(catalog_cabs) == 1
        assert catalog_cabs[0].cabinet_type.nazwa == "D60"

        # Verify custom cabinet
        custom_cabs = [cab for cab in project_cabinets if cab.type_id is None]
        assert len(custom_cabs) == 1

        # Verify custom parts
        custom_parts = (
            session.query(ProjectCabinetPart)
            .filter(ProjectCabinetPart.project_cabinet_id == custom_cabs[0].id)
            .all()
        )
        assert len(custom_parts) == 1
        assert custom_parts[0].part_name == "Custom Bok"


if __name__ == "__main__":
    pytest.main([__file__])
