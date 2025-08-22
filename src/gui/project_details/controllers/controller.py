"""
Main Project Details Controller.

This controller orchestrates all business logic for the project details dialog.
It manages data operations, coordinates between different UI components,
and handles user interactions.
"""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from src.db_schema.orm_models import Project
from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator
from src.gui.add_cabinet_dialog import AddCabinetDialog
from src.gui.adhoc_cabinet_dialog import AdhocCabinetDialog

# Import models and UI state
from ..models import (
    CabinetTableModel,
    make_proxy,
    setup_color_chip_delegate,
    UiState,
    open_or_print,
)

if TYPE_CHECKING:
    from ..view import ProjectDetailsView

logger = logging.getLogger(__name__)


class ProjectDetailsController(QObject):
    """
    Main controller for project details functionality.

    This controller handles:
    - Project data operations (CRUD)
    - Cabinet management (add, edit, delete, reorder)
    - View mode and search functionality
    - UI state persistence
    - Integration with existing dialogs
    """

    def __init__(self, session: Session, project: Project, modal: bool = False):
        """
        Initialize the controller.

        Args:
            session: Database session for operations
            project: The project to manage
            modal: Whether the dialog should be modal
        """
        super().__init__()

        self.session = session
        self.project = project
        self.modal = modal
        self.view: Optional[ProjectDetailsView] = None

        # Initialize services
        self.project_service = ProjectService(session)
        self.report_generator = ReportGenerator(session)

        # Initialize UI state persistence
        self.ui_state = UiState()

        # Initialize data models
        self.cabinet_model: Optional[CabinetTableModel] = None
        self.cabinet_proxy: Optional[object] = None

        # Track cabinet data
        self.cabinets = []

        logger.debug(
            f"Initialized ProjectDetailsController for project: {project.name}"
        )

    def attach(self, view: ProjectDetailsView) -> None:
        """
        Attach the controller to a view and wire all signals.

        Args:
            view: The view to control
        """
        self.view = view

        # Wire all view signals to controller slots
        self._wire_signals()

        # Load initial data
        self._load_project_data()

        # Setup table model and proxy
        self._setup_table_model()

        # Restore UI state
        self._restore_ui_state()

        logger.debug("Controller attached to view and signals wired")

    def open(self) -> None:
        """Show the dialog (exec/show based on modal setting)."""
        if not self.view:
            logger.error("Cannot open: no view attached")
            return

        if self.modal:
            self.view.exec()
        else:
            self.view.show()

    def _wire_signals(self) -> None:
        """Wire all view signals to controller slots."""
        if not self.view:
            return

        # Header signals
        self.view.sig_export.connect(self._handle_export)
        self.view.sig_print.connect(self._handle_print)

        # Toolbar signals
        self.view.sig_add_from_catalog.connect(self._handle_add_from_catalog)
        self.view.sig_add_custom.connect(self._handle_add_custom)
        self.view.sig_search_changed.connect(self._handle_search_changed)
        self.view.sig_view_mode_changed.connect(self._handle_view_mode_changed)

        # Cabinet card signals
        self.view.sig_cabinet_qty_changed.connect(self._handle_qty_changed)
        self.view.sig_cabinet_edit.connect(self._handle_cabinet_edit)
        self.view.sig_cabinet_duplicate.connect(self._handle_cabinet_duplicate)
        self.view.sig_cabinet_delete.connect(self._handle_cabinet_delete)
        self.view.sig_cabinet_selected.connect(self._handle_cabinet_selected)

        # Client sidebar signals
        self.view.sig_client_save.connect(self._handle_client_save)

        logger.debug("All view signals wired to controller")

    def _load_project_data(self) -> None:
        """Load project data from database with resilience for missing related data."""
        try:
            # Load cabinets with safe handling
            raw_cabinets = self.project_service.list_cabinets(self.project.id)
            self.cabinets = []

            for cabinet in raw_cabinets:
                try:
                    # Validate essential cabinet data with safe fallbacks
                    cabinet_id = getattr(cabinet, "id", None)
                    if cabinet_id is None:
                        logger.warning("Skipping cabinet with no ID")
                        continue

                    # Safe quantity handling
                    quantity = getattr(cabinet, "quantity", 1)
                    try:
                        quantity = max(1, int(quantity)) if quantity is not None else 1
                    except (ValueError, TypeError):
                        quantity = 1

                    # Safe sequence handling
                    sequence = getattr(
                        cabinet, "sequence_number", len(self.cabinets) + 1
                    )
                    try:
                        sequence = (
                            int(sequence)
                            if sequence is not None
                            else len(self.cabinets) + 1
                        )
                    except (ValueError, TypeError):
                        sequence = len(self.cabinets) + 1

                    # Add to list if basic validation passes
                    self.cabinets.append(cabinet)
                    logger.debug(
                        f"Loaded cabinet {cabinet_id} (seq: {sequence}, qty: {quantity})"
                    )

                except Exception as cabinet_error:
                    logger.warning(f"Skipping problematic cabinet: {cabinet_error}")
                    # Continue with other cabinets
                    continue

            logger.debug(f"Loaded {len(self.cabinets)} valid cabinets")

            # Populate header info with safe fallbacks
            if self.view:
                try:
                    project_name = getattr(self.project, "name", "Projekt")
                    order_number = getattr(self.project, "order_number", "N/A")
                    kitchen_type = getattr(
                        self.project, "kitchen_type", "Nie określono"
                    )

                    # Format created date
                    created_at = getattr(self.project, "created_at", None)
                    created_date = ""
                    if created_at:
                        created_date = created_at.strftime("%Y-%m-%d %H:%M")

                    self.view.set_header_info(
                        project_name, f"Projekt #{order_number}", kitchen_type
                    )

                    # Also update header bar directly with all info including date
                    if hasattr(self.view, "header_bar") and self.view.header_bar:
                        self.view.header_bar.set_project_info(
                            title=project_name,
                            order_number=order_number,
                            kitchen_type=kitchen_type,
                            created_date=created_date,
                        )

                    # Populate client info with safe fallbacks
                    client_name = (
                        getattr(self.project, "client_name", None) or "Nie określono"
                    )
                    client_address = (
                        getattr(self.project, "client_address", None) or "Nie określono"
                    )
                    client_phone = (
                        getattr(self.project, "client_phone", None) or "Nie określono"
                    )
                    client_email = (
                        getattr(self.project, "client_email", None) or "Nie określono"
                    )

                    client_info = f"""
                    Klient: {client_name}
                    Adres: {client_address}
                    Telefon: {client_phone}
                    Email: {client_email}
                    """.strip()

                    display_name = (
                        client_name if client_name != "Nie określono" else "Klient"
                    )
                    self.view.set_client_info(display_name, client_info)

                except Exception as view_error:
                    logger.warning(
                        f"Error updating view with project data: {view_error}"
                    )

        except Exception as e:
            logger.error(f"Error loading project data: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas ładowania danych: {e}")

    def _setup_table_model(self) -> None:
        """Setup table model and proxy for cabinet display."""
        try:
            # Create cabinet table model
            self.cabinet_model = CabinetTableModel(self.cabinets)

            # Create proxy for filtering/sorting
            self.cabinet_proxy = make_proxy(self.cabinet_model)

            # Connect model signals
            self.cabinet_model.cabinet_data_changed.connect(
                self._handle_model_data_changed
            )

            # Install model in view (if view supports table mode)
            if self.view and hasattr(self.view, "set_table_model"):
                self.view.set_table_model(self.cabinet_proxy)

                # Setup color chip delegates
                if hasattr(self.view, "get_table_view"):
                    table_view = self.view.get_table_view()
                    if table_view:
                        setup_color_chip_delegate(table_view, self.cabinet_model)

            # Update card view with cabinet data
            self._update_card_view()

            logger.debug("Table model and proxy setup complete")

        except Exception as e:
            logger.error(f"Error setting up table model: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas konfiguracji tabeli: {e}")

    def _update_card_view(self) -> None:
        """Update the card view with current cabinet data."""
        if self.view:
            # Clear existing cards and add new ones
            self.view.clear_cabinet_cards()

            for cabinet in self.cabinets:
                # Create cabinet card data
                card_data = {
                    "id": cabinet.id,
                    "name": cabinet.cabinet_type.nazwa
                    if cabinet.cabinet_type
                    else "Niestandardowy",
                    "body_color": cabinet.body_color or "Nie określono",
                    "front_color": cabinet.front_color or "Nie określono",
                    "handle_type": cabinet.handle_type or "Nie określono",
                    "quantity": cabinet.quantity,
                    "is_custom": cabinet.type_id is None,
                    "sequence": cabinet.sequence_number,
                }

                self.view.add_cabinet_card(card_data)

    def _restore_ui_state(self) -> None:
        """Restore UI state from settings."""
        try:
            # Restore view mode
            view_mode = self.ui_state.get_view_mode("cards")
            if self.view:
                self.view.set_view_mode(view_mode)

            # Restore splitters if available
            if hasattr(self.view, "get_main_splitter"):
                main_splitter = self.view.get_main_splitter()
                if main_splitter:
                    self.ui_state.restore_splitter("main", main_splitter)

            # Restore table column widths if available
            if hasattr(self.view, "get_table_view"):
                table_view = self.view.get_table_view()
                if table_view:
                    self.ui_state.restore_column_widths("cabinets", table_view)

            logger.debug("UI state restored")

        except Exception as e:
            logger.error(f"Error restoring UI state: {e}")

    def _save_ui_state(self) -> None:
        """Save current UI state to settings."""
        try:
            if not self.view:
                return

            # Save view mode
            current_mode = self.view.get_current_view_mode()
            self.ui_state.set_view_mode(current_mode)

            # Save splitters if available
            if hasattr(self.view, "get_main_splitter"):
                main_splitter = self.view.get_main_splitter()
                if main_splitter:
                    self.ui_state.save_splitter("main", main_splitter)

            # Save table column widths if available
            if hasattr(self.view, "get_table_view"):
                table_view = self.view.get_table_view()
                if table_view:
                    self.ui_state.save_column_widths("cabinets", table_view)

            logger.debug("UI state saved")

        except Exception as e:
            logger.error(f"Error saving UI state: {e}")

    # Signal handlers
    def _handle_export(self) -> None:
        """Handle export request."""
        try:
            # Generate report and get file path
            report_path = self.report_generator.generate_project_report(
                self.project, format_type="pdf"
            )

            if report_path:
                # Open the exported file
                success = open_or_print(report_path, "open")
                if success and self.view:
                    self.view.show_success_banner(
                        "Raport został wygenerowany i otwarty"
                    )
                elif self.view:
                    self.view.show_error_banner("Nie udało się otworzyć raportu")
            else:
                if self.view:
                    self.view.show_error_banner("Nie udało się wygenerować raportu")

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas eksportu: {e}")

    def _handle_print(self) -> None:
        """Handle print request."""
        try:
            # Generate report for printing
            report_path = self.report_generator.generate_project_report(
                self.project, format_type="pdf"
            )

            if report_path:
                # Print the file
                success = open_or_print(report_path, "print")
                if success and self.view:
                    self.view.show_success_banner("Raport został wysłany do drukarki")
                elif self.view:
                    self.view.show_error_banner("Nie udało się wydrukować raportu")
            else:
                if self.view:
                    self.view.show_error_banner("Nie udało się wygenerować raportu")

        except Exception as e:
            logger.error(f"Error printing report: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas drukowania: {e}")

    def _handle_add_from_catalog(self) -> None:
        """Handle add cabinet from catalog request."""
        try:
            dialog = AddCabinetDialog(self.session, self.project, None, self.view)
            if dialog.exec() == QMessageBox.Ok:
                # Refresh cabinet data
                self._load_project_data()
                self._update_card_view()

                if self.view:
                    self.view.show_success_banner("Szafka została dodana z katalogu")

        except Exception as e:
            logger.error(f"Error adding cabinet from catalog: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas dodawania szafki: {e}")

    def _handle_add_custom(self) -> None:
        """Handle add custom cabinet request."""
        try:
            dialog = AdhocCabinetDialog(self.session, self.project, None, self.view)
            if dialog.exec() == QMessageBox.Ok:
                # Refresh cabinet data
                self._load_project_data()
                self._update_card_view()

                if self.view:
                    self.view.show_success_banner(
                        "Niestandardowa szafka została dodana"
                    )

        except Exception as e:
            logger.error(f"Error adding custom cabinet: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas dodawania szafki: {e}")

    def _handle_search_changed(self, search_text: str) -> None:
        """Handle search text change."""
        try:
            if self.cabinet_proxy:
                self.cabinet_proxy.set_search_filter(search_text)

                # Update card grid empty state if applicable
                card_grid = self.view.get_card_grid() if self.view else None
                if card_grid:
                    card_grid.update_search_filter(search_text)

                logger.debug(f"Applied search filter: '{search_text}'")

        except Exception as e:
            logger.error(f"Error applying search filter: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas wyszukiwania: {e}")

    def _handle_view_mode_changed(self, mode: str) -> None:
        """Handle view mode change."""
        try:
            # Save the view mode preference
            self.ui_state.set_view_mode(mode)
            logger.debug(f"View mode changed to: {mode}")

        except Exception as e:
            logger.error(f"Error changing view mode: {e}")

    def _handle_qty_changed(self, cabinet_id: int, new_quantity: int) -> None:
        """Handle cabinet quantity change."""
        try:
            # Update cabinet in database
            updated_cabinet = self.project_service.update_cabinet(
                cabinet_id, quantity=new_quantity
            )

            if updated_cabinet:
                # Update local data
                for i, cabinet in enumerate(self.cabinets):
                    if cabinet.id == cabinet_id:
                        self.cabinets[i] = updated_cabinet
                        break

                # Update model if available
                if self.cabinet_model:
                    self.cabinet_model.set_rows(self.cabinets)

                if self.view:
                    self.view.show_success_banner(
                        f"Ilość została zaktualizowana na {new_quantity}"
                    )

                logger.debug(f"Updated cabinet {cabinet_id} quantity to {new_quantity}")
            else:
                if self.view:
                    self.view.show_error_banner("Nie udało się zaktualizować ilości")

        except Exception as e:
            logger.error(f"Error updating cabinet quantity: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas aktualizacji ilości: {e}")

    def _handle_cabinet_edit(self, cabinet_id: int) -> None:
        """Handle cabinet edit request."""
        try:
            # Find the cabinet
            cabinet = None
            for c in self.cabinets:
                if c.id == cabinet_id:
                    cabinet = c
                    break

            if not cabinet:
                if self.view:
                    self.view.show_error_banner("Nie znaleziono szafki do edycji")
                return

            # Open appropriate dialog based on cabinet type
            if cabinet.type_id is None:
                # Custom cabinet - use adhoc dialog
                dialog = AdhocCabinetDialog(
                    self.session, self.project, cabinet_id, self.view
                )
                dialog.load_cabinet_data(cabinet_id)
            else:
                # Catalog cabinet - could open edit version of add dialog
                # For now, show message that editing catalog cabinets is not supported
                if self.view:
                    self.view.show_info_banner(
                        "Edycja szafek katalogowych będzie dostępna wkrótce"
                    )
                return

            if dialog.exec() == QMessageBox.Ok:
                # Refresh data
                self._load_project_data()
                self._update_card_view()

                if self.view:
                    self.view.show_success_banner("Szafka została zaktualizowana")

        except Exception as e:
            logger.error(f"Error editing cabinet: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas edycji szafki: {e}")

    def _handle_cabinet_duplicate(self, cabinet_id: int) -> None:
        """Handle cabinet duplicate request."""
        try:
            # Find the original cabinet
            original_cabinet = None
            for c in self.cabinets:
                if c.id == cabinet_id:
                    original_cabinet = c
                    break

            if not original_cabinet:
                if self.view:
                    self.view.show_error_banner("Nie znaleziono szafki do duplikacji")
                return

            # Get next sequence number
            next_seq = self.project_service.get_next_cabinet_sequence(self.project.id)

            # Create duplicate cabinet
            if original_cabinet.type_id is None:
                # Custom cabinet
                new_cabinet = self.project_service.add_cabinet(
                    self.project.id,
                    cabinet_type_id=None,
                    quantity=original_cabinet.quantity,
                    sequence_number=next_seq,
                    body_color=original_cabinet.body_color,
                    front_color=original_cabinet.front_color,
                    handle_type=original_cabinet.handle_type,
                    # Add other custom cabinet fields as needed
                )
            else:
                # Catalog cabinet
                new_cabinet = self.project_service.add_cabinet(
                    self.project.id,
                    cabinet_type_id=original_cabinet.type_id,
                    quantity=original_cabinet.quantity,
                    sequence_number=next_seq,
                    body_color=original_cabinet.body_color,
                    front_color=original_cabinet.front_color,
                    handle_type=original_cabinet.handle_type,
                )

            if new_cabinet:
                # Refresh data
                self._load_project_data()
                self._update_card_view()

                if self.view:
                    self.view.show_success_banner("Szafka została zduplikowana")
            else:
                if self.view:
                    self.view.show_error_banner("Nie udało się zduplikować szafki")

        except Exception as e:
            logger.error(f"Error duplicating cabinet: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas duplikacji szafki: {e}")

    def _handle_cabinet_delete(self, cabinet_id: int) -> None:
        """Handle cabinet delete request."""
        try:
            # Confirm deletion
            reply = QMessageBox.question(
                self.view,
                "Potwierdź usunięcie",
                "Czy na pewno chcesz usunąć tę szafkę?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                success = self.project_service.delete_cabinet(cabinet_id)

                if success:
                    # Refresh data
                    self._load_project_data()
                    self._update_card_view()

                    if self.view:
                        self.view.show_success_banner("Szafka została usunięta")
                else:
                    if self.view:
                        self.view.show_error_banner("Nie udało się usunąć szafki")

        except Exception as e:
            logger.error(f"Error deleting cabinet: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas usuwania szafki: {e}")

    def _handle_cabinet_selected(self, cabinet_id: int) -> None:
        """Handle cabinet selection."""
        try:
            logger.debug(f"Cabinet selected: {cabinet_id}")
            # Could implement selection highlighting or other features

        except Exception as e:
            logger.error(f"Error handling cabinet selection: {e}")

    def _handle_client_save(self, client_data: dict) -> None:
        """Handle client information save."""
        try:
            # Update project with client data
            updated_project = self.project_service.update_project(
                self.project.id,
                client_name=client_data.get("name"),
                client_address=client_data.get("address"),
                client_phone=client_data.get("phone"),
                client_email=client_data.get("email"),
            )

            if updated_project:
                # Update local project object
                self.project = updated_project

                if self.view:
                    self.view.show_success_banner("Dane klienta zostały zapisane")

                logger.debug("Client data saved successfully")
            else:
                if self.view:
                    self.view.show_error_banner("Nie udało się zapisać danych klienta")

        except Exception as e:
            logger.error(f"Error saving client data: {e}")
            if self.view:
                self.view.show_error_banner(
                    f"Błąd podczas zapisywania danych klienta: {e}"
                )

    def _handle_model_data_changed(
        self, cabinet_id: int, column_name: str, new_value
    ) -> None:
        """Handle data changes from the table model."""
        try:
            if column_name == "quantity":
                self._handle_qty_changed(cabinet_id, new_value)

        except Exception as e:
            logger.error(f"Error handling model data change: {e}")

    def _handle_cabinet_reorder(self, old_index: int, new_index: int) -> None:
        """Handle cabinet reordering from drag-drop."""
        try:
            # The model should have already updated the order via moveRows
            # Now we need to persist the new sequence numbers

            # Update sequence numbers in database
            for i, cabinet in enumerate(self.cabinets):
                new_seq = i + 1
                if cabinet.sequence_number != new_seq:
                    self.project_service.update_cabinet(
                        cabinet.id, sequence_number=new_seq
                    )
                    cabinet.sequence_number = new_seq

            if self.view:
                self.view.show_success_banner("Kolejność szafek została zaktualizowana")

            logger.debug(f"Reordered cabinet from {old_index} to {new_index}")

        except Exception as e:
            logger.error(f"Error handling cabinet reorder: {e}")
            if self.view:
                self.view.show_error_banner(f"Błąd podczas zmiany kolejności: {e}")

    def close_event(self) -> None:
        """Handle controller cleanup when view is closing."""
        try:
            # Save UI state before closing
            self._save_ui_state()

            logger.debug("Controller cleanup completed")

        except Exception as e:
            logger.error(f"Error during controller cleanup: {e}")
