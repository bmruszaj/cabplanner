"""
Tests for cabinet editor in-memory pending changes and database save behavior.

Tests that changes are held in memory until Save button is clicked,
then properly persisted to the database.
"""

import pytest
from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db_schema.orm_models import Base, Project, ProjectCabinet, ProjectCabinetPart
from src.db_schema.orm_models import ProjectCabinetAccessorySnapshot
from src.services.project_service import ProjectService
from src.gui.cabinet_editor.pending_changes import PendingChanges


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def project_service(db_session):
    """Create ProjectService with test database."""
    return ProjectService(db_session)


@pytest.fixture
def sample_project(db_session):
    """Create a sample project with a cabinet."""
    project = Project(
        name="Test Project",
        order_number="TEST-001",
        client_name="Test Customer",
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def sample_cabinet(db_session, sample_project):
    """Create a sample cabinet with parts and accessories."""
    cabinet = ProjectCabinet(
        project_id=sample_project.id,
        type_id=None,  # Custom cabinet
        quantity=1,
        sequence_number=1,
        body_color="White",
        front_color="White",
        handle_type="Standard",
    )
    db_session.add(cabinet)
    db_session.commit()

    # Add parts
    part1 = ProjectCabinetPart(
        project_cabinet_id=cabinet.id,
        part_name="Side Panel",
        width_mm=500,
        height_mm=700,
        pieces=2,
        material="PLYTA 18",
    )
    part2 = ProjectCabinetPart(
        project_cabinet_id=cabinet.id,
        part_name="Shelf",
        width_mm=468,
        height_mm=300,
        pieces=1,
        material="PLYTA 18",
    )
    db_session.add_all([part1, part2])

    # Add accessory
    accessory = ProjectCabinetAccessorySnapshot(
        project_cabinet_id=cabinet.id,
        name="Handle",
        sku="HANDLE-001",
        count=2,
    )
    db_session.add(accessory)
    db_session.commit()

    db_session.refresh(cabinet)
    return cabinet


class TestPartsFormPendingChanges:
    """Test parts form in-memory pending changes."""

    def test_pending_changes_not_in_database_before_save(
        self, db_session, project_service, sample_cabinet
    ):
        """Pending additions are not saved to database until explicitly saved."""
        # Simulate adding a part via pending changes (like parts_form does)
        pending = PendingChanges()
        pending.add_item(
            {
                "part_name": "New Shelf",
                "width_mm": 400,
                "height_mm": 200,
                "pieces": 1,
                "material": "PLYTA 16",
            }
        )

        # Verify pending changes exist
        assert len(pending.to_add) == 1

        # But database still has original parts count
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.parts) == 2  # Original parts only

    def test_pending_removals_not_in_database_before_save(
        self, db_session, project_service, sample_cabinet
    ):
        """Pending removals don't affect database until saved."""
        original_part = sample_cabinet.parts[0]

        # Simulate marking for removal via pending changes
        pending = PendingChanges()
        pending.remove_item(original_part.id)

        # Verify pending removal exists
        assert original_part.id in pending.to_remove

        # But database still has the part
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.parts) == 2

    def test_pending_updates_not_in_database_before_save(
        self, db_session, project_service, sample_cabinet
    ):
        """Pending updates don't affect database until saved."""
        original_part = sample_cabinet.parts[0]
        original_name = original_part.part_name

        # Simulate updating via pending changes
        pending = PendingChanges()
        pending.update_item(original_part.id, {"part_name": "Modified Name"})

        # Verify pending update exists
        assert original_part.id in pending.changes

        # But database still has original name
        db_session.refresh(original_part)
        assert original_part.part_name == original_name

    def test_apply_pending_additions_to_database(
        self, db_session, project_service, sample_cabinet
    ):
        """Applying pending additions persists them to database."""
        pending = PendingChanges()
        pending.add_item(
            {
                "part_name": "New Shelf",
                "width_mm": 400,
                "height_mm": 200,
                "pieces": 1,
                "material": "PLYTA 16",
            }
        )

        # Apply changes (simulate what editor_dialog does on save)
        for part_data in pending.get_additions():
            project_service.add_part_to_cabinet(
                cabinet_id=sample_cabinet.id,
                part_name=part_data["part_name"],
                width_mm=part_data["width_mm"],
                height_mm=part_data["height_mm"],
                pieces=part_data["pieces"],
                material=part_data.get("material"),
            )

        # Verify database has new part
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.parts) == 3
        part_names = [p.part_name for p in cabinet.parts]
        assert "New Shelf" in part_names

    def test_apply_pending_removals_to_database(
        self, db_session, project_service, sample_cabinet
    ):
        """Applying pending removals deletes them from database."""
        part_to_remove = sample_cabinet.parts[0]
        part_id = part_to_remove.id

        pending = PendingChanges()
        pending.remove_item(part_id)

        # Apply changes
        for removal_id in pending.get_removals():
            project_service.remove_part_from_cabinet(removal_id)

        # Verify database no longer has the part
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.parts) == 1
        assert all(p.id != part_id for p in cabinet.parts)

    def test_apply_pending_updates_to_database(
        self, db_session, project_service, sample_cabinet
    ):
        """Applying pending updates modifies database records."""
        part_to_update = sample_cabinet.parts[0]

        pending = PendingChanges()
        pending.update_item(
            part_to_update.id,
            {
                "part_name": "Modified Panel",
                "width_mm": 600,
            },
        )

        # Apply changes
        for part_id, part_data in pending.get_updates().items():
            project_service.update_part(part_id, part_data)

        # Verify database has updated values
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        updated_part = next(p for p in cabinet.parts if p.id == part_to_update.id)
        assert updated_part.part_name == "Modified Panel"
        assert updated_part.width_mm == 600


