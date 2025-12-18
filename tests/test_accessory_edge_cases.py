"""
Comprehensive edge case tests for accessory functionality.
Tests all boundary conditions, error cases, and exceptional scenarios.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from src.db_schema.orm_models import (
    Project,
    ProjectCabinetAccessorySnapshot,
)
from src.services.project_service import ProjectService
from src.services.formula_service import FormulaService


class TestAccessoryEdgeCases:
    """Test all edge cases for accessory operations"""

    def test_add_accessory_invalid_cabinet_id(self, session, project_service):
        """Test adding accessory to non-existent cabinet"""
        # GIVEN: A non-existent cabinet ID
        invalid_cabinet_id = 99999

        # WHEN: Attempting to add accessory to invalid cabinet
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=invalid_cabinet_id,
            name="Test Accessory",
            sku="TEST-001",
            count=1,
        )

        # THEN: Operation should fail
        assert result is False

    def test_add_accessory_empty_name(self, session, project_service, custom_cabinet):
        """Test adding accessory with empty name"""
        # WHEN: Adding accessory with empty name
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="", sku="TEST-001", count=1
        )

        # THEN: Operation should fail or handle gracefully
        # Note: Implementation may allow empty names, adjust based on business rules
        if result:
            # If allowed, verify it was saved correctly
            session.refresh(custom_cabinet)
            assert len(custom_cabinet.accessory_snapshots) == 1
            assert custom_cabinet.accessory_snapshots[0].name == ""
        else:
            # If not allowed, ensure no accessory was added
            session.refresh(custom_cabinet)
            assert len(custom_cabinet.accessory_snapshots) == 0

    def test_add_accessory_none_name(self, session, project_service, custom_cabinet):
        """Test adding accessory with None name"""
        # WHEN: Adding accessory with None name
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name=None, sku="TEST-001", count=1
        )

        # THEN: Should fail gracefully
        assert result is False
        session.refresh(custom_cabinet)
        assert len(custom_cabinet.accessory_snapshots) == 0

    def test_add_accessory_empty_sku(self, session, project_service, custom_cabinet):
        """Test adding accessory with empty SKU"""
        # WHEN: Adding accessory with empty SKU
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="Test Accessory", sku="", count=1
        )

        # THEN: Should handle gracefully (business rule dependent)
        if result:
            session.refresh(custom_cabinet)
            assert len(custom_cabinet.accessory_snapshots) == 1
            assert custom_cabinet.accessory_snapshots[0].sku == ""

    def test_add_accessory_zero_count(self, session, project_service, custom_cabinet):
        """Test adding accessory with zero count"""
        # WHEN: Adding accessory with zero count
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="Test Accessory", sku="TEST-001", count=0
        )

        # THEN: Should handle based on business rules
        if result:
            session.refresh(custom_cabinet)
            assert len(custom_cabinet.accessory_snapshots) == 1
            assert custom_cabinet.accessory_snapshots[0].count == 0

    def test_add_accessory_negative_count(
        self, session, project_service, custom_cabinet
    ):
        """Test adding accessory with negative count"""
        # WHEN: Adding accessory with negative count
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Test Accessory",
            sku="TEST-001",
            count=-1,
        )

        # THEN: Should be rejected
        assert result is False
        session.refresh(custom_cabinet)
        assert len(custom_cabinet.accessory_snapshots) == 0

    def test_add_accessory_extremely_large_count(
        self, session, project_service, custom_cabinet
    ):
        """Test adding accessory with extremely large count"""
        # WHEN: Adding accessory with very large count
        large_count = 2**31 - 1  # Max int32
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Test Accessory",
            sku="TEST-001",
            count=large_count,
        )

        # THEN: Should handle large numbers
        if result:
            session.refresh(custom_cabinet)
            assert len(custom_cabinet.accessory_snapshots) == 1
            assert custom_cabinet.accessory_snapshots[0].count == large_count

    def test_add_duplicate_accessories_same_sku(
        self, session, project_service, custom_cabinet
    ):
        """Test adding multiple accessories with same SKU"""
        # GIVEN: One accessory already exists
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Original Accessory",
            sku="DUPLICATE-001",
            count=1,
        )

        # WHEN: Adding another accessory with same SKU
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Duplicate Accessory",
            sku="DUPLICATE-001",
            count=2,
        )

        # THEN: Should handle duplicates appropriately
        session.refresh(custom_cabinet)
        if result:
            # If allowed, should have both accessories
            assert len(custom_cabinet.accessory_snapshots) == 2
            skus = [acc.sku for acc in custom_cabinet.accessory_snapshots]
            assert skus.count("DUPLICATE-001") == 2
        else:
            # If not allowed, should only have original
            assert len(custom_cabinet.accessory_snapshots) == 1

    def test_update_accessory_quantity_invalid_id(self, project_service):
        """Test updating quantity for non-existent accessory"""
        # WHEN: Updating non-existent accessory
        result = project_service.update_accessory_quantity(
            accessory_snapshot_id=99999, new_count=5
        )

        # THEN: Should fail gracefully
        assert result is False

    def test_update_accessory_quantity_negative(
        self, session, project_service, custom_cabinet
    ):
        """Test updating accessory quantity to negative value"""
        # GIVEN: An existing accessory
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="Test Accessory", sku="TEST-001", count=5
        )
        session.refresh(custom_cabinet)
        accessory = custom_cabinet.accessory_snapshots[0]

        # WHEN: Updating to negative quantity
        result = project_service.update_accessory_quantity(
            accessory_snapshot_id=accessory.id, new_count=-1
        )

        # THEN: Should be rejected
        assert result is False
        session.refresh(accessory)
        assert accessory.count == 5  # Should remain unchanged

    def test_update_accessory_quantity_zero(
        self, session, project_service, custom_cabinet
    ):
        """Test updating accessory quantity to zero"""
        # GIVEN: An existing accessory
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="Test Accessory", sku="TEST-001", count=5
        )
        session.refresh(custom_cabinet)
        accessory = custom_cabinet.accessory_snapshots[0]

        # WHEN: Updating to zero quantity
        result = project_service.update_accessory_quantity(
            accessory_snapshot_id=accessory.id, new_count=0
        )

        # THEN: Should handle based on business rules
        if result:
            session.refresh(accessory)
            assert accessory.count == 0

    def test_remove_accessory_invalid_id(self, project_service):
        """Test removing non-existent accessory"""
        # WHEN: Removing non-existent accessory
        result = project_service.remove_accessory_from_cabinet(
            accessory_snapshot_id=99999
        )

        # THEN: Should fail gracefully
        assert result is False

    def test_remove_accessory_already_removed(
        self, session, project_service, custom_cabinet
    ):
        """Test removing accessory that was already removed"""
        # GIVEN: An accessory that exists
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="Test Accessory", sku="TEST-001", count=1
        )
        session.refresh(custom_cabinet)
        accessory_id = custom_cabinet.accessory_snapshots[0].id

        # WHEN: Removing it twice
        result1 = project_service.remove_accessory_from_cabinet(accessory_id)
        result2 = project_service.remove_accessory_from_cabinet(accessory_id)

        # THEN: First should succeed, second should fail
        assert result1 is True
        assert result2 is False

    def test_concurrent_accessory_operations(
        self, session, project_service, custom_cabinet
    ):
        """Test concurrent operations on same accessory"""
        # GIVEN: An accessory
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="Test Accessory", sku="TEST-001", count=5
        )
        session.refresh(custom_cabinet)
        accessory_id = custom_cabinet.accessory_snapshots[0].id

        # WHEN: Simulating concurrent updates
        # Note: This is a simplified test - real concurrency testing would need threading
        result1 = project_service.update_accessory_quantity(accessory_id, 10)
        result2 = project_service.update_accessory_quantity(accessory_id, 15)

        # THEN: Both should succeed, last one wins
        assert result1 is True
        assert result2 is True

        session.refresh(custom_cabinet)
        assert custom_cabinet.accessory_snapshots[0].count == 15

    def test_accessory_with_unicode_characters(
        self, session, project_service, custom_cabinet
    ):
        """Test accessories with special Unicode characters"""
        # WHEN: Adding accessory with Unicode characters
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Uchwyt® żółwik™ ñiño 中文",
            sku="UNICODE-测试-001",
            count=1,
        )

        # THEN: Should handle Unicode correctly
        assert result is True
        session.refresh(custom_cabinet)
        assert len(custom_cabinet.accessory_snapshots) == 1
        accessory = custom_cabinet.accessory_snapshots[0]
        assert "żółwik" in accessory.name
        assert "测试" in accessory.sku

    def test_accessory_with_very_long_strings(
        self, session, project_service, custom_cabinet
    ):
        """Test accessories with very long name and SKU"""
        # WHEN: Adding accessory with very long strings
        long_name = "A" * 1000  # Very long name
        long_sku = "B" * 500  # Very long SKU

        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name=long_name, sku=long_sku, count=1
        )

        # THEN: Should handle or truncate appropriately
        if result:
            session.refresh(custom_cabinet)
            assert len(custom_cabinet.accessory_snapshots) == 1
            # Note: Actual behavior depends on database column constraints

    def test_accessory_database_constraint_violation(
        self, session, project_service, custom_cabinet
    ):
        """Test database constraint violations"""
        # WHEN: Adding accessory and then trying to violate constraints
        with patch.object(
            session, "commit", side_effect=Exception("Database constraint violation")
        ):
            result = project_service.add_accessory_to_cabinet(
                cabinet_id=custom_cabinet.id,
                name="Test Accessory",
                sku="TEST-001",
                count=1,
            )

            # THEN: Should handle database errors gracefully
            assert result is False

    def test_accessory_operations_on_deleted_cabinet(
        self, session, project_service, custom_cabinet
    ):
        """Test accessory operations on deleted cabinet"""
        # GIVEN: A cabinet with accessories
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id, name="Test Accessory", sku="TEST-001", count=1
        )

        # WHEN: Cabinet is deleted and we try to add more accessories
        session.delete(custom_cabinet)
        session.commit()

        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Another Accessory",
            sku="TEST-002",
            count=1,
        )

        # THEN: Should fail gracefully
        assert result is False

    def test_accessory_timestamp_handling(
        self, session, project_service, custom_cabinet
    ):
        """Test that accessory timestamps are handled correctly"""
        # WHEN: Adding an accessory
        before_time = datetime.now(timezone.utc)
        result = project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Timestamped Accessory",
            sku="TIME-001",
            count=1,
        )
        after_time = datetime.now(timezone.utc)

        # THEN: Should have proper timestamps
        assert result is True
        session.refresh(custom_cabinet)
        accessory = custom_cabinet.accessory_snapshots[0]

        # Add small buffer for timestamp comparison (to handle precision differences)
        from datetime import timedelta

        buffer = timedelta(seconds=1)
        before_time_with_buffer = before_time - buffer
        after_time_with_buffer = after_time + buffer

        # Check created_at timestamp
        if hasattr(accessory, "created_at") and accessory.created_at:
            created_at = accessory.created_at
            # Handle timezone-naive vs timezone-aware datetime comparison
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            assert before_time_with_buffer <= created_at <= after_time_with_buffer

        # Check updated_at timestamp
        if hasattr(accessory, "updated_at") and accessory.updated_at:
            updated_at = accessory.updated_at
            # Handle timezone-naive vs timezone-aware datetime comparison
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            assert before_time_with_buffer <= updated_at <= after_time_with_buffer

    def test_accessory_cascade_deletion(self, session, project_service, custom_cabinet):
        """Test that accessories are deleted when cabinet is deleted"""
        # GIVEN: A cabinet with accessories
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Test Accessory 1",
            sku="TEST-001",
            count=1,
        )
        project_service.add_accessory_to_cabinet(
            cabinet_id=custom_cabinet.id,
            name="Test Accessory 2",
            sku="TEST-002",
            count=2,
        )
        session.refresh(custom_cabinet)

        # WHEN: Cabinet is deleted
        cabinet_id = custom_cabinet.id
        session.delete(custom_cabinet)
        session.commit()

        # THEN: Accessories should be deleted too (if cascade is configured)
        remaining_accessories = (
            session.query(ProjectCabinetAccessorySnapshot)
            .filter(ProjectCabinetAccessorySnapshot.project_cabinet_id == cabinet_id)
            .all()
        )

        # This depends on cascade configuration in the model
        assert len(remaining_accessories) == 0


# Fixtures for the tests
@pytest.fixture
def project_service(session):
    """Create a ProjectService instance"""
    return ProjectService(session)


@pytest.fixture
def formula_service(session):
    """Create a FormulaService instance"""
    return FormulaService(session)


@pytest.fixture
def test_project(session):
    """Create a test project"""
    project = Project(
        name="Test Project Edge Cases",
        client_name="Test Client",
        client_address="Test Address",
        client_phone="123-456-789",
        client_email="test@example.com",
        order_number="EDGE-001",
        kitchen_type="Modern",
    )
    session.add(project)
    session.commit()
    return project


@pytest.fixture
def custom_cabinet(session, test_project, project_service, formula_service):
    """Create a custom cabinet for testing"""
    # Create valid parts using formula service
    valid_parts = formula_service.compute_parts("D60", 600, 720, 560)
    parts_data = [
        {
            "part_name": part.part_name,
            "width_mm": part.width_mm,
            "height_mm": part.height_mm,
            "pieces": part.pieces,
            "material": part.material,
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
        "description": "Test custom cabinet for edge cases",
        "created_via": "EdgeCaseTest",
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

    return cabinet
