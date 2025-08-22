"""
Project Details Actions - Slot handlers for UI actions.

This module provides centralized action handling for project details operations
like add, edit, delete, duplicate cabinet actions.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Any, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from src.db_schema.orm_models import Project
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProjectDetailsActions(QObject):
    """
    Actions handler for project details operations.

    This class centralizes all the action callbacks and business logic
    for cabinet operations, providing a clean interface between UI and data.
    """

    # Signals for notifying controllers and views
    cabinet_added = Signal(object)  # ProjectCabinet
    cabinet_edited = Signal(object)  # ProjectCabinet
    cabinet_deleted = Signal(int)  # cabinet_id
    cabinet_duplicated = Signal(object)  # ProjectCabinet
    project_exported = Signal(str)  # format_type
    project_printed = Signal()

    def __init__(self, project: Project, session: Session, parent=None):
        """
        Initialize the actions handler.

        Args:
            project: The project to handle actions for
            session: Database session
            parent: Parent object
        """
        super().__init__(parent)
        self.project = project
        self.session = session

        # Callback registry for external handlers
        self._callbacks: Dict[str, Callable] = {}

        logger.debug(f"Initialized ProjectDetailsActions for project: {project.name}")

    def register_callback(self, action_name: str, callback: Callable) -> None:
        """
        Register a callback for an action.

        Args:
            action_name: Name of the action
            callback: Callback function to register
        """
        self._callbacks[action_name] = callback
        logger.debug(f"Registered callback for action: {action_name}")

    def _call_callback(self, action_name: str, *args, **kwargs) -> Any:
        """Call a registered callback if it exists."""
        callback = self._callbacks.get(action_name)
        if callback:
            try:
                return callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in callback {action_name}: {e}")
                return None
        return None

    # Cabinet actions
    def add_cabinet_from_catalog(self) -> None:
        """Handle adding a cabinet from the catalog."""
        logger.debug("Action: Add cabinet from catalog")

        # TODO: Open cabinet catalog dialog
        # This would typically:
        # 1. Open the cabinet type selection dialog
        # 2. Allow user to choose type, colors, etc.
        # 3. Create new ProjectCabinet instance
        # 4. Add to project and emit signal

        # Call external callback if registered
        result = self._call_callback("add_from_catalog")
        if result:
            self.cabinet_added.emit(result)

    def add_custom_cabinet(self) -> None:
        """Handle adding a custom cabinet."""
        logger.debug("Action: Add custom cabinet")

        # TODO: Open custom cabinet dialog
        # This would typically:
        # 1. Open custom cabinet creation dialog
        # 2. Allow user to specify dimensions, colors, etc.
        # 3. Create new ProjectCabinet instance (type_id = None)
        # 4. Add to project and emit signal

        # Call external callback if registered
        result = self._call_callback("add_custom")
        if result:
            self.cabinet_added.emit(result)

    def edit_cabinet(self, cabinet_id: int) -> None:
        """
        Handle editing a cabinet.

        Args:
            cabinet_id: ID of cabinet to edit
        """
        logger.debug(f"Action: Edit cabinet {cabinet_id}")

        # TODO: Open cabinet edit dialog
        # This would typically:
        # 1. Find the cabinet by ID
        # 2. Open edit dialog with current values
        # 3. Update cabinet properties
        # 4. Save changes and emit signal

        # Call external callback if registered
        result = self._call_callback("edit_cabinet", cabinet_id)
        if result:
            self.cabinet_edited.emit(result)

    def duplicate_cabinet(self, cabinet_id: int) -> None:
        """
        Handle duplicating a cabinet.

        Args:
            cabinet_id: ID of cabinet to duplicate
        """
        logger.debug(f"Action: Duplicate cabinet {cabinet_id}")

        # TODO: Implement cabinet duplication
        # This would typically:
        # 1. Find the cabinet by ID
        # 2. Create a copy with new sequence number
        # 3. Add to project and emit signal

        # Call external callback if registered
        result = self._call_callback("duplicate_cabinet", cabinet_id)
        if result:
            self.cabinet_duplicated.emit(result)

    def delete_cabinet(self, cabinet_id: int, confirm: bool = True) -> bool:
        """
        Handle deleting a cabinet.

        Args:
            cabinet_id: ID of cabinet to delete
            confirm: Whether to show confirmation dialog

        Returns:
            True if cabinet was deleted
        """
        logger.debug(f"Action: Delete cabinet {cabinet_id}")

        if confirm:
            # Show confirmation dialog
            reply = QMessageBox.question(
                None,  # Parent widget would be passed in real implementation
                "Potwierdź usunięcie",
                "Czy na pewno chcesz usunąć tę szafkę?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                logger.debug("Cabinet deletion cancelled by user")
                return False

        # TODO: Implement cabinet deletion
        # This would typically:
        # 1. Find the cabinet by ID
        # 2. Remove from project
        # 3. Update sequence numbers of remaining cabinets
        # 4. Save changes and emit signal

        # Call external callback if registered
        success = self._call_callback("delete_cabinet", cabinet_id)
        if success:
            self.cabinet_deleted.emit(cabinet_id)
            return True

        return False

    def delete_multiple_cabinets(self, cabinet_ids: list[int]) -> int:
        """
        Handle deleting multiple cabinets.

        Args:
            cabinet_ids: List of cabinet IDs to delete

        Returns:
            Number of cabinets actually deleted
        """
        if not cabinet_ids:
            return 0

        logger.debug(f"Action: Delete multiple cabinets ({len(cabinet_ids)})")

        # Show confirmation dialog
        reply = QMessageBox.question(
            None,
            "Potwierdź usunięcie",
            f"Czy na pewno chcesz usunąć {len(cabinet_ids)} szafek?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            logger.debug("Multiple cabinet deletion cancelled by user")
            return 0

        # Delete each cabinet
        deleted_count = 0
        for cabinet_id in cabinet_ids:
            if self.delete_cabinet(cabinet_id, confirm=False):
                deleted_count += 1

        logger.debug(f"Deleted {deleted_count}/{len(cabinet_ids)} cabinets")
        return deleted_count

    def update_cabinet_quantity(self, cabinet_id: int, new_quantity: int) -> bool:
        """
        Handle updating cabinet quantity.

        Args:
            cabinet_id: ID of cabinet to update
            new_quantity: New quantity value

        Returns:
            True if quantity was updated
        """
        if new_quantity < 1:
            logger.warning(f"Invalid quantity {new_quantity} for cabinet {cabinet_id}")
            return False

        logger.debug(f"Action: Update cabinet {cabinet_id} quantity to {new_quantity}")

        # TODO: Implement quantity update
        # This would typically:
        # 1. Find the cabinet by ID
        # 2. Update quantity property
        # 3. Save changes

        # Call external callback if registered
        result = self._call_callback("update_quantity", cabinet_id, new_quantity)
        return result is not False

    # Project actions
    def export_project(self, format_type: str = "pdf") -> bool:
        """
        Handle exporting the project.

        Args:
            format_type: Export format ("pdf", "excel", etc.)

        Returns:
            True if export was successful
        """
        logger.debug(f"Action: Export project as {format_type}")

        # TODO: Implement project export
        # This would typically:
        # 1. Generate report using ReportGenerator service
        # 2. Save to user-selected location
        # 3. Show success/error message

        # Call external callback if registered
        result = self._call_callback("export_project", format_type)
        if result is not False:
            self.project_exported.emit(format_type)
            return True

        return False

    def print_project(self) -> bool:
        """
        Handle printing the project.

        Returns:
            True if print was successful
        """
        logger.debug("Action: Print project")

        # TODO: Implement project printing
        # This would typically:
        # 1. Generate printable document
        # 2. Send to system printer
        # 3. Show success/error message

        # Call external callback if registered
        result = self._call_callback("print_project")
        if result is not False:
            self.project_printed.emit()
            return True

        return False

    # Bulk operations
    def bulk_edit_cabinets(self, cabinet_ids: list[int]) -> None:
        """
        Handle bulk editing of multiple cabinets.

        Args:
            cabinet_ids: List of cabinet IDs to edit
        """
        if not cabinet_ids:
            return

        logger.debug(f"Action: Bulk edit {len(cabinet_ids)} cabinets")

        # TODO: Open bulk edit dialog
        # This would typically:
        # 1. Open dialog for editing common properties
        # 2. Apply changes to all selected cabinets
        # 3. Save changes and emit signals

        # Call external callback if registered
        self._call_callback("bulk_edit", cabinet_ids)

    def duplicate_multiple_cabinets(self, cabinet_ids: list[int]) -> int:
        """
        Handle duplicating multiple cabinets.

        Args:
            cabinet_ids: List of cabinet IDs to duplicate

        Returns:
            Number of cabinets actually duplicated
        """
        if not cabinet_ids:
            return 0

        logger.debug(f"Action: Duplicate {len(cabinet_ids)} cabinets")

        # Duplicate each cabinet
        duplicated_count = 0
        for cabinet_id in cabinet_ids:
            self.duplicate_cabinet(cabinet_id)
            duplicated_count += 1

        logger.debug(f"Duplicated {duplicated_count} cabinets")
        return duplicated_count

    # Search and filter actions
    def clear_search(self) -> None:
        """Handle clearing search filters."""
        logger.debug("Action: Clear search")
        self._call_callback("clear_search")

    def clear_all_filters(self) -> None:
        """Handle clearing all filters."""
        logger.debug("Action: Clear all filters")
        self._call_callback("clear_filters")

    def show_all_cabinets(self) -> None:
        """Handle showing all cabinets (clear filters)."""
        logger.debug("Action: Show all cabinets")
        self.clear_all_filters()

    # Utility methods
    def get_project(self) -> Project:
        """Get the current project."""
        return self.project

    def get_session(self) -> Session:
        """Get the database session."""
        return self.session

    def set_project(self, project: Project) -> None:
        """
        Set a new project.

        Args:
            project: New project to handle actions for
        """
        self.project = project
        logger.debug(f"Set new project: {project.name}")

    def has_callback(self, action_name: str) -> bool:
        """
        Check if a callback is registered for an action.

        Args:
            action_name: Name of the action

        Returns:
            True if callback is registered
        """
        return action_name in self._callbacks