class TestAccessoriesFormPendingChanges:
    """Test accessories form in-memory pending changes."""

    def test_pending_accessory_additions_not_in_database_before_save(
        self, db_session, project_service, sample_cabinet
    ):
        """Pending accessory additions are not saved until explicitly saved."""
        pending = PendingChanges()
        pending.add_item(
            {
                "name": "New Hinge",
                "sku": "HINGE-001",
                "count": 4,
            }
        )

        # Verify pending exists
        assert len(pending.to_add) == 1

        # But database still has original accessory count
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.accessory_snapshots) == 1

    def test_pending_accessory_removals_not_in_database_before_save(
        self, db_session, project_service, sample_cabinet
    ):
        """Pending accessory removals don't affect database until saved."""
        original_accessory = sample_cabinet.accessory_snapshots[0]

        pending = PendingChanges()
        pending.remove_item(original_accessory.id)

        # Verify pending removal exists
        assert original_accessory.id in pending.to_remove

        # But database still has the accessory
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.accessory_snapshots) == 1

    def test_pending_quantity_changes_not_in_database_before_save(
        self, db_session, project_service, sample_cabinet
    ):
        """Pending quantity changes don't affect database until saved."""
        original_accessory = sample_cabinet.accessory_snapshots[0]
        original_count = original_accessory.count

        pending = PendingChanges()
        pending.update_item(original_accessory.id, {"count": 10})

        # Verify pending change exists
        assert original_accessory.id in pending.changes

        # But database still has original count
        db_session.refresh(original_accessory)
        assert original_accessory.count == original_count

    def test_apply_pending_accessory_additions_to_database(
        self, db_session, project_service, sample_cabinet
    ):
        """Applying pending accessory additions persists them to database."""
        pending = PendingChanges()
        pending.add_item(
            {
                "name": "New Hinge",
                "sku": "HINGE-001",
                "count": 4,
            }
        )

        # Apply changes
        for acc_data in pending.get_additions():
            project_service.add_accessory_to_cabinet(
                cabinet_id=sample_cabinet.id,
                name=acc_data["name"],
                sku=acc_data.get("sku"),
                count=acc_data["count"],
            )

        # Verify database has new accessory
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.accessory_snapshots) == 2
        acc_names = [a.name for a in cabinet.accessory_snapshots]
        assert "New Hinge" in acc_names

    def test_apply_pending_accessory_removals_to_database(
        self, db_session, project_service, sample_cabinet
    ):
        """Applying pending accessory removals deletes them from database."""
        acc_to_remove = sample_cabinet.accessory_snapshots[0]
        acc_id = acc_to_remove.id

        pending = PendingChanges()
        pending.remove_item(acc_id)

        # Apply changes
        for removal_id in pending.get_removals():
            project_service.remove_accessory_from_cabinet(removal_id)

        # Verify database no longer has the accessory
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.accessory_snapshots) == 0

    def test_apply_pending_quantity_changes_to_database(
        self, db_session, project_service, sample_cabinet
    ):
        """Applying pending quantity changes modifies database records."""
        acc_to_update = sample_cabinet.accessory_snapshots[0]

        pending = PendingChanges()
        pending.update_item(acc_to_update.id, {"count": 10})

        # Apply quantity changes
        for acc_id, changes in pending.get_updates().items():
            if "count" in changes:
                project_service.update_accessory_quantity(acc_id, changes["count"])

        # Verify database has updated count
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        updated_acc = cabinet.accessory_snapshots[0]
        assert updated_acc.count == 10


