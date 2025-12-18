"""
Integration tests for parts functionality across cabinet lifecycle.
Tests parts behavior during cabinet creation, editing, copying, and deletion.
"""

import pytest

from src.db_schema.orm_models import (
    Project,
    ProjectCabinet,
    ProjectCabinetPart,
    CabinetTemplate,
    CabinetPart,
)
from src.services.project_service import ProjectService
from src.services.formula_service import FormulaService
from src.services.catalog_service import CatalogService
from src.services.template_service import TemplateService


class TestPartsIntegration:
    """Integration tests for parts across cabinet operations"""

    @pytest.fixture
    def test_project(self, session, project_service):
        """Create a test project for integration tests"""
        return project_service.create_project(
            name="Parts Integration Test",
            order_number="INT-001",
        )

    @pytest.fixture
    def formula_service(self, session):
        """Provide FormulaService instance"""
        from src.services.formula_constants_service import FormulaConstantsService
        from src.services.formula_engine import FormulaEngine

        fcs = FormulaConstantsService(session)
        return FormulaService(session, FormulaEngine(fcs))

    @pytest.fixture
    def catalog_template(self, session, template_service):
        """Create a catalog template with parts"""
        template = template_service.create_template(
            name="D60",
            kitchen_type="MODERN",
        )

        # Add parts to template
        parts_data = [
            {"part_name": "Bok prawy", "width_mm": 560, "height_mm": 702},
            {"part_name": "Bok lewy", "width_mm": 560, "height_mm": 702},
            {"part_name": "Wieniec górny", "width_mm": 564, "height_mm": 560},
            {"part_name": "Wieniec dolny", "width_mm": 564, "height_mm": 560},
        ]

        for part_data in parts_data:
            template_service.add_part(
                template_id=template.id,
                part_name=part_data["part_name"],
                width_mm=part_data["width_mm"],
                height_mm=part_data["height_mm"],
                pieces=1,
                material="PLYTA",
                thickness_mm=18,
            )

        session.refresh(template)
        return template

    @pytest.fixture
    def custom_cabinet_with_parts(
        self, session, project_service, test_project, template_service
    ):
        """Create a custom cabinet with parts for testing"""
        template = template_service.create_template(
            name="CustomCabinet",
            kitchen_type="MODERN",
        )

        cabinet = ProjectCabinet(
            project_id=test_project.id,
            type_id=template.id,
            sequence_number=1,
            quantity=1,
            body_color="#ffffff",
            front_color="#000000",
            handle_type="Standard",
        )
        session.add(cabinet)
        session.flush()

        # Add some parts
        parts = [
            ProjectCabinetPart(
                project_cabinet_id=cabinet.id,
                part_name="Bok prawy",
                width_mm=560,
                height_mm=720,
                pieces=1,
                material="PLYTA",
                thickness_mm=18,
            ),
            ProjectCabinetPart(
                project_cabinet_id=cabinet.id,
                part_name="Bok lewy",
                width_mm=560,
                height_mm=720,
                pieces=1,
                material="PLYTA",
                thickness_mm=18,
            ),
            ProjectCabinetPart(
                project_cabinet_id=cabinet.id,
                part_name="Półka",
                width_mm=564,
                height_mm=540,
                pieces=2,
                material="PLYTA",
                thickness_mm=18,
            ),
        ]
        for part in parts:
            session.add(part)

        session.commit()
        return cabinet

    def test_parts_in_custom_cabinet_creation(
        self, session, project_service, test_project
    ):
        """Test that parts can be included during custom cabinet creation"""
        # GIVEN: Parts data for cabinet
        parts_data = [
            {
                "part_name": "Bok prawy",
                "width_mm": 560,
                "height_mm": 720,
                "pieces": 1,
                "material": "PLYTA",
                "thickness_mm": 18,
                "wrapping": "NO",
                "comments": "",
            },
            {
                "part_name": "Bok lewy",
                "width_mm": 560,
                "height_mm": 720,
                "pieces": 1,
                "material": "PLYTA",
                "thickness_mm": 18,
                "wrapping": "NO",
                "comments": "",
            },
            {
                "part_name": "Wieniec górny",
                "width_mm": 564,
                "height_mm": 560,
                "pieces": 1,
                "material": "PLYTA",
                "thickness_mm": 18,
                "wrapping": "NO",
                "comments": "",
            },
        ]

        calc_context = {
            "template_name": "CustomD60",
            "input_dimensions": {"width": 600, "height": 720, "depth": 560},
            "final_dimensions": {"width": 600, "height": 720, "depth": 560},
            "category": "DOLNY",
            "kitchen_type": "Modern",
            "description": "Cabinet with initial parts",
            "created_via": "IntegrationTest",
        }

        # WHEN: Creating cabinet with initial parts
        sequence_number = project_service.get_next_cabinet_sequence(test_project.id)
        cabinet = project_service.add_custom_cabinet(
            project_id=test_project.id,
            sequence_number=sequence_number,
            body_color="#ffffff",
            front_color="#ffffff",
            handle_type="Standard",
            quantity=1,
            custom_parts=parts_data,
            calc_context=calc_context,
        )

        # THEN: Cabinet should have the initial parts
        assert cabinet is not None
        session.refresh(cabinet)
        assert len(cabinet.parts) == 3

        part_names = [p.part_name for p in cabinet.parts]
        assert "Bok prawy" in part_names
        assert "Bok lewy" in part_names
        assert "Wieniec górny" in part_names

    def test_parts_persist_through_accessory_changes(
        self, session, project_service, custom_cabinet_with_parts
    ):
        """Test that parts persist when accessories are changed"""
        # GIVEN: A cabinet with parts
        original_part_count = len(custom_cabinet_with_parts.parts)
        original_part_names = [p.part_name for p in custom_cabinet_with_parts.parts]

        # WHEN: Adding accessories to the cabinet
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet_with_parts.id,
            name="Hinge",
            sku="HNG-001",
            count=4,
        )
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet_with_parts.id,
            name="Handle",
            sku="HDL-001",
            count=1,
        )

        # THEN: Parts should remain unchanged
        session.refresh(custom_cabinet_with_parts)
        assert len(custom_cabinet_with_parts.parts) == original_part_count

        current_part_names = [p.part_name for p in custom_cabinet_with_parts.parts]
        for name in original_part_names:
            assert name in current_part_names

        # AND: Accessories should be added
        assert len(custom_cabinet_with_parts.accessory_snapshots) == 2

    def test_parts_in_cabinet_copying(
        self, session, project_service, custom_cabinet_with_parts, test_project
    ):
        """Test that parts are copied when cabinet is duplicated"""
        # GIVEN: A cabinet with parts
        original_parts = custom_cabinet_with_parts.parts
        original_count = len(original_parts)

        # WHEN: Copying the cabinet
        sequence_number = project_service.get_next_cabinet_sequence(test_project.id)

        copied_cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=sequence_number,
            type_id=custom_cabinet_with_parts.type_id,
            body_color=custom_cabinet_with_parts.body_color,
            front_color=custom_cabinet_with_parts.front_color,
            handle_type=custom_cabinet_with_parts.handle_type,
            quantity=custom_cabinet_with_parts.quantity,
        )
        session.add(copied_cabinet)
        session.flush()

        # Copy parts using the service
        for part in original_parts:
            project_service.add_part_to_cabinet(
                cabinet_id=copied_cabinet.id,
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

        session.commit()

        # THEN: Copied cabinet should have same parts
        session.refresh(copied_cabinet)
        assert len(copied_cabinet.parts) == original_count

        # Verify part details match
        original_names = sorted([p.part_name for p in original_parts])
        copied_names = sorted([p.part_name for p in copied_cabinet.parts])
        assert original_names == copied_names

    def test_removing_part_does_not_affect_other_parts(
        self, session, project_service, custom_cabinet_with_parts
    ):
        """Test that removing one part doesn't affect others"""
        # GIVEN: A cabinet with multiple parts
        initial_count = len(custom_cabinet_with_parts.parts)
        part_to_remove = custom_cabinet_with_parts.parts[0]
        part_id_to_remove = part_to_remove.id
        remaining_names = [
            p.part_name
            for p in custom_cabinet_with_parts.parts
            if p.id != part_id_to_remove
        ]

        # WHEN: Removing one part
        result = project_service.remove_part_from_cabinet(part_id_to_remove)

        # THEN: Removal should succeed
        assert result is True

        # AND: Other parts should remain
        session.refresh(custom_cabinet_with_parts)
        assert len(custom_cabinet_with_parts.parts) == initial_count - 1

        current_names = [p.part_name for p in custom_cabinet_with_parts.parts]
        for name in remaining_names:
            assert name in current_names

    def test_updating_part_does_not_affect_other_parts(
        self, session, project_service, custom_cabinet_with_parts
    ):
        """Test that updating one part doesn't affect others"""
        # GIVEN: A cabinet with multiple parts
        parts = list(custom_cabinet_with_parts.parts)
        part_to_update = parts[0]
        other_parts_data = [
            (p.id, p.part_name, p.width_mm, p.height_mm)
            for p in parts
            if p.id != part_to_update.id
        ]

        # WHEN: Updating one part
        project_service.update_part(
            part_id=part_to_update.id,
            part_data={
                "part_name": "Updated Part Name",
                "width_mm": 999,
            },
        )

        # THEN: Other parts should remain unchanged
        session.refresh(custom_cabinet_with_parts)
        for part_id, name, width, height in other_parts_data:
            part = session.get(ProjectCabinetPart, part_id)
            assert part.part_name == name
            assert part.width_mm == width
            assert part.height_mm == height

    def test_parts_and_accessories_coexist(
        self, session, project_service, test_project, template_service
    ):
        """Test that parts and accessories can coexist on same cabinet"""
        # GIVEN: A cabinet with both parts and accessories
        template = template_service.create_template(
            name="MixedCabinet",
            kitchen_type="MODERN",
        )

        cabinet = ProjectCabinet(
            project_id=test_project.id,
            type_id=template.id,
            sequence_number=1,
            quantity=1,
            body_color="#ffffff",
            front_color="#000000",
            handle_type="Standard",
        )
        session.add(cabinet)
        session.flush()

        # Add parts
        for i in range(3):
            project_service.add_part_to_cabinet(
                cabinet_id=cabinet.id,
                part_name=f"Part {i+1}",
                width_mm=500 + i * 10,
                height_mm=400 + i * 10,
            )

        # Add accessories
        for i in range(2):
            project_service.add_accessory_to_cabinet(
                cabinet_id=cabinet.id,
                name=f"Accessory {i+1}",
                sku=f"ACC-{i+1:03d}",
                count=i + 1,
            )

        session.commit()

        # THEN: Cabinet should have both parts and accessories
        session.refresh(cabinet)
        assert len(cabinet.parts) == 3
        assert len(cabinet.accessory_snapshots) == 2

        # Verify they are separate and independent
        part_names = [p.part_name for p in cabinet.parts]
        accessory_names = [a.name for a in cabinet.accessory_snapshots]

        assert "Part 1" in part_names
        assert "Accessory 1" in accessory_names

    def test_deleting_cabinet_removes_all_parts(
        self, session, project_service, custom_cabinet_with_parts
    ):
        """Test that deleting a cabinet removes all its parts"""
        # GIVEN: A cabinet with parts
        cabinet_id = custom_cabinet_with_parts.id
        part_ids = [p.id for p in custom_cabinet_with_parts.parts]
        assert len(part_ids) > 0

        # WHEN: Deleting the cabinet
        project_service.delete_cabinet(cabinet_id)

        # THEN: All parts should be deleted (cascade)
        for part_id in part_ids:
            part = session.get(ProjectCabinetPart, part_id)
            assert part is None

    def test_parts_survive_quantity_change(
        self, session, project_service, custom_cabinet_with_parts
    ):
        """Test that parts remain when cabinet quantity is changed"""
        # GIVEN: A cabinet with parts
        original_parts = [(p.id, p.part_name) for p in custom_cabinet_with_parts.parts]

        # WHEN: Changing the cabinet quantity
        custom_cabinet_with_parts.quantity = 5
        session.commit()

        # THEN: Parts should remain unchanged
        session.refresh(custom_cabinet_with_parts)
        current_parts = [(p.id, p.part_name) for p in custom_cabinet_with_parts.parts]
        assert original_parts == current_parts

    def test_add_edit_remove_sequence(
        self, session, project_service, custom_cabinet_with_parts
    ):
        """Test a sequence of add, edit, and remove operations"""
        # GIVEN: A cabinet with initial parts
        initial_count = len(custom_cabinet_with_parts.parts)

        # Step 1: Add a new part
        project_service.add_part_to_cabinet(
            cabinet_id=custom_cabinet_with_parts.id,
            part_name="New Shelf",
            width_mm=570,
            height_mm=280,
            pieces=2,
        )
        session.refresh(custom_cabinet_with_parts)
        assert len(custom_cabinet_with_parts.parts) == initial_count + 1

        new_part = next(
            p for p in custom_cabinet_with_parts.parts if p.part_name == "New Shelf"
        )

        # Step 2: Edit the new part
        project_service.update_part(
            part_id=new_part.id,
            part_data={"pieces": 3, "comments": "Extra shelf"},
        )
        session.refresh(new_part)
        assert new_part.pieces == 3
        assert new_part.comments == "Extra shelf"

        # Step 3: Remove an existing part
        part_to_remove = next(
            p for p in custom_cabinet_with_parts.parts if p.part_name == "Bok prawy"
        )
        project_service.remove_part_from_cabinet(part_to_remove.id)
        session.refresh(custom_cabinet_with_parts)
        assert len(custom_cabinet_with_parts.parts) == initial_count  # back to original

        # Verify final state
        part_names = [p.part_name for p in custom_cabinet_with_parts.parts]
        assert "New Shelf" in part_names
        assert "Bok prawy" not in part_names


class TestPartsWithCatalogTemplates:
    """Test parts integration with catalog templates"""

    @pytest.fixture
    def template_with_parts(self, session, template_service):
        """Create a template with predefined parts"""
        template = template_service.create_template(
            name="CatalogTemplate",
            kitchen_type="MODERN",
        )

        parts = [
            ("Bok prawy", 560, 702),
            ("Bok lewy", 560, 702),
            ("Wieniec górny", 564, 560),
            ("Wieniec dolny", 564, 560),
            ("Plecy HDF", 596, 716),
        ]

        for name, width, height in parts:
            template_service.add_part(
                cabinet_type_id=template.id,
                part_name=name,
                width_mm=width,
                height_mm=height,
                pieces=1,
                material="PLYTA" if "Plecy" not in name else "HDF",
                thickness_mm=18 if "Plecy" not in name else 3,
            )

        session.refresh(template)
        return template

    def test_template_parts_exist(self, session, template_with_parts):
        """Test that template has parts"""
        assert len(template_with_parts.parts) == 5

    def test_adding_part_to_template(self, session, template_service, template_with_parts):
        """Test adding a part to catalog template"""
        # GIVEN: A template with parts
        initial_count = len(template_with_parts.parts)

        # WHEN: Adding a new part
        result = template_service.add_part(
            cabinet_type_id=template_with_parts.id,
            part_name="Półka stała",
            width_mm=564,
            height_mm=540,
            pieces=1,
            material="PLYTA",
            thickness_mm=18,
        )

        # THEN: Part should be added
        assert result is not None
        session.refresh(template_with_parts)
        assert len(template_with_parts.parts) == initial_count + 1

    def test_deleting_template_part(self, session, template_service, template_with_parts):
        """Test deleting a part from catalog template"""
        # GIVEN: A template with parts
        initial_count = len(template_with_parts.parts)
        part = template_with_parts.parts[0]
        part_id = part.id

        # WHEN: Deleting the part
        result = template_service.delete_part(part_id)

        # THEN: Part should be deleted
        assert result is True
        session.refresh(template_with_parts)
        assert len(template_with_parts.parts) == initial_count - 1
