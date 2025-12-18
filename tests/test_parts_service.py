"""
Unit tests for parts service functionality in ProjectService.
Tests basic CRUD operations for cabinet parts.
"""

import pytest

from src.db_schema.orm_models import (
    ProjectCabinetPart,
    ProjectCabinet,
)


class TestPartsServiceCRUD:
    """Test basic CRUD operations for cabinet parts"""

    @pytest.fixture
    def test_project(self, session, project_service):
        """Create a test project"""
        return project_service.create_project(
            name="Parts Test Project",
            order_number="PARTS-001",
        )

    @pytest.fixture
    def test_cabinet(self, session, project_service, test_project, template_service):
        """Create a test cabinet for parts operations"""
        template = template_service.create_template(
            name="TestCabinetTemplate",
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
        session.commit()
        return cabinet

    def test_add_part_to_cabinet_success(self, session, project_service, test_cabinet):
        """Test successfully adding a part to a cabinet"""
        # WHEN: Adding a valid part
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Bok prawy",
            width_mm=560,
            height_mm=720,
            pieces=1,
            material="PLYTA 18",
            wrapping="NO",
            comments="Test part",
        )

        # THEN: Operation should succeed
        assert result is True

        # AND: Part should be in the cabinet
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 1

        part = test_cabinet.parts[0]
        assert part.part_name == "Bok prawy"
        assert part.width_mm == 560
        assert part.height_mm == 720
        assert part.pieces == 1
        assert part.material == "PLYTA 18"
        assert part.wrapping == "NO"
        assert part.comments == "Test part"

    def test_add_part_to_cabinet_minimal_fields(
        self, session, project_service, test_cabinet
    ):
        """Test adding a part with only required fields"""
        # WHEN: Adding part with minimal required fields
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Półka",
            width_mm=580,
            height_mm=300,
        )

        # THEN: Operation should succeed
        assert result is True

        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 1

        part = test_cabinet.parts[0]
        assert part.part_name == "Półka"
        assert part.width_mm == 580
        assert part.height_mm == 300
        assert part.pieces == 1  # Default value

    def test_add_multiple_parts_to_cabinet(
        self, session, project_service, test_cabinet
    ):
        """Test adding multiple parts to a cabinet"""
        # WHEN: Adding multiple parts
        parts_data = [
            {"part_name": "Bok prawy", "width_mm": 560, "height_mm": 720},
            {"part_name": "Bok lewy", "width_mm": 560, "height_mm": 720},
            {"part_name": "Wieniec górny", "width_mm": 564, "height_mm": 560},
            {"part_name": "Wieniec dolny", "width_mm": 564, "height_mm": 560},
            {"part_name": "Plecy", "width_mm": 600, "height_mm": 720},
        ]

        for part in parts_data:
            result = project_service.add_part_to_cabinet(
                cabinet_id=test_cabinet.id, **part
            )
            assert result is True

        # THEN: All parts should be in the cabinet
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 5

        part_names = [p.part_name for p in test_cabinet.parts]
        assert "Bok prawy" in part_names
        assert "Bok lewy" in part_names
        assert "Wieniec górny" in part_names
        assert "Wieniec dolny" in part_names
        assert "Plecy" in part_names

    def test_update_part_success(self, session, project_service, test_cabinet):
        """Test successfully updating a part"""
        # GIVEN: A part exists
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Półka",
            width_mm=580,
            height_mm=300,
            pieces=2,
        )
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]
        original_id = part.id

        # WHEN: Updating the part
        result = project_service.update_part(
            part_id=part.id,
            part_data={
                "part_name": "Półka ruchoma",
                "width_mm": 570,
                "height_mm": 290,
                "pieces": 3,
                "material": "PLYTA",
                "comments": "Updated shelf",
            },
        )

        # THEN: Update should succeed
        assert result is True

        # AND: Part should be updated
        session.refresh(test_cabinet)
        updated_part = test_cabinet.parts[0]
        assert updated_part.id == original_id
        assert updated_part.part_name == "Półka ruchoma"
        assert updated_part.width_mm == 570
        assert updated_part.height_mm == 290
        assert updated_part.pieces == 3
        assert updated_part.material == "PLYTA"
        assert updated_part.comments == "Updated shelf"

    def test_remove_part_from_cabinet_success(
        self, session, project_service, test_cabinet
    ):
        """Test successfully removing a part from a cabinet"""
        # GIVEN: A part exists
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Półka do usunięcia",
            width_mm=580,
            height_mm=300,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id

        # WHEN: Removing the part
        result = project_service.remove_part_from_cabinet(part_id)

        # THEN: Removal should succeed
        assert result is True

        # AND: Part should no longer exist
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 0

    def test_remove_part_second_time_fails(
        self, session, project_service, test_cabinet
    ):
        """Test removing a part that was already removed"""
        # GIVEN: A part that was added and removed
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Part",
            width_mm=100,
            height_mm=100,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id

        project_service.remove_part_from_cabinet(part_id)

        # WHEN: Trying to remove again
        result = project_service.remove_part_from_cabinet(part_id)

        # THEN: Second removal should fail
        assert result is False

    def test_get_part_after_adding(self, session, project_service, test_cabinet):
        """Test that added part can be retrieved"""
        # GIVEN: A part was added
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Test Part",
            width_mm=500,
            height_mm=400,
            pieces=2,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id

        # WHEN: Retrieving the part directly
        part = session.get(ProjectCabinetPart, part_id)

        # THEN: Part should be correctly retrieved
        assert part is not None
        assert part.part_name == "Test Part"
        assert part.width_mm == 500
        assert part.height_mm == 400
        assert part.pieces == 2

    def test_part_has_correct_cabinet_reference(
        self, session, project_service, test_cabinet
    ):
        """Test that part correctly references its parent cabinet"""
        # GIVEN: A part was added
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Test Part",
            width_mm=500,
            height_mm=400,
        )
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]

        # THEN: Part should reference correct cabinet
        assert part.project_cabinet_id == test_cabinet.id
        assert part.project_cabinet is not None
        assert part.project_cabinet.id == test_cabinet.id

    def test_cabinet_updated_at_changes_on_part_add(
        self, session, project_service, test_cabinet
    ):
        """Test that cabinet's updated_at timestamp changes when adding part"""
        # GIVEN: Cabinet with known updated_at
        original_updated_at = test_cabinet.updated_at

        # WHEN: Adding a part
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="New Part",
            width_mm=300,
            height_mm=200,
        )

        # THEN: Cabinet's updated_at should change
        session.refresh(test_cabinet)
        assert test_cabinet.updated_at >= original_updated_at

    def test_cabinet_updated_at_changes_on_part_update(
        self, session, project_service, test_cabinet
    ):
        """Test that cabinet's updated_at timestamp changes when updating part"""
        # GIVEN: Cabinet with a part
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Part",
            width_mm=300,
            height_mm=200,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id
        original_updated_at = test_cabinet.updated_at

        # WHEN: Updating the part
        project_service.update_part(
            part_id=part_id,
            part_data={"width_mm": 350},
        )

        # THEN: Cabinet's updated_at should change
        session.refresh(test_cabinet)
        assert test_cabinet.updated_at >= original_updated_at

    def test_cabinet_updated_at_changes_on_part_remove(
        self, session, project_service, test_cabinet
    ):
        """Test that cabinet's updated_at timestamp changes when removing part"""
        # GIVEN: Cabinet with a part
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Part",
            width_mm=300,
            height_mm=200,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id
        original_updated_at = test_cabinet.updated_at

        # WHEN: Removing the part
        project_service.remove_part_from_cabinet(part_id)

        # THEN: Cabinet's updated_at should change
        session.refresh(test_cabinet)
        assert test_cabinet.updated_at >= original_updated_at


