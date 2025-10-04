"""
Integration tests for accessory functionality across cabinet lifecycle.
Tests accessory behavior during cabinet creation, editing, copying, and deletion.
"""

import pytest

from src.db_schema.orm_models import (
    Project,
    ProjectCabinet,
    ProjectCabinetPart,
    ProjectCabinetAccessorySnapshot,
    CabinetTemplate,
    CabinetPart,
)
from src.services.project_service import ProjectService
from src.services.formula_service import FormulaService
from src.services.catalog_service import CatalogService


class TestAccessoryIntegration:
    """Integration tests for accessories across cabinet operations"""

    def test_accessories_in_custom_cabinet_creation(
        self, session, project_service, formula_service, test_project
    ):
        """Test that accessories can be included during custom cabinet creation"""
        # GIVEN: Valid parts and initial accessories
        valid_parts = formula_service.compute_parts("D60", 600, 720, 560)
        parts_data = [
            {
                "part_name": part.part_name,
                "width_mm": part.width_mm,
                "height_mm": part.height_mm,
                "pieces": part.pieces,
                "material": part.material,
                "thickness_mm": part.thickness_mm,
                "wrapping": part.wrapping,
                "comments": part.comments,
            }
            for part in valid_parts
        ]

        initial_accessories = [
            {"name": "Hinge", "sku": "HNG-001", "count": 4},
            {"name": "Handle", "sku": "HDL-001", "count": 1},
        ]

        calc_context = {
            "template_name": "D60",
            "input_dimensions": {"width": 600, "height": 720, "depth": 560},
            "final_dimensions": {"width": 600, "height": 720, "depth": 560},
            "category": "DOLNY",
            "kitchen_type": "Modern",
            "description": "Cabinet with initial accessories",
            "created_via": "IntegrationTest",
        }

        # WHEN: Creating cabinet with initial accessories
        sequence_number = project_service.get_next_cabinet_sequence(test_project.id)
        cabinet = project_service.add_custom_cabinet(
            project_id=test_project.id,
            sequence_number=sequence_number,
            body_color="#ffffff",
            front_color="#ffffff",
            handle_type="Standard",
            quantity=1,
            custom_parts=parts_data,
            custom_accessories=initial_accessories,
            calc_context=calc_context,
        )

        # THEN: Cabinet should have the initial accessories
        assert cabinet is not None
        session.refresh(cabinet)
        assert len(cabinet.accessory_snapshots) == 2

        accessory_names = [acc.name for acc in cabinet.accessory_snapshots]
        assert "Hinge" in accessory_names
        assert "Handle" in accessory_names

        hinge = next(acc for acc in cabinet.accessory_snapshots if acc.name == "Hinge")
        assert hinge.sku == "HNG-001"
        assert hinge.count == 4

    def test_accessories_persist_through_cabinet_editing(
        self, session, project_service, custom_cabinet_with_accessories
    ):
        """Test that accessories persist when cabinet parts are edited"""
        # GIVEN: A cabinet with accessories and parts
        original_accessory_count = len(
            custom_cabinet_with_accessories.accessory_snapshots
        )
        original_part_count = len(custom_cabinet_with_accessories.parts)

        # Add an extra part to modify
        new_part_data = {
            "part_name": "Additional Shelf",
            "width_mm": 580,
            "height_mm": 300,
            "pieces": 1,
            "material": "PLYTA",
            "thickness_mm": 18,
            "wrapping": "NO",
            "comments": "Extra shelf added",
        }

        # WHEN: Editing the cabinet (adding a part)
        # Note: This assumes there's a method to edit cabinet parts
        # If not available, we'll directly add to database to simulate editing
        new_part = ProjectCabinetPart(
            project_cabinet_id=custom_cabinet_with_accessories.id,
            part_name=new_part_data["part_name"],
            width_mm=new_part_data["width_mm"],
            height_mm=new_part_data["height_mm"],
            pieces=new_part_data["pieces"],
            material=new_part_data["material"],
            thickness_mm=new_part_data["thickness_mm"],
            wrapping=new_part_data["wrapping"],
            comments=new_part_data["comments"],
        )
        session.add(new_part)
        session.commit()

        # THEN: Accessories should remain unchanged
        session.refresh(custom_cabinet_with_accessories)
        assert (
            len(custom_cabinet_with_accessories.accessory_snapshots)
            == original_accessory_count
        )
        assert len(custom_cabinet_with_accessories.parts) == original_part_count + 1

        # Verify specific accessories still exist
        accessory_names = [
            acc.name for acc in custom_cabinet_with_accessories.accessory_snapshots
        ]
        assert "Test Hinge" in accessory_names
        assert "Test Handle" in accessory_names

    def test_accessories_in_cabinet_copying(
        self, session, project_service, custom_cabinet_with_accessories, test_project
    ):
        """Test that accessories are copied when cabinet is duplicated"""
        # GIVEN: A cabinet with accessories
        original_accessories = custom_cabinet_with_accessories.accessory_snapshots
        original_count = len(original_accessories)

        # WHEN: Copying the cabinet (simulate cabinet duplication)
        sequence_number = project_service.get_next_cabinet_sequence(test_project.id)

        # Copy cabinet data
        copied_cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=sequence_number,
            type_id=custom_cabinet_with_accessories.type_id,
            body_color=custom_cabinet_with_accessories.body_color,
            front_color=custom_cabinet_with_accessories.front_color,
            handle_type=custom_cabinet_with_accessories.handle_type,
            quantity=custom_cabinet_with_accessories.quantity,
        )
        session.add(copied_cabinet)
        session.flush()  # Get the ID

        # Copy parts
        for part in custom_cabinet_with_accessories.parts:
            copied_part = ProjectCabinetPart(
                project_cabinet_id=copied_cabinet.id,
                part_name=part.part_name,
                width_mm=part.width_mm,
                height_mm=part.height_mm,
                pieces=part.pieces,
                material=part.material,
                thickness_mm=part.thickness_mm,
                wrapping=part.wrapping,
                comments=part.comments,
                source_part_id=part.source_part_id,
            )
            session.add(copied_part)

        # Copy accessories using the service method
        for accessory in original_accessories:
            project_service.add_accessory_to_cabinet(
                cabinet_id=copied_cabinet.id,
                name=accessory.name,
                sku=accessory.sku,
                count=accessory.count,
            )

        session.commit()

        # THEN: Copied cabinet should have same accessories
        session.refresh(copied_cabinet)
        assert len(copied_cabinet.accessory_snapshots) == original_count

        # Verify accessory details match
        copied_accessory_data = [
            (acc.name, acc.sku, acc.count) for acc in copied_cabinet.accessory_snapshots
        ]
        original_accessory_data = [
            (acc.name, acc.sku, acc.count) for acc in original_accessories
        ]

        # Sort both lists for comparison (order might differ)
        copied_accessory_data.sort()
        original_accessory_data.sort()

        assert copied_accessory_data == original_accessory_data

    def test_accessories_cascade_delete_with_cabinet(
        self, session, project_service, custom_cabinet_with_accessories
    ):
        """Test that accessories are deleted when cabinet is deleted"""
        # GIVEN: A cabinet with accessories
        accessory_ids = [
            acc.id for acc in custom_cabinet_with_accessories.accessory_snapshots
        ]

        assert len(accessory_ids) > 0  # Ensure we have accessories to test

        # WHEN: Deleting the cabinet
        session.delete(custom_cabinet_with_accessories)
        session.commit()

        # THEN: Accessories should be deleted too
        remaining_accessories = (
            session.query(ProjectCabinetAccessorySnapshot)
            .filter(ProjectCabinetAccessorySnapshot.id.in_(accessory_ids))
            .all()
        )

        assert len(remaining_accessories) == 0

    def test_accessories_with_cabinet_quantity_changes(
        self, session, project_service, custom_cabinet_with_accessories
    ):
        """Test accessory behavior when cabinet quantity changes"""
        # GIVEN: A cabinet with accessories and quantity of 1
        original_quantity = custom_cabinet_with_accessories.quantity
        assert original_quantity == 1

        original_accessories = list(custom_cabinet_with_accessories.accessory_snapshots)
        original_accessory_counts = [acc.count for acc in original_accessories]

        # WHEN: Changing cabinet quantity
        new_quantity = 3
        custom_cabinet_with_accessories.quantity = new_quantity
        session.commit()

        # THEN: Accessories should remain unchanged (business rule dependent)
        # Note: This test assumes accessories don't auto-scale with cabinet quantity
        session.refresh(custom_cabinet_with_accessories)
        current_accessory_counts = [
            acc.count for acc in custom_cabinet_with_accessories.accessory_snapshots
        ]

        # Accessories remain the same regardless of cabinet quantity
        assert current_accessory_counts == original_accessory_counts

    def test_accessory_operations_across_multiple_cabinets(
        self, session, project_service, formula_service, test_project
    ):
        """Test accessory operations across multiple cabinets in same project"""
        # GIVEN: Multiple cabinets in the same project
        cabinets = []
        for i in range(3):
            valid_parts = formula_service.compute_parts("D60", 600, 720, 560)
            parts_data = [
                {
                    "part_name": part.part_name,
                    "width_mm": part.width_mm,
                    "height_mm": part.height_mm,
                    "pieces": part.pieces,
                    "material": part.material,
                    "thickness_mm": part.thickness_mm,
                    "wrapping": part.wrapping,
                    "comments": part.comments,
                }
                for part in valid_parts
            ]

            calc_context = {
                "template_name": "D60",
                "input_dimensions": {"width": 600, "height": 720, "depth": 560},
                "final_dimensions": {"width": 600, "height": 720, "depth": 560},
                "category": "DOLNY",
                "kitchen_type": "Modern",
                "description": f"Test cabinet {i + 1}",
                "created_via": "MultiCabinetTest",
            }

            sequence_number = project_service.get_next_cabinet_sequence(test_project.id)
            cabinet = project_service.add_custom_cabinet(
                project_id=test_project.id,
                sequence_number=sequence_number,
                body_color="#ffffff",
                front_color="#ffffff",
                handle_type="Standard",
                quantity=1,
                custom_parts=parts_data,
                custom_accessories=[],
                calc_context=calc_context,
            )
            cabinets.append(cabinet)

        # WHEN: Adding different accessories to each cabinet
        accessories_data = [
            ("Cabinet 1 Hinge", "C1-HNG-001", 4),
            ("Cabinet 2 Handle", "C2-HDL-001", 2),
            ("Cabinet 3 Drawer Slide", "C3-DRW-001", 6),
        ]

        for i, (name, sku, count) in enumerate(accessories_data):
            result = project_service.add_accessory_to_cabinet(
                cabinet_id=cabinets[i].id, name=name, sku=sku, count=count
            )
            assert result is True

        # THEN: Each cabinet should have its own accessories
        for i, cabinet in enumerate(cabinets):
            session.refresh(cabinet)
            assert len(cabinet.accessory_snapshots) == 1

            accessory = cabinet.accessory_snapshots[0]
            expected_name, expected_sku, expected_count = accessories_data[i]
            assert accessory.name == expected_name
            assert accessory.sku == expected_sku
            assert accessory.count == expected_count

    def test_accessory_integration_with_standard_cabinets(
        self, session, project_service, catalog_service, test_project
    ):
        """Test accessories work with standard (template-based) cabinets"""
        # GIVEN: A standard cabinet template
        # First create a simple template
        template = CabinetTemplate(
            nazwa="StandardD60",
            kitchen_type="Standard",
        )
        session.add(template)
        session.flush()

        # Add a part to the template
        template_part = CabinetPart(
            cabinet_type_id=template.id,
            part_name="Standard Side Panel",
            width_mm=560,
            height_mm=720,
            pieces=2,
            material="PLYTA",
            thickness_mm=18,
            wrapping="NO",
        )
        session.add(template_part)
        session.commit()

        # WHEN: Creating a standard cabinet and adding accessories
        sequence_number = project_service.get_next_cabinet_sequence(test_project.id)
        standard_cabinet = project_service.add_cabinet(
            project_id=test_project.id,
            sequence_number=sequence_number,
            type_id=template.id,
            body_color="#ffffff",
            front_color="#ffffff",
            handle_type="Standard",
            quantity=1,
        )

        # Add accessories to standard cabinet
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=standard_cabinet.id,
            name="Standard Hinge",
            sku="STD-HNG-001",
            count=4,
        )

        # THEN: Standard cabinet should support accessories
        assert result is True
        session.refresh(standard_cabinet)
        assert len(standard_cabinet.accessory_snapshots) == 1

        accessory = standard_cabinet.accessory_snapshots[0]
        assert accessory.name == "Standard Hinge"
        assert accessory.sku == "STD-HNG-001"
        assert accessory.count == 4

    def test_accessory_data_integrity_across_sessions(
        self, engine, project_service_factory, test_project
    ):
        """Test that accessory data persists correctly across database sessions"""
        # GIVEN: A cabinet with accessories created in one session
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=engine)

        # First session - create cabinet and accessories
        session1 = Session()
        try:
            service1 = project_service_factory(session1)
            formula_service = FormulaService(session1)

            # Create cabinet
            valid_parts = formula_service.compute_parts("D60", 600, 720, 560)
            parts_data = [
                {
                    "part_name": part.part_name,
                    "width_mm": part.width_mm,
                    "height_mm": part.height_mm,
                    "pieces": part.pieces,
                    "material": part.material,
                    "thickness_mm": part.thickness_mm,
                    "wrapping": part.wrapping,
                    "comments": part.comments,
                }
                for part in valid_parts
            ]

            calc_context = {
                "template_name": "D60",
                "input_dimensions": {"width": 600, "height": 720, "depth": 560},
                "final_dimensions": {"width": 600, "height": 720, "depth": 560},
                "category": "DOLNY",
                "kitchen_type": "Modern",
                "description": "Cross-session test cabinet",
                "created_via": "CrossSessionTest",
            }

            sequence_number = service1.get_next_cabinet_sequence(test_project.id)
            cabinet = service1.add_custom_cabinet(
                project_id=test_project.id,
                sequence_number=sequence_number,
                body_color="#ffffff",
                front_color="#ffffff",
                handle_type="Standard",
                quantity=1,
                custom_parts=parts_data,
                custom_accessories=[],
                calc_context=calc_context,
            )

            # Add accessories
            service1.add_accessory_to_cabinet(
                cabinet_id=cabinet.id,
                name="Session Test Hinge",
                sku="SESS-HNG-001",
                count=4,
            )

            cabinet_id = cabinet.id
            session1.commit()
        finally:
            session1.close()

        # WHEN: Accessing the data in a different session
        session2 = Session()
        try:
            service2 = project_service_factory(session2)

            # Retrieve cabinet
            retrieved_cabinet = (
                session2.query(ProjectCabinet)
                .filter(ProjectCabinet.id == cabinet_id)
                .first()
            )

            # THEN: Accessories should be accessible and correct
            assert retrieved_cabinet is not None
            assert len(retrieved_cabinet.accessory_snapshots) == 1

            accessory = retrieved_cabinet.accessory_snapshots[0]
            assert accessory.name == "Session Test Hinge"
            assert accessory.sku == "SESS-HNG-001"
            assert accessory.count == 4

            # Test operations in new session
            result = service2.update_accessory_quantity(accessory.id, 6)
            assert result is True

            session2.refresh(accessory)
            assert accessory.count == 6

        finally:
            session2.close()


