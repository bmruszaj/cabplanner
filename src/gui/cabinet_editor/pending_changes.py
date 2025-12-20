"""
Pending changes container for cabinet editor forms.

Provides a unified structure for tracking in-memory changes
that are only persisted when the user clicks Save.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PendingChanges:
    """
    Container for pending changes in editor forms.

    All changes are tracked with temporary IDs for new items,
    allowing proper identification even before database persistence.
    """

    # Items to add: list of dicts with temp_id and data
    to_add: list[dict[str, Any]] = field(default_factory=list)

    # Item IDs to remove (database IDs for existing, temp_id for pending)
    to_remove: list[int] = field(default_factory=list)

    # Changes to existing items: {item_id: updated_data_dict}
    changes: dict[int, dict[str, Any]] = field(default_factory=dict)

    # Counter for generating temporary IDs (negative to avoid DB conflicts)
    _temp_id_counter: int = field(default=-1, repr=False)

    def next_temp_id(self) -> int:
        """Generate next temporary ID for new items."""
        temp_id = self._temp_id_counter
        self._temp_id_counter -= 1
        return temp_id

    def add_item(self, data: dict[str, Any]) -> int:
        """
        Add a new item to pending additions.

        Returns the temporary ID assigned to the item.
        """
        temp_id = self.next_temp_id()
        item = {"temp_id": temp_id, **data}
        self.to_add.append(item)
        return temp_id

    def update_item(self, item_id: int, data: dict[str, Any]) -> None:
        """
        Update an item (existing or pending).

        For existing items (positive ID): adds to changes dict.
        For pending items (negative ID): updates in to_add list.
        """
        if item_id < 0:
            # Pending item - update in to_add
            for item in self.to_add:
                if item.get("temp_id") == item_id:
                    item.update(data)
                    return
        else:
            # Existing item - track change
            if item_id in self.changes:
                self.changes[item_id].update(data)
            else:
                self.changes[item_id] = data.copy()

    def remove_item(self, item_id: int) -> None:
        """
        Mark an item for removal.

        For existing items (positive ID): adds to to_remove list.
        For pending items (negative ID): removes from to_add list.
        """
        if item_id < 0:
            # Pending item - remove from to_add
            self.to_add = [
                item for item in self.to_add if item.get("temp_id") != item_id
            ]
        else:
            # Existing item - mark for removal
            if item_id not in self.to_remove:
                self.to_remove.append(item_id)
            # Also remove any pending changes for this item
            self.changes.pop(item_id, None)

    def clear(self) -> None:
        """Clear all pending changes."""
        self.to_add.clear()
        self.to_remove.clear()
        self.changes.clear()
        self._temp_id_counter = -1

    def has_changes(self) -> bool:
        """Check if there are any pending changes."""
        return bool(self.to_add or self.to_remove or self.changes)

    def get_additions(self) -> list[dict[str, Any]]:
        """Get items to add (without temp_id for database insertion)."""
        return [
            {k: v for k, v in item.items() if k != "temp_id"} for item in self.to_add
        ]

    def get_removals(self) -> list[int]:
        """Get IDs of items to remove."""
        return self.to_remove.copy()

    def get_updates(self) -> dict[int, dict[str, Any]]:
        """Get item updates."""
        return self.changes.copy()