class TestPendingChangesClearOnLoad:
    """Test that pending changes are cleared when loading new data."""

    def test_clear_on_load_preserves_database(
        self, db_session, project_service, sample_cabinet
    ):
        """Clearing pending changes on load doesn't affect database."""
        # Add some pending changes
        pending = PendingChanges()
        pending.add_item({"part_name": "Temp Part"})
        pending.remove_item(sample_cabinet.parts[0].id)

        # Clear (simulates loading new cabinet)
        pending.clear()

        # Verify database is unchanged
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert len(cabinet.parts) == 2  # Original count


class TestPendingChangesDisplayIntegration:
    """Test that display correctly shows pending changes."""

    def test_get_display_parts_with_pending_additions(self):
        """Display parts includes pending additions."""
        # Simulate existing parts from database
        existing_parts = [
            SimpleNamespace(id=1, part_name="Part 1", width_mm=100, height_mm=200),
            SimpleNamespace(id=2, part_name="Part 2", width_mm=150, height_mm=250),
        ]

        pending = PendingChanges()
        pending.add_item({"part_name": "New Part", "width_mm": 300, "height_mm": 400})

        # Build display list (simulating _get_display_parts)
        display_parts = list(existing_parts)
        for item in pending.to_add:
            display_parts.append(
                SimpleNamespace(
                    id=None,
                    temp_id=item["temp_id"],
                    part_name=item["part_name"],
                )
            )

        assert len(display_parts) == 3

    def test_get_display_parts_excludes_pending_removals(self):
        """Display parts excludes parts marked for removal."""
        existing_parts = [
            SimpleNamespace(id=1, part_name="Part 1"),
            SimpleNamespace(id=2, part_name="Part 2"),
            SimpleNamespace(id=3, part_name="Part 3"),
        ]

        pending = PendingChanges()
        pending.remove_item(2)  # Mark Part 2 for removal

        # Build display list (simulating _get_display_parts)
        display_parts = [p for p in existing_parts if p.id not in pending.to_remove]

        assert len(display_parts) == 2
        assert all(p.id != 2 for p in display_parts)

    def test_get_display_parts_shows_pending_updates(self):
        """Display parts shows updated values for changed parts."""
        existing_parts = [
            SimpleNamespace(id=1, part_name="Original Name", width_mm=100),
        ]

        pending = PendingChanges()
        pending.update_item(1, {"part_name": "Updated Name"})

        # Build display list with updates applied
        display_parts = []
        for part in existing_parts:
            if part.id in pending.changes:
                updated_data = pending.changes[part.id]
                display_parts.append(
                    SimpleNamespace(
                        id=part.id,
                        part_name=updated_data.get("part_name", part.part_name),
                        width_mm=updated_data.get("width_mm", part.width_mm),
                    )
                )
            else:
                display_parts.append(part)

        assert display_parts[0].part_name == "Updated Name"
        assert display_parts[0].width_mm == 100  # Unchanged


class TestCancelDiscardsPendingChanges:
    """Test that canceling discards pending changes without database effect."""

    def test_cancel_discards_pending_additions(
        self, db_session, project_service, sample_cabinet
    ):
        """Canceling discards pending additions without saving."""
        pending = PendingChanges()
        pending.add_item({"part_name": "Will Be Discarded"})

        # Simulate cancel - just clear without applying
        pending.clear()

        # Verify database unchanged
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        part_names = [p.part_name for p in cabinet.parts]
        assert "Will Be Discarded" not in part_names

    def test_cancel_discards_pending_removals(
        self, db_session, project_service, sample_cabinet
    ):
        """Canceling discards pending removals without deleting."""
        part_id = sample_cabinet.parts[0].id

        pending = PendingChanges()
        pending.remove_item(part_id)

        # Simulate cancel
        pending.clear()

        # Verify database still has the part
        cabinet = project_service.get_cabinet(sample_cabinet.id)
        assert any(p.id == part_id for p in cabinet.parts)

    def test_cancel_discards_pending_updates(
        self, db_session, project_service, sample_cabinet
    ):
        """Canceling discards pending updates without modifying."""
        part = sample_cabinet.parts[0]
        original_name = part.part_name

        pending = PendingChanges()
        pending.update_item(part.id, {"part_name": "Will Be Discarded"})

        # Simulate cancel
        pending.clear()

        # Verify database unchanged
        db_session.refresh(part)
        assert part.part_name == original_name
