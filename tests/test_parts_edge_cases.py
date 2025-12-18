"""
Comprehensive edge case tests for parts functionality.
Tests all boundary conditions, error cases, and exceptional scenarios.
"""

import pytest

from src.db_schema.orm_models import (
    ProjectCabinet,
)


class TestPartsEdgeCases:
    """Test all edge cases for parts operations"""

    @pytest.fixture
    def test_project(self, session, project_service):
        """Create a test project"""
        return project_service.create_project(
            name="Edge Case Project",
            order_number="EDGE-001",
        )

    @pytest.fixture
    def test_cabinet(self, session, project_service, test_project, template_service):
        """Create a test cabinet for edge case testing"""
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

    # ============================================================
    # Invalid Cabinet ID Tests
    # ============================================================

    def test_add_part_invalid_cabinet_id(self, session, project_service):
        """Test adding part to non-existent cabinet"""
        # GIVEN: A non-existent cabinet ID
        invalid_cabinet_id = 99999

        # WHEN: Attempting to add part to invalid cabinet
        result = project_service.add_part_to_cabinet(
            cabinet_id=invalid_cabinet_id,
            part_name="Test Part",
            width_mm=500,
            height_mm=400,
        )

        # THEN: Operation should fail
        assert result is False

    def test_add_part_negative_cabinet_id(self, session, project_service):
        """Test adding part with negative cabinet ID"""
        # WHEN: Adding part with negative cabinet ID
        result = project_service.add_part_to_cabinet(
            cabinet_id=-1,
            part_name="Test Part",
            width_mm=500,
            height_mm=400,
        )

        # THEN: Should fail
        assert result is False

    # ============================================================
    # Part Name Edge Cases
    # ============================================================

    def test_add_part_empty_name(self, session, project_service, test_cabinet):
        """Test adding part with empty name"""
        # WHEN: Adding part with empty name
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="",
            width_mm=500,
            height_mm=400,
        )

        # THEN: Should fail (name is required)
        assert result is False
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 0

    def test_add_part_none_name(self, session, project_service, test_cabinet):
        """Test adding part with None name"""
        # WHEN: Adding part with None name
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name=None,
            width_mm=500,
            height_mm=400,
        )

        # THEN: Should fail
        assert result is False
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 0

    def test_add_part_very_long_name(self, session, project_service, test_cabinet):
        """Test adding part with very long name"""
        # WHEN: Adding part with very long name
        long_name = "A" * 1000

        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name=long_name,
            width_mm=500,
            height_mm=400,
        )

        # THEN: Should handle appropriately (may truncate or fail)
        if result:
            session.refresh(test_cabinet)
            assert len(test_cabinet.parts) == 1

    def test_add_part_unicode_name(self, session, project_service, test_cabinet):
        """Test adding part with Unicode characters in name"""
        # WHEN: Adding part with Unicode characters
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Półka żółwik™ 中文 ñiño ß",
            width_mm=500,
            height_mm=400,
        )

        # THEN: Should handle Unicode correctly
        assert result is True
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 1
        assert "żółwik" in test_cabinet.parts[0].part_name
        assert "中文" in test_cabinet.parts[0].part_name

    def test_add_part_special_characters_name(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with special characters in name"""
        # WHEN: Adding part with special characters
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Part <>&\"' / \\ @ #",
            width_mm=500,
            height_mm=400,
        )

        # THEN: Should handle special characters
        assert result is True
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 1

    def test_add_part_whitespace_only_name(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with whitespace-only name"""
        # WHEN: Adding part with whitespace name
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="   ",
            width_mm=500,
            height_mm=400,
        )

        # THEN: Behavior depends on implementation - could be allowed or rejected
        # Just verify no crash
        session.refresh(test_cabinet)

    # ============================================================
    # Dimension Edge Cases
    # ============================================================

    def test_add_part_zero_dimensions(self, session, project_service, test_cabinet):
        """Test adding part with zero dimensions"""
        # WHEN: Adding part with zero dimensions
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Zero Part",
            width_mm=0,
            height_mm=0,
        )

        # THEN: Implementation may allow or reject - just verify no crash
        session.refresh(test_cabinet)

    def test_add_part_negative_dimensions(self, session, project_service, test_cabinet):
        """Test adding part with negative dimensions"""
        # WHEN: Adding part with negative dimensions
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Negative Part",
            width_mm=-500,
            height_mm=-400,
        )

        # THEN: Implementation may allow or reject
        session.refresh(test_cabinet)

    def test_add_part_very_large_dimensions(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with very large dimensions"""
        # WHEN: Adding part with very large dimensions
        large_value = 2**30  # Very large but within int32

        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Large Part",
            width_mm=large_value,
            height_mm=large_value,
        )

        # THEN: Should handle large numbers
        if result:
            session.refresh(test_cabinet)
            part = test_cabinet.parts[0]
            assert part.width_mm == large_value
            assert part.height_mm == large_value

    # ============================================================
    # Pieces Count Edge Cases
    # ============================================================

    def test_add_part_zero_pieces(self, session, project_service, test_cabinet):
        """Test adding part with zero pieces"""
        # WHEN: Adding part with zero pieces
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Zero Pieces Part",
            width_mm=500,
            height_mm=400,
            pieces=0,
        )

        # THEN: Should handle zero pieces
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].pieces == 0

    def test_add_part_negative_pieces(self, session, project_service, test_cabinet):
        """Test adding part with negative pieces"""
        # WHEN: Adding part with negative pieces
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Negative Pieces Part",
            width_mm=500,
            height_mm=400,
            pieces=-1,
        )

        # THEN: Implementation should handle
        session.refresh(test_cabinet)

    def test_add_part_very_large_pieces_count(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with very large pieces count"""
        # WHEN: Adding part with very large pieces count
        large_count = 2**20

        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Many Pieces Part",
            width_mm=500,
            height_mm=400,
            pieces=large_count,
        )

        # THEN: Should handle large count
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].pieces == large_count

    # ============================================================
    # Update Part Edge Cases
    # ============================================================

    def test_update_nonexistent_part(self, session, project_service):
        """Test updating a non-existent part"""
        # WHEN: Updating non-existent part
        result = project_service.update_part(
            part_id=99999,
            part_data={"part_name": "Updated Name"},
        )

        # THEN: Should fail gracefully
        assert result is False

    def test_update_part_with_empty_data(self, session, project_service, test_cabinet):
        """Test updating part with empty data dict"""
        # GIVEN: A part exists
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Original Name",
            width_mm=500,
            height_mm=400,
        )
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]

        # WHEN: Updating with empty data
        result = project_service.update_part(
            part_id=part.id,
            part_data={},
        )

        # THEN: Should succeed but change nothing
        assert result is True
        session.refresh(part)
        assert part.part_name == "Original Name"

    def test_update_part_with_invalid_fields(
        self, session, project_service, test_cabinet
    ):
        """Test updating part with non-existent field names"""
        # GIVEN: A part exists
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Original Name",
            width_mm=500,
            height_mm=400,
        )
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]

        # WHEN: Updating with invalid field names
        result = project_service.update_part(
            part_id=part.id,
            part_data={
                "nonexistent_field": "value",
                "another_invalid": 123,
            },
        )

        # THEN: Should succeed but ignore invalid fields
        assert result is True
        session.refresh(part)
        assert part.part_name == "Original Name"

    def test_update_part_name_to_empty(self, session, project_service, test_cabinet):
        """Test updating part name to empty string"""
        # GIVEN: A part exists
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Original Name",
            width_mm=500,
            height_mm=400,
        )
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]

        # WHEN: Updating name to empty
        project_service.update_part(
            part_id=part.id,
            part_data={"part_name": ""},
        )

        # THEN: Depends on implementation validation
        session.refresh(part)

    # ============================================================
    # Remove Part Edge Cases
    # ============================================================

    def test_remove_nonexistent_part(self, session, project_service):
        """Test removing a non-existent part"""
        # WHEN: Removing non-existent part
        result = project_service.remove_part_from_cabinet(99999)

        # THEN: Should fail gracefully
        assert result is False

    def test_remove_part_negative_id(self, session, project_service):
        """Test removing part with negative ID"""
        # WHEN: Removing with negative ID
        result = project_service.remove_part_from_cabinet(-1)

        # THEN: Should fail
        assert result is False

    def test_remove_same_part_twice(self, session, project_service, test_cabinet):
        """Test removing the same part twice"""
        # GIVEN: A part exists
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Part To Remove",
            width_mm=500,
            height_mm=400,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id

        # WHEN: Removing twice
        result1 = project_service.remove_part_from_cabinet(part_id)
        result2 = project_service.remove_part_from_cabinet(part_id)

        # THEN: First succeeds, second fails
        assert result1 is True
        assert result2 is False

    # ============================================================
    # Duplicate Parts Edge Cases
    # ============================================================

    def test_add_duplicate_part_names(self, session, project_service, test_cabinet):
        """Test adding multiple parts with same name"""
        # WHEN: Adding parts with same name
        result1 = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Duplicate Part",
            width_mm=500,
            height_mm=400,
        )
        result2 = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Duplicate Part",
            width_mm=600,
            height_mm=300,
        )

        # THEN: Both should succeed (duplicates allowed by design)
        assert result1 is True
        assert result2 is True

        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 2

        # Both have same name but different dimensions
        names = [p.part_name for p in test_cabinet.parts]
        assert names.count("Duplicate Part") == 2

    def test_add_parts_with_same_dimensions(
        self, session, project_service, test_cabinet
    ):
        """Test adding parts with identical dimensions but different names"""
        # WHEN: Adding parts with same dimensions
        parts = [
            ("Part A", 500, 400),
            ("Part B", 500, 400),
            ("Part C", 500, 400),
        ]

        for name, w, h in parts:
            result = project_service.add_part_to_cabinet(
                cabinet_id=test_cabinet.id,
                part_name=name,
                width_mm=w,
                height_mm=h,
            )
            assert result is True

        # THEN: All parts should exist
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 3

    # ============================================================
    # Material and Thickness Edge Cases
    # ============================================================

    def test_add_part_with_null_material(self, session, project_service, test_cabinet):
        """Test adding part with null material"""
        # WHEN: Adding part with None material
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="No Material Part",
            width_mm=500,
            height_mm=400,
            material=None,
        )

        # THEN: Should succeed
        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material is None

    def test_add_part_with_zero_thickness(self, session, project_service, test_cabinet):
        """Test adding part with zero thickness"""
        # WHEN: Adding part with zero thickness
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Zero Thickness Part",
            width_mm=500,
            height_mm=400,
            thickness_mm=0,
        )

        # THEN: Should handle
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].thickness_mm == 0

    def test_add_part_with_negative_thickness(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with negative thickness"""
        # WHEN: Adding part with negative thickness
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Negative Thickness Part",
            width_mm=500,
            height_mm=400,
            thickness_mm=-18,
        )

        # THEN: Implementation should handle
        session.refresh(test_cabinet)

    # ============================================================
    # Comments Edge Cases
    # ============================================================

    def test_add_part_with_very_long_comments(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with very long comments"""
        # WHEN: Adding part with very long comments
        long_comments = "X" * 5000

        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Long Comments Part",
            width_mm=500,
            height_mm=400,
            comments=long_comments,
        )

        # THEN: Should handle appropriately
        if result:
            session.refresh(test_cabinet)
            assert len(test_cabinet.parts[0].comments) > 0

    def test_add_part_with_unicode_comments(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with Unicode comments"""
        # WHEN: Adding part with Unicode comments
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Unicode Comments Part",
            width_mm=500,
            height_mm=400,
            comments="Komentarz: żółć 日本語 العربية 🎉",
        )

        # THEN: Should handle Unicode
        assert result is True
        session.refresh(test_cabinet)
        assert "żółć" in test_cabinet.parts[0].comments
        assert "日本語" in test_cabinet.parts[0].comments

    # ============================================================
    # Concurrent Operations Edge Cases
    # ============================================================

    def test_sequential_updates_on_same_part(
        self, session, project_service, test_cabinet
    ):
        """Test multiple sequential updates on same part"""
        # GIVEN: A part exists
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Sequential Part",
            width_mm=500,
            height_mm=400,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id

        # WHEN: Performing multiple sequential updates
        for i in range(10):
            result = project_service.update_part(
                part_id=part_id,
                part_data={"width_mm": 500 + i},
            )
            assert result is True

        # THEN: Last update should persist
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].width_mm == 509

    def test_rapid_add_remove_cycle(self, session, project_service, test_cabinet):
        """Test rapid add/remove cycles"""
        # WHEN: Rapidly adding and removing parts
        for i in range(20):
            result = project_service.add_part_to_cabinet(
                cabinet_id=test_cabinet.id,
                part_name=f"Cycle Part {i}",
                width_mm=500,
                height_mm=400,
            )
            assert result is True

            session.refresh(test_cabinet)
            part_id = test_cabinet.parts[-1].id

            result = project_service.remove_part_from_cabinet(part_id)
            assert result is True

        # THEN: Cabinet should have no parts
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts) == 0


class TestPartsSourceTracking:
    """Test source tracking for parts (template/part references)"""

    @pytest.fixture
    def test_project(self, session, project_service):
        return project_service.create_project(
            name="Source Tracking Project",
            order_number="SRC-001",
        )

    @pytest.fixture
    def test_cabinet(self, session, project_service, test_project, template_service):
        template = template_service.create_template(
            name="SourceTemplate",
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

    def test_add_part_with_source_template_id(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with source template reference"""
        # WHEN: Adding part with source template ID
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Sourced Part",
            width_mm=500,
            height_mm=400,
            source_template_id=123,
        )

        # THEN: Source should be tracked
        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].source_template_id == 123

    def test_add_part_with_source_part_id(self, session, project_service, test_cabinet):
        """Test adding part with source part reference"""
        # WHEN: Adding part with source part ID
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Sourced Part",
            width_mm=500,
            height_mm=400,
            source_part_id=456,
        )

        # THEN: Source should be tracked
        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].source_part_id == 456

    def test_add_part_with_both_source_references(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with both source references"""
        # WHEN: Adding part with both source references
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Full Source Part",
            width_mm=500,
            height_mm=400,
            source_template_id=123,
            source_part_id=456,
        )

        # THEN: Both sources should be tracked
        assert result is True
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]
        assert part.source_template_id == 123
        assert part.source_part_id == 456

    def test_source_references_preserved_on_update(
        self, session, project_service, test_cabinet
    ):
        """Test that source references are preserved when updating other fields"""
        # GIVEN: A part with source references
        project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Source Part",
            width_mm=500,
            height_mm=400,
            source_template_id=123,
            source_part_id=456,
        )
        session.refresh(test_cabinet)
        part_id = test_cabinet.parts[0].id

        # WHEN: Updating other fields
        project_service.update_part(
            part_id=part_id,
            part_data={"width_mm": 600, "comments": "Updated"},
        )

        # THEN: Source references should remain
        session.refresh(test_cabinet)
        part = test_cabinet.parts[0]
        assert part.source_template_id == 123
        assert part.source_part_id == 456
        assert part.width_mm == 600
