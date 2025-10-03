"""
Test for report generation with custom ca            ProjectCabinetPart(
                project_cabinet_id=custom_cabinet.id,
                part_name="Bok prawy",
                width_mm=560,
                height_mm=720,
                pieces=1,
                material="PLYTA",
                thickness_mm=18,
                comments="Panel boczny",
This test verifies that ReportGenerator properly processes custom cabinets
that have type_id=NULL and use ProjectCabinetCustomPart for parts storage.
"""

import pytest
from src.db_schema.orm_models import (
    Project,
    ProjectCabinet,
    CabinetTemplate,
    ProjectCabinetPart,
)
from src.services.report_generator import ReportGenerator


class TestReportGeneratorCustomCabinets:
    """Test report generation with custom cabinets"""

    def test_report_generator_handles_custom_cabinets(self, session):
        """Test that ReportGenerator processes custom cabinets correctly"""
        # Create a project
        project = Project(
            name="Custom Cabinet Test Project",
            order_number="CUSTOM-001",
            kitchen_type="LOFT",
        )
        session.add(project)
        session.commit()

        # Create a custom cabinet (type_id=NULL)
        custom_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=None,  # Custom cabinet
            sequence_number=1,
            body_color="Biały",
            front_color="Szary",
            handle_type="Nowoczesny",
            quantity=2,
        )
        session.add(custom_cabinet)
        session.commit()

        # Add custom parts
        custom_parts = [
            ProjectCabinetPart(
                project_cabinet_id=custom_cabinet.id,
                part_name="Bok lewy",
                width_mm=560,
                height_mm=720,
                pieces=1,
                material="PLYTA",
                thickness_mm=18,
                comments="Panel boczny",
            ),
            ProjectCabinetPart(
                project_cabinet_id=custom_cabinet.id,
                part_name="Front główny",
                width_mm=596,
                height_mm=718,
                pieces=1,
                material="FRONT",
                thickness_mm=18,
                comments="Front MDF",
            ),
            ProjectCabinetPart(
                project_cabinet_id=custom_cabinet.id,
                part_name="Tył HDF",
                width_mm=592,
                height_mm=712,
                pieces=1,
                material="HDF",
                thickness_mm=3,
                comments="Tył płyta HDF",
            ),
        ]

        for part in custom_parts:
            session.add(part)
        session.commit()

        # Load the project with relationships
        session.refresh(project)
        session.refresh(custom_cabinet)

        # Create report generator
        report_generator = ReportGenerator()

        # Extract materials from project
        formatki, fronty, hdf, akcesoria = report_generator._extract_elements_directly(
            project
        )

        # Verify FORMATKI (panels) - should have "Bok lewy"
        formatki_names = [part.name for part in formatki]
        assert "Bok lewy" in formatki_names

        # Find the panel part
        panel_part = next(part for part in formatki if part.name == "Bok lewy")
        assert panel_part.quantity == 2  # 1 piece * 2 cabinet quantity
        assert panel_part.width == 560
        assert panel_part.height == 720
        assert panel_part.color == "Biały"  # body_color
        assert panel_part.seq == "①"  # sequence number 1
        assert "Panel boczny" in panel_part.notes

        # Verify FRONTY (fronts) - should have "Front główny"
        fronty_names = [part.name for part in fronty]
        assert "Front główny" in fronty_names

        # Find the front part
        front_part = next(part for part in fronty if part.name == "Front główny")
        assert front_part.quantity == 2  # 1 piece * 2 cabinet quantity
        assert front_part.width == 596
        assert front_part.height == 718
        assert front_part.color == "Szary"  # front_color
        assert front_part.seq == "①"  # sequence number 1
        assert "Handle: Nowoczesny" in front_part.notes

        # Verify HDF - should have "Tył HDF"
        hdf_names = [part.name for part in hdf]
        assert "Tył HDF" in hdf_names

        # Find the HDF part
        hdf_part = next(part for part in hdf if part.name == "Tył HDF")
        assert hdf_part.quantity == 2  # 1 piece * 2 cabinet quantity
        assert hdf_part.width == 592
        assert hdf_part.height == 712
        assert hdf_part.color == ""  # HDF has no color
        assert hdf_part.seq == "①"  # sequence number 1
        assert "Tył płyta HDF" in hdf_part.notes

        # No accessories should be present since we didn't add any
        assert len(akcesoria) == 0

    def test_mixed_project_catalog_and_custom_cabinets(self, session):
        """Test report generation for project with both catalog and custom cabinets"""
        # Create a project
        project = Project(
            name="Mixed Cabinet Project", order_number="MIXED-002", kitchen_type="LOFT"
        )
        session.add(project)
        session.commit()

        # Create catalog template
        catalog_template = CabinetTemplate(nazwa="G40", kitchen_type="LOFT")
        session.add(catalog_template)
        session.commit()

        # Create catalog cabinet
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

        # Create custom cabinet
        custom_cabinet = ProjectCabinet(
            project_id=project.id,
            type_id=None,  # Custom cabinet
            sequence_number=2,
            body_color="Szary",
            front_color="Czarny",
            handle_type="Metalowy",
            quantity=1,
        )
        session.add(custom_cabinet)
        session.commit()

        # Add custom parts to custom cabinet
        custom_part = ProjectCabinetPart(
            project_cabinet_id=custom_cabinet.id,
            part_name="Custom Panel",
            width_mm=400,
            height_mm=600,
            pieces=1,
            material="PLYTA",
            thickness_mm=18,
        )
        session.add(custom_part)
        session.commit()

        # Load the project with relationships
        session.refresh(project)
        session.refresh(catalog_cabinet)
        session.refresh(custom_cabinet)

        # Create report generator
        report_generator = ReportGenerator()

        # Extract materials from project - should not fail
        formatki, fronty, hdf, akcesoria = report_generator._extract_elements_directly(
            project
        )

        # Should have parts from custom cabinet
        custom_parts = [part for part in formatki if part.seq == "②"]  # sequence 2
        assert len(custom_parts) >= 1

        custom_part_found = next(
            (part for part in custom_parts if part.name == "Custom Panel"), None
        )
        assert custom_part_found is not None
        assert custom_part_found.width == 400
        assert custom_part_found.height == 600
        assert custom_part_found.color == "Szary"  # body_color


if __name__ == "__main__":
    pytest.main([__file__])
