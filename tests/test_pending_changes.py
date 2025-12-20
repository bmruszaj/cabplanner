"""
Tests for PendingChanges class - in-memory change tracking.

Tests the unified container for tracking add/edit/delete operations
that are held in memory until explicitly saved.
"""

from src.gui.cabinet_editor.pending_changes import PendingChanges


class TestPendingChangesInit:
    """Test PendingChanges initialization."""

    def test_init_empty(self):
        """PendingChanges starts empty."""
        pc = PendingChanges()
        assert pc.to_add == []
        assert pc.to_remove == []
        assert pc.changes == {}
        assert not pc.has_changes()

    def test_init_counter_starts_at_minus_one(self):
        """Temp ID counter starts at -1."""
        pc = PendingChanges()
        assert pc._temp_id_counter == -1


class TestPendingChangesAddItem:
    """Test adding items to pending changes."""

    def test_add_item_returns_temp_id(self):
        """add_item returns a negative temporary ID."""
        pc = PendingChanges()
        temp_id = pc.add_item({"name": "Test Part"})
        assert temp_id == -1

    def test_add_item_increments_temp_id(self):
        """Each add_item returns a decreasing temp ID."""
        pc = PendingChanges()
        id1 = pc.add_item({"name": "Part 1"})
        id2 = pc.add_item({"name": "Part 2"})
        id3 = pc.add_item({"name": "Part 3"})

        assert id1 == -1
        assert id2 == -2
        assert id3 == -3

    def test_add_item_stores_data_with_temp_id(self):
        """add_item stores data dict with temp_id included."""
        pc = PendingChanges()
        temp_id = pc.add_item({"name": "Test", "width": 100})

        assert len(pc.to_add) == 1
        assert pc.to_add[0]["temp_id"] == temp_id
        assert pc.to_add[0]["name"] == "Test"
        assert pc.to_add[0]["width"] == 100

    def test_add_item_marks_has_changes(self):
        """Adding an item marks has_changes as True."""
        pc = PendingChanges()
        assert not pc.has_changes()

        pc.add_item({"name": "Test"})
        assert pc.has_changes()


class TestPendingChangesUpdateItem:
    """Test updating items in pending changes."""

    def test_update_existing_item_positive_id(self):
        """Updating item with positive ID adds to changes dict."""
        pc = PendingChanges()
        pc.update_item(42, {"name": "Updated Name"})

        assert 42 in pc.changes
        assert pc.changes[42]["name"] == "Updated Name"

    def test_update_existing_item_merges_changes(self):
        """Multiple updates to same item are merged."""
        pc = PendingChanges()
        pc.update_item(42, {"name": "Name1"})
        pc.update_item(42, {"width": 100})
        pc.update_item(42, {"name": "Name2"})

        assert pc.changes[42]["name"] == "Name2"
        assert pc.changes[42]["width"] == 100

    def test_update_pending_item_negative_id(self):
        """Updating item with negative ID updates in to_add list."""
        pc = PendingChanges()
        temp_id = pc.add_item({"name": "Original", "width": 50})

        pc.update_item(temp_id, {"name": "Updated", "height": 100})

        assert len(pc.to_add) == 1
        assert pc.to_add[0]["name"] == "Updated"
        assert pc.to_add[0]["height"] == 100
        assert pc.to_add[0]["width"] == 50  # Original value preserved

    def test_update_marks_has_changes(self):
        """Updating an item marks has_changes as True."""
        pc = PendingChanges()
        assert not pc.has_changes()

        pc.update_item(42, {"name": "Test"})
        assert pc.has_changes()


class TestPendingChangesRemoveItem:
    """Test removing items from pending changes."""

    def test_remove_existing_item_positive_id(self):
        """Removing item with positive ID adds to to_remove list."""
        pc = PendingChanges()
        pc.remove_item(42)

        assert 42 in pc.to_remove

    def test_remove_existing_item_clears_pending_changes(self):
        """Removing an item also clears any pending changes for it."""
        pc = PendingChanges()
        pc.update_item(42, {"name": "Updated"})
        assert 42 in pc.changes

        pc.remove_item(42)

        assert 42 in pc.to_remove
        assert 42 not in pc.changes

    def test_remove_pending_item_negative_id(self):
        """Removing item with negative ID removes from to_add list."""
        pc = PendingChanges()
        temp_id = pc.add_item({"name": "To Remove"})
        pc.add_item({"name": "To Keep"})

        assert len(pc.to_add) == 2

        pc.remove_item(temp_id)

        assert len(pc.to_add) == 1
        assert pc.to_add[0]["name"] == "To Keep"

    def test_remove_does_not_duplicate_ids(self):
        """Removing same ID twice doesn't duplicate in to_remove."""
        pc = PendingChanges()
        pc.remove_item(42)
        pc.remove_item(42)

        assert pc.to_remove.count(42) == 1

    def test_remove_marks_has_changes(self):
        """Removing an item marks has_changes as True."""
        pc = PendingChanges()
        assert not pc.has_changes()

        pc.remove_item(42)
        assert pc.has_changes()


