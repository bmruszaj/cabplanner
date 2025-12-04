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

            # Validate sequence uniqueness - create temporary cabinet with proper project_id
            temp_cabinets = [c for c in self.cabinets if c.id != cabinet_id]
            temp_cabinet = ProjectCabinet(
                id=cabinet_id,
                project_id=current_cabinet.project_id,
                sequence_number=new_sequence,
            )
            temp_cabinets.append(temp_cabinet)

            validation_errors = validate_sequence_unique(temp_cabinets)
            if validation_errors:
                self.validation_error.emit(validation_errors[0])
                return

            # Update cabinet via service
            try:
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

            except Exception as db_error:
                # Handle database constraint errors specifically
                if "UNIQUE constraint failed" in str(db_error):
                    self.validation_error.emit(
                        f"Sekwencja {new_sequence} już istnieje w projekcie"
                    )
                else:
                    self.validation_error.emit(f"Błąd bazy danych: {str(db_error)}")
                return

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

    def on_quantity_changed(self, cabinet_id: int, new_quantity: int):
        """
        Handle quantity change from UI.

        Args:
            cabinet_id: ID of the cabinet to update
            new_quantity: New quantity value
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

            # Check if quantity is actually changing
            if current_cabinet.quantity == new_quantity:
                # Quantity hasn't changed, no need to update
                return

            # Update cabinet via service
            try:
                updated_cabinet = self.project_service.update_cabinet(
                    cabinet_id, quantity=new_quantity
                )

                if not updated_cabinet:
                    self.validation_error.emit("Nie udało się zaktualizować ilości")
                    return

                # Update local cache
                self._replace_cabinet_in_cache(updated_cabinet)

                # Re-sort and emit new order
                ordered_cabinets = sort_cabinets(self.cabinets)
                self.data_loaded.emit(ordered_cabinets)
                self.cabinet_updated.emit(updated_cabinet)

            except Exception as db_error:
                self.validation_error.emit(
                    f"Błąd bazy danych podczas aktualizacji ilości: {str(db_error)}"
                )
                return

        except Exception as e:
            error_msg = f"Błąd podczas aktualizacji ilości: {str(e)}"
            self.validation_error.emit(error_msg)

    def on_cabinet_deleted(self, cabinet_id: int):
        """
        Handle cabinet deletion.

        Args:
            cabinet_id: ID of the cabinet to delete
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"[CONTROLLER] on_cabinet_deleted: cabinet_id={cabinet_id}")
        try:
            success = self.project_service.delete_cabinet(cabinet_id)
            logger.debug(f"[CONTROLLER] delete_cabinet success={success}")
            if not success:
                self.validation_error.emit("Nie udało się usunąć szafy")
                return

            # Remove from local cache
            old_count = len(self.cabinets)
            self.cabinets = [c for c in self.cabinets if c.id != cabinet_id]
            logger.debug(
                f"[CONTROLLER] cache updated: {old_count} -> {len(self.cabinets)} cabinets"
            )

            # Re-emit sorted data
            ordered_cabinets = sort_cabinets(self.cabinets)
            logger.debug(
                f"[CONTROLLER] emitting data_loaded with {len(ordered_cabinets)} cabinets"
            )
            self.data_loaded.emit(ordered_cabinets)

        except Exception as e:
            error_msg = f"Błąd podczas usuwania szafy: {str(e)}"
            logger.exception(f"[CONTROLLER] delete error: {e}")
            self.validation_error.emit(error_msg)

    def _replace_cabinet_in_cache(self, updated_cabinet: ProjectCabinet):
        """Replace cabinet in local cache with updated version."""
        for i, cabinet in enumerate(self.cabinets):
            if cabinet.id == updated_cabinet.id:
                self.cabinets[i] = updated_cabinet
                break

    def get_next_cabinet_sequence(self, project_id: int) -> int:
        """Get the next available sequence number for a cabinet."""
        return self.project_service.get_next_cabinet_sequence(project_id)

    def add_cabinet(self, project_id: int, **kwargs):
        """Add a cabinet to the project."""
        try:
            # Check if this is a custom cabinet with parts
            if "parts" in kwargs:
                return self._add_custom_cabinet_with_parts(project_id, **kwargs)

            # Standard cabinet addition
            sequence_number = kwargs.get(
                "sequence_number"
            ) or self.get_next_cabinet_sequence(project_id)

            cabinet_data = {
                "sequence_number": sequence_number,
                "type_id": kwargs.get(
                    "type_id", None
                ),  # Use provided type_id or None for custom
                "body_color": kwargs.get("body_color", "#ffffff"),
                "front_color": kwargs.get("front_color", "#ffffff"),
                "handle_type": kwargs.get("handle_type", "Standardowy"),
                "quantity": kwargs.get("quantity", 1),
            }

            new_cabinet = self.project_service.add_cabinet(project_id, **cabinet_data)
            self.cabinets.append(new_cabinet)
            self.load_data()
            return new_cabinet

        except Exception as e:
            error_msg = f"Błąd podczas dodawania szafy: {str(e)}"
            self.validation_error.emit(error_msg)
            raise

    def _add_custom_cabinet_with_parts(self, project_id: int, **kwargs):
        """Add a custom cabinet with calculated parts using new architecture."""
        try:
            # Create custom cabinet WITHOUT creating CabinetTemplate (type_id=NULL)
            next_sequence = self.get_next_cabinet_sequence(project_id)

            cabinet_data = {
                "sequence_number": next_sequence,
                "type_id": None,  # Custom cabinet - no template
                "body_color": kwargs.get("body_color", "#ffffff"),
                "front_color": kwargs.get("front_color", "#ffffff"),
                "handle_type": kwargs.get("handle_type", "Standardowy"),
                "quantity": kwargs.get("quantity", 1),
            }

            # Create the cabinet first
            new_cabinet = self.project_service.add_cabinet(project_id, **cabinet_data)

            # Now add all the calculated parts to ProjectCabinetPart table (new architecture)
            from src.db_schema.orm_models import ProjectCabinetPart

            for part_data in kwargs.get("parts", []):
                custom_part = ProjectCabinetPart(
                    project_cabinet_id=new_cabinet.id,
                    part_name=part_data["part_name"],
                    height_mm=part_data["height_mm"],
                    width_mm=part_data["width_mm"],
                    pieces=part_data["pieces"],
                    material=part_data.get("material"),
                    thickness_mm=part_data.get("thickness_mm"),
                    wrapping=part_data.get("wrapping"),
                    comments=part_data.get("comments"),
                )
                self.session.add(custom_part)

            # Commit all parts
            self.session.commit()

            self.cabinets.append(new_cabinet)
            self.load_data()
            return new_cabinet

        except Exception as e:
            self.session.rollback()
            error_msg = f"Błąd podczas dodawania niestandardowej szafy: {str(e)}"
            self.validation_error.emit(error_msg)
            raise

    def add_catalog_cabinet(self, cabinet_data):
        """Add a cabinet from catalog to the project."""
        try:
            # Handle both dictionary and object inputs
            if hasattr(cabinet_data, "__dict__"):
                # It's an object (like ProjectCabinet), already added to database
                # Just update local cache and reload
                self.cabinets.append(cabinet_data)
                self.load_data()
                return cabinet_data
            else:
                # It's a dictionary, convert to cabinet data
                data = {
                    "name": cabinet_data.get("name", "Cabinet"),
                    "width": cabinet_data.get("width", 60),
                    "height": cabinet_data.get("height", 72),
                    "depth": cabinet_data.get("depth", 35),
                    "code": cabinet_data.get("code", ""),
                    "description": cabinet_data.get("description", ""),
                    "price": cabinet_data.get("price", 0.0),
                }

                # Get next sequence number
                next_sequence = self.get_next_cabinet_sequence(self.project.id)
                data["sequence_number"] = next_sequence

                # Add cabinet through project service - need to use proper parameters
                cabinet_kwargs = {
                    "sequence_number": data["sequence_number"],
                    "type_id": None,  # Catalog method creates custom cabinets
                    "body_color": "#ffffff",  # Default colors
                    "front_color": "#ffffff",
                    "handle_type": "Standardowy",
                    "quantity": 1,
                }
                new_cabinet = self.project_service.add_cabinet(
                    self.project.id, **cabinet_kwargs
                )

                # Update local cache
                self.cabinets.append(new_cabinet)

                # Reload data to refresh view
                self.load_data()

                return new_cabinet

        except Exception as e:
            error_msg = f"Błąd podczas dodawania szafy z katalogu: {str(e)}"
            self.validation_error.emit(error_msg)
            raise
