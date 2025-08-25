"""
Project Details Controller - orchestrates project cabinet management.

Handles:
- UI event processing
- Data persistence via services
- Business logic coordination
- View state management
"""

from typing import List
from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project, ProjectCabinet
from src.services.project_service import ProjectService
from src.domain.sorting import sort_cabinets, validate_sequence_unique


class ProjectDetailsController(QObject):
    """Controller for project details dialog - handles cabinet management."""

    # Signals for communication with view
    data_loaded = Signal(list)  # List[ProjectCabinet]
    data_error = Signal(str)  # Error message
    cabinet_updated = Signal(object)  # Updated ProjectCabinet
    validation_error = Signal(str)  # Validation error message

    def __init__(self, session: Session, project: Project, parent=None):
        super().__init__(parent)
        self.session = session
        self.project = project
        self.project_service = ProjectService(session)
        self.cabinets: List[ProjectCabinet] = []

    def load_data(self):
        """Load project cabinets and emit sorted data."""
        try:
            self.cabinets = self.project_service.list_cabinets(self.project.id)
            ordered_cabinets = sort_cabinets(self.cabinets)
            self.data_loaded.emit(ordered_cabinets)
        except Exception as e:
            error_msg = f"Błąd podczas ładowania danych projektu: {str(e)}"
            self.data_error.emit(error_msg)

    def on_sequence_changed(self, cabinet_id: int, new_sequence: int):
        """
        Handle sequence number change from UI.

        Args:
            cabinet_id: ID of the cabinet to update
            new_sequence: New sequence number
        """
        try:
            # Find the current cabinet
            current_cabinet = None
            for cabinet in self.cabinets:
                if cabinet.id == cabinet_id:
                    current_cabinet = cabinet
                    break

            if not current_cabinet:
                self.validation_error.emit("Nie znaleziono szafy do aktualizacji")
                return

            # Check if sequence is actually changing
            if current_cabinet.sequence_number == new_sequence:
                # Sequence hasn't changed, no need to update
                return

            # Validate sequence uniqueness
            temp_cabinets = [c for c in self.cabinets if c.id != cabinet_id]
            temp_cabinet = ProjectCabinet(id=cabinet_id, sequence_number=new_sequence)
            temp_cabinets.append(temp_cabinet)

            validation_errors = validate_sequence_unique(temp_cabinets)
            if validation_errors:
                self.validation_error.emit(validation_errors[0])
                return

            # Update cabinet via service
            updated_cabinet = self.project_service.update_cabinet(
                cabinet_id, sequence_number=new_sequence
            )

            if not updated_cabinet:
                self.validation_error.emit("Nie udało się zaktualizować sekwencji")
                return

            # Update local cache
            self._replace_cabinet_in_cache(updated_cabinet)

            # Re-sort and emit new order
            ordered_cabinets = sort_cabinets(self.cabinets)
            self.data_loaded.emit(ordered_cabinets)
            self.cabinet_updated.emit(updated_cabinet)

        except Exception as e:
            error_msg = f"Błąd podczas aktualizacji sekwencji: {str(e)}"
            self.validation_error.emit(error_msg)

    def on_sort_requested(self):
        """Handle explicit sort request from UI (toolbar button)."""
        try:
            ordered_cabinets = sort_cabinets(self.cabinets)
            self.data_loaded.emit(ordered_cabinets)
        except Exception as e:
            error_msg = f"Błąd podczas sortowania: {str(e)}"
            self.data_error.emit(error_msg)

    def on_cabinet_deleted(self, cabinet_id: int):
        """
        Handle cabinet deletion.

        Args:
            cabinet_id: ID of the cabinet to delete
        """
        try:
            success = self.project_service.delete_cabinet(cabinet_id)
            if not success:
                self.validation_error.emit("Nie udało się usunąć szafy")
                return

            # Remove from local cache
            self.cabinets = [c for c in self.cabinets if c.id != cabinet_id]

            # Re-emit sorted data
            ordered_cabinets = sort_cabinets(self.cabinets)
            self.data_loaded.emit(ordered_cabinets)

        except Exception as e:
            error_msg = f"Błąd podczas usuwania szafy: {str(e)}"
            self.validation_error.emit(error_msg)

    def _replace_cabinet_in_cache(self, updated_cabinet: ProjectCabinet):
        """Replace cabinet in local cache with updated version."""
        for i, cabinet in enumerate(self.cabinets):
            if cabinet.id == updated_cabinet.id:
                self.cabinets[i] = updated_cabinet
                break