class TestPendingChangesClear:
    """Test clearing pending changes."""

    def test_clear_removes_all_data(self):
        """clear() removes all pending changes."""
        pc = PendingChanges()
        pc.add_item({"name": "Added"})
        pc.update_item(42, {"name": "Updated"})
        pc.remove_item(100)

        pc.clear()

        assert pc.to_add == []
        assert pc.to_remove == []
        assert pc.changes == {}
        assert not pc.has_changes()

    def test_clear_resets_temp_id_counter(self):
        """clear() resets the temp ID counter."""
        pc = PendingChanges()
        pc.add_item({"name": "1"})
        pc.add_item({"name": "2"})

        pc.clear()

        assert pc._temp_id_counter == -1
        new_id = pc.add_item({"name": "3"})
        assert new_id == -1


class TestPendingChangesGetters:
    """Test getter methods for retrieving changes."""

    def test_get_additions_returns_data_without_temp_id(self):
        """get_additions() returns item data without temp_id field."""
        pc = PendingChanges()
        pc.add_item({"name": "Part 1", "width": 100})
        pc.add_item({"name": "Part 2", "height": 200})

        additions = pc.get_additions()

        assert len(additions) == 2
        assert additions[0] == {"name": "Part 1", "width": 100}
        assert additions[1] == {"name": "Part 2", "height": 200}
        # Verify temp_id is not included
        assert "temp_id" not in additions[0]
        assert "temp_id" not in additions[1]

    def test_get_removals_returns_copy(self):
        """get_removals() returns a copy of to_remove list."""
        pc = PendingChanges()
        pc.remove_item(42)
        pc.remove_item(100)

        removals = pc.get_removals()

        assert removals == [42, 100]
        # Verify it's a copy
        removals.append(999)
        assert 999 not in pc.to_remove

    def test_get_updates_returns_copy(self):
        """get_updates() returns a copy of changes dict."""
        pc = PendingChanges()
        pc.update_item(42, {"name": "Updated"})

        updates = pc.get_updates()

        assert updates == {42: {"name": "Updated"}}
        # Verify it's a copy
        updates[999] = {"name": "New"}
        assert 999 not in pc.changes


class TestPendingChangesHasChanges:
    """Test has_changes() method."""

    def test_has_changes_false_when_empty(self):
        """has_changes() returns False when no changes."""
        pc = PendingChanges()
        assert not pc.has_changes()

    def test_has_changes_true_with_additions(self):
        """has_changes() returns True when there are additions."""
        pc = PendingChanges()
        pc.add_item({"name": "Test"})
        assert pc.has_changes()

    def test_has_changes_true_with_removals(self):
        """has_changes() returns True when there are removals."""
        pc = PendingChanges()
        pc.remove_item(42)
        assert pc.has_changes()

    def test_has_changes_true_with_updates(self):
        """has_changes() returns True when there are updates."""
        pc = PendingChanges()
        pc.update_item(42, {"name": "Updated"})
        assert pc.has_changes()


class TestPendingChangesComplexScenarios:
    """Test complex usage scenarios."""

    def test_add_then_update_then_remove_pending_item(self):
        """Add, update, then remove a pending item."""
        pc = PendingChanges()

        temp_id = pc.add_item({"name": "Original"})
        assert len(pc.to_add) == 1

        pc.update_item(temp_id, {"name": "Updated"})
        assert pc.to_add[0]["name"] == "Updated"

        pc.remove_item(temp_id)
        assert len(pc.to_add) == 0

    def test_update_then_remove_existing_item(self):
        """Update then remove an existing item."""
        pc = PendingChanges()

        pc.update_item(42, {"name": "Updated"})
        assert 42 in pc.changes

        pc.remove_item(42)
        assert 42 in pc.to_remove
        assert 42 not in pc.changes

    def test_mixed_operations(self):
        """Perform mixed add/update/remove operations."""
        pc = PendingChanges()

        # Add new items
        id1 = pc.add_item({"name": "New 1"})
        id2 = pc.add_item({"name": "New 2"})

        # Update existing items
        pc.update_item(100, {"name": "Updated 100"})
        pc.update_item(200, {"name": "Updated 200"})

        # Remove existing items
        pc.remove_item(300)
        pc.remove_item(400)

        # Update a pending item
        pc.update_item(id1, {"name": "New 1 Updated"})

        # Remove a pending item
        pc.remove_item(id2)

        # Verify state
        assert len(pc.to_add) == 1
        assert pc.to_add[0]["name"] == "New 1 Updated"

        assert len(pc.changes) == 2
        assert pc.changes[100]["name"] == "Updated 100"
        assert pc.changes[200]["name"] == "Updated 200"

        assert len(pc.to_remove) == 2
        assert 300 in pc.to_remove
        assert 400 in pc.to_remove