# Fixtures
@pytest.fixture
def project_service_factory():
    """Factory function for creating ProjectService instances"""

    def _create_service(session):
        return ProjectService(session)

    return _create_service


@pytest.fixture
def catalog_service(session):
    """Create a CatalogService instance"""
    return CatalogService(session)


@pytest.fixture
def test_project(session):
    """Create a test project"""
    project = Project(
        name="Test Integration Project",
        client_name="Integration Client",
        client_address="Integration Address",
        client_phone="123-456-789",
        client_email="integration@example.com",
        order_number="INT-001",
        kitchen_type="Modern",
    )
    session.add(project)
    session.commit()
    return project


@pytest.fixture
def project_service(session):
    """Create a ProjectService instance"""
    return ProjectService(session)


@pytest.fixture
def formula_service(session):
    """Create a FormulaService instance"""
    return FormulaService(session)


@pytest.fixture
def custom_cabinet_with_accessories(
    session, test_project, project_service, formula_service
):
    """Create a custom cabinet with pre-loaded accessories"""
    # Create cabinet
    valid_parts = formula_service.compute_parts("D60", 600, 720, 560)
    parts_data = [
        {
            "part_name": part.part_name,
            "width_mm": part.width_mm,
            "height_mm": part.height_mm,
            "pieces": part.pieces,
            "material": part.material,
            "thickness_mm": part.thickness_mm,
            "wrapping": part.wrapping,
            "comments": part.comments,
        }
        for part in valid_parts
    ]

    calc_context = {
        "template_name": "D60",
        "input_dimensions": {"width": 600, "height": 720, "depth": 560},
        "final_dimensions": {"width": 600, "height": 720, "depth": 560},
        "category": "DOLNY",
        "kitchen_type": "Modern",
        "description": "Cabinet with accessories for integration testing",
        "created_via": "IntegrationTestFixture",
    }

    sequence_number = project_service.get_next_cabinet_sequence(test_project.id)
    cabinet = project_service.add_custom_cabinet(
        project_id=test_project.id,
        sequence_number=sequence_number,
        body_color="#ffffff",
        front_color="#ffffff",
        handle_type="Standard",
        quantity=1,
        custom_parts=parts_data,
        custom_accessories=[],
        calc_context=calc_context,
    )

    # Add accessories
    project_service.add_accessory_to_cabinet(
        cabinet_id=cabinet.id, name="Test Hinge", sku="TEST-HNG-001", count=4
    )
    project_service.add_accessory_to_cabinet(
        cabinet_id=cabinet.id, name="Test Handle", sku="TEST-HDL-001", count=1
    )

    session.refresh(cabinet)
    return cabinet