# ==============================================================================
# Edge Cases Tests
# ==============================================================================


class TestPartsEdgeCases:
    """Test edge cases for parts operations"""

    @pytest.fixture
    def test_project(self, session, project_service):
        """Create a test project for edge case tests"""
        return project_service.create_project(
            name="Edge Case Project",
            order_number="EDGE-001",
        )

    @pytest.fixture
    def test_cabinet(self, session, project_service, test_project, template_service):
        """Create a test cabinet for edge case tests"""
        template = template_service.create_template(
            name="EdgeCaseTemplate",
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
        session.commit()
        return cabinet

    def test_cabinet_without_parts(self, session, project_service, test_cabinet):
        """Test that a cabinet with no parts works correctly"""
        # GIVEN: A cabinet with no parts
        session.refresh(test_cabinet)

        # THEN: Cabinet should have empty parts list
        assert test_cabinet.parts == []

        # AND: Getting parts should return empty list
        parts = (
            session.query(ProjectCabinetPart)
            .filter_by(project_cabinet_id=test_cabinet.id)
            .all()
        )
        assert parts == []

    def test_part_with_unicode_polish_name(
        self, session, project_service, test_cabinet
    ):
        """Test part with Polish characters in name"""
        # GIVEN: Polish characters
        polish_name = "Półka górna żółta"

        # WHEN: Adding part with Polish name
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name=polish_name,
            width_mm=400,
            height_mm=300,
            comments="Ścięty róg, łączenie ćwierćwalca",
        )

        # THEN: Polish characters should be preserved
        assert result is True
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]
        assert part.part_name == polish_name
        assert "Ścięty" in part.comments
        assert "ćwierćwalca" in part.comments

    def test_part_with_emoji_name(self, session, project_service, test_cabinet):
        """Test part with emoji in name"""
        # GIVEN: Emoji in part name
        emoji_name = "Front 🚪 główny"

        # WHEN: Adding part with emoji
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name=emoji_name,
            width_mm=400,
            height_mm=700,
            comments="Super ✨ jakość",
        )

        # THEN: Emoji should be preserved
        assert result is True
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]
        assert "🚪" in part.part_name
        assert "✨" in part.comments

    def test_part_with_very_long_comments(self, session, project_service, test_cabinet):
        """Test part with very long comments (5000+ chars)"""
        # GIVEN: Very long comments
        long_comment = "Opis " + "X" * 5000 + " koniec"

        # WHEN: Adding part with long comments
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Część z długim opisem",
            width_mm=300,
            height_mm=200,
            comments=long_comment,
        )

        # THEN: Comments should be preserved
        assert result is True
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]
        assert len(part.comments) > 5000
        assert part.comments.startswith("Opis ")
        assert part.comments.endswith(" koniec")

    def test_cabinet_with_many_parts(self, session, project_service, test_cabinet):
        """Test cabinet with large number of parts (50+)"""
        # GIVEN: Adding 50 parts to a cabinet
        num_parts = 50
        for i in range(1, num_parts + 1):
            project_service.add_part_to_cabinet(
                cabinet_id=test_cabinet.id,
                part_name=f"Część nr {i}",
                width_mm=100 + i,
                height_mm=200 + i,
                pieces=1,
            )

        # THEN: All parts should be added
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == num_parts

        # AND: Each part should have correct data
        for idx, part in enumerate(sorted(test_cabinet.parts, key=lambda p: p.id)):
            expected_width = 100 + (idx + 1)
            assert part.width_mm == expected_width

    def test_part_with_special_characters_in_wrapping(
        self, session, project_service, test_cabinet
    ):
        """Test part with special characters in wrapping field"""
        # GIVEN: Special characters
        special_wrapping = "2x ABS 0.8mm / 2x PCV 1.5mm"

        # WHEN: Adding part
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Blat",
            width_mm=600,
            height_mm=40,
            wrapping=special_wrapping,
        )

        # THEN: Special characters preserved
        assert result is True
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]
        assert part.wrapping == special_wrapping
