"""
Unified Cabinet Catalog Window.

A single window that supports both catalog management and project integration.
Provides browsing, searching, creating, editing, and adding cabinets to projects.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import Signal, QTimer

from src.gui.resources.styles import get_theme, PRIMARY
from src.gui.cabinet_editor import CabinetEditorDialog
from src.services.catalog_service import CatalogService
from src.gui.resources.resources import get_icon
from src.services.project_service import ProjectService
from src.services.color_palette_service import ColorPaletteService
from src.services.settings_service import SettingsService
from src.db_schema.orm_models import Project

from .browser_widget import CatalogBrowserWidget
from .manage_toolbar import ManageToolbar
from .add_footer import AddFooter


class CatalogWindow(QDialog):
    """Unified catalog window for browsing and managing cabinet types."""

    # Signals
    sig_added_to_project = Signal(
        int, int, int, dict
    )  # cabinet_type_id, project_id, quantity, options
    sig_catalog_changed = Signal()  # emitted after create/update/delete
    SEARCH_DEBOUNCE_MS = 300

    def __init__(
        self,
        catalog_service: CatalogService,
        project_service: Optional[ProjectService] = None,
        initial_mode: str = "add",
        target_project: Optional[Project] = None,
        parent=None,
    ):
        super().__init__(parent)

        self.catalog_service = catalog_service
        self.project_service = project_service
        self.target_project = target_project
        self.current_mode = initial_mode
        self.color_service = None
        self.is_dark_mode = False
        self._search_debounce_timer = QTimer(self)
        self._search_debounce_timer.setSingleShot(True)
        self._search_debounce_timer.setInterval(self.SEARCH_DEBOUNCE_MS)

        if getattr(self.catalog_service, "session", None) is not None:
            self.color_service = ColorPaletteService(self.catalog_service.session)
            self.color_service.ensure_seeded()
            self.color_service.sync_runtime_color_map()
            try:
                self.is_dark_mode = bool(
                    SettingsService(self.catalog_service.session).get_setting_value(
                        "dark_mode", False
                    )
                )
            except Exception:
                self.is_dark_mode = False

        self._setup_ui()
        self._setup_connections()
        self._apply_styles()
        self._update_mode_ui()

        self.setModal(True)
        self.setMinimumSize(900, 700)
        self.setWindowTitle("Katalog szafek")
        self.setWindowIcon(get_icon("catalog"))

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with search and mode toggle
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setMinimumHeight(60)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 8, 16, 8)

        # Search section
        search_label = QLabel("Szukaj:")
        header_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj typów szafek...")
        self.search_edit.setMinimumWidth(240)
        self.search_edit.setMaximumWidth(480)
        header_layout.addWidget(self.search_edit)

        # Spacer
        header_layout.addStretch()

        layout.addWidget(header_frame)

        # Manage toolbar
        self.manage_toolbar = ManageToolbar(is_dark_mode=self.is_dark_mode)
        layout.addWidget(self.manage_toolbar)

        # Browser area
        self.browser_widget = CatalogBrowserWidget(
            self.catalog_service, is_dark_mode=self.is_dark_mode
        )
        layout.addWidget(self.browser_widget)

        # Add footer
        self.add_footer = AddFooter(
            color_service=self.color_service,
            is_dark_mode=self.is_dark_mode,
        )
        layout.addWidget(self.add_footer)

    def _setup_connections(self):
        """Setup signal connections."""
        # Search
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.search_edit.returnPressed.connect(self._apply_search_now)
        self._search_debounce_timer.timeout.connect(self._apply_search_now)

        # Browser
        self.browser_widget.sig_item_activated.connect(self._on_item_activated)
        self.browser_widget.sig_selection_changed.connect(self._on_selection_changed)

        # Manage toolbar
        self.manage_toolbar.sig_new.connect(self._on_new)
        self.manage_toolbar.sig_edit.connect(self._on_edit)
        self.manage_toolbar.sig_duplicate.connect(self._on_duplicate)
        self.manage_toolbar.sig_delete.connect(self._on_delete)

        # Add footer
        self.add_footer.sig_add_to_project.connect(self._on_add_clicked)

    def _apply_styles(self):
        """Apply styling to the window."""
        label_color = "#E0E0E0" if self.is_dark_mode else "#333333"
        self.setStyleSheet(
            get_theme(self.is_dark_mode)
            + f"""
            QFrame#headerFrame {{
                border-bottom: 1px solid palette(mid);
            }}
            QLineEdit {{
                padding: 8px;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border-color: {PRIMARY};
            }}
            QRadioButton {{
                font-size: 10pt;
                padding: 4px 8px;
                margin: 0 4px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #D0D0D0;
                background-color: white;
            }}
            QRadioButton::indicator:checked {{
                background-color: {PRIMARY};
                border-color: {PRIMARY};
            }}
            QRadioButton::indicator:checked {{
                background-color: {PRIMARY};
                border: 2px solid {PRIMARY};
                border-radius: 6px;
            }}
            QLabel {{
                font-size: 10pt;
                color: {label_color};
            }}
        """
        )

    def _update_mode_ui(self):
        """Update UI based on current mode and project availability."""
        has_project = self.target_project is not None
        has_selection = self.browser_widget.current_item_id() is not None

        # Add footer is enabled only if we have a project and selection
        if has_project and has_selection:
            self.add_footer.set_enabled(True)
        else:
            tooltip = "Otwórz z projektu, aby dodać" if not has_project else ""
            self.add_footer.set_enabled(False, tooltip)

        # Manage toolbar is always available but depends on selection for some actions
        self.manage_toolbar.set_enabled_for_selection(has_selection)

    def _on_search_changed(self, _text: str):
        """Handle search text change."""
        self._search_debounce_timer.start()

    def _apply_search_now(self):
        """Apply current search text immediately."""
        self._search_debounce_timer.stop()
        self.browser_widget.set_query(self.search_edit.text())

    def _on_item_activated(self, cabinet_type_id: int):
        """Handle item activation (double-click)."""
        if self.current_mode == "add" and self.target_project:
            # Quick add mode
            self._add_to_project(cabinet_type_id)
        else:
            # Manage mode - open editor
            self._edit_cabinet_type(cabinet_type_id)

    def _on_selection_changed(self, has_selection: bool):
        """Handle selection change."""
        self._update_mode_ui()

    def _on_add_clicked(self):
        """Handle add button click."""
        cabinet_type_id = self.browser_widget.current_item_id()
        if cabinet_type_id and self.target_project:
            self._add_to_project(cabinet_type_id)

    def _on_new(self):
        """Handle new cabinet type."""
        try:
            from src.gui.dialogs.add_cabinet_dialog import AddCabinetDialog
            from src.services.accessory_service import AccessoryService

            # Create accessory service for the dialog
            accessory_service = AccessoryService(self.catalog_service.session)

            # Create and show the add cabinet dialog
            dialog = AddCabinetDialog(
                catalog_service=self.catalog_service,
                accessory_service=accessory_service,
                is_dark_mode=self.is_dark_mode,
                parent=self,
            )

            # Show the dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Refresh the browser to show the new cabinet
                self.browser_widget.refresh()
                self.sig_catalog_changed.emit()

        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się otworzyć edytora: {str(e)}"
            )

    def _on_edit(self):
        """Handle edit cabinet type."""
        cabinet_type_id = self.browser_widget.current_item_id()
        if cabinet_type_id:
            self._edit_cabinet_type(cabinet_type_id)

    def _on_duplicate(self):
        """Handle duplicate cabinet type."""
        cabinet_type_id = self.browser_widget.current_item_id()
        if not cabinet_type_id:
            return

        item = self.browser_widget.current_item()
        if not item:
            return

        try:
            # Duplicate the template using the service
            new_template = self.catalog_service.cabinet_type_service.duplicate_template(
                cabinet_type_id
            )
            if new_template:
                self.browser_widget.refresh()
                self.sig_catalog_changed.emit()
                QMessageBox.information(
                    self,
                    "Sukces",
                    f"Typ szafki '{item.name}' został zduplikowany jako '{new_template.name}'.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ostrzeżenie",
                    "Nie udało się zduplikować typu szafki.",
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zduplikować typu szafki: {str(e)}"
            )

    def _on_delete(self):
        """Handle delete cabinet type."""
        cabinet_type_id = self.browser_widget.current_item_id()
        if not cabinet_type_id:
            return

        item = self.browser_widget.current_item()
        if not item:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Potwierdzenie usunięcia",
            f"Czy na pewno chcesz usunąć '{item.name}'?\n\nTej operacji nie można cofnąć.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.catalog_service.delete_type(cabinet_type_id)
                if success:
                    self.browser_widget.refresh()
                    self.sig_catalog_changed.emit()
                    QMessageBox.information(
                        self,
                        "Sukces",
                        f"Typ szafki '{item.name}' został usunięty.",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Ostrzeżenie",
                        "Nie udało się usunąć typu szafki (może być używany).",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Błąd", f"Nie udało się usunąć typu szafki: {str(e)}"
                )

    def _edit_cabinet_type(self, cabinet_type_id: int):
        """Open editor for cabinet type."""
        try:
            # Get the actual cabinet type object for editing
            cabinet_type = self.catalog_service.cabinet_type_service.get_template(
                cabinet_type_id
            )
            if not cabinet_type:
                QMessageBox.warning(self, "Ostrzeżenie", "Nie znaleziono typu szafki")
                return

            # Open unified editor dialog in type mode
            editor = CabinetEditorDialog(
                catalog_service=self.catalog_service,
                project_service=None,  # Not needed for type editing
                color_service=self.color_service,
                is_dark_mode=self.is_dark_mode,
                parent=self,
            )
            editor.load_type(cabinet_type)

            if editor.exec() == QDialog.DialogCode.Accepted:
                self.browser_widget.refresh()
                self.sig_catalog_changed.emit()

        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się otworzyć edytora: {str(e)}"
            )

    def _add_to_project(self, cabinet_type_id: int):
        """Add cabinet type to project."""
        if not self.project_service or not self.target_project:
            return

        try:
            # Get quantity and options from footer
            quantity, options = self.add_footer.values()

            # Get next sequence number
            sequence_number = self.project_service.get_next_cabinet_sequence(
                self.target_project.id
            )

            # Add cabinet to project
            self.project_service.add_cabinet(
                project_id=self.target_project.id,
                sequence_number=sequence_number,
                type_id=cabinet_type_id,
                quantity=quantity,
                body_color=options["body_color"],
                front_color=options["front_color"],
                handle_type=options["handle_type"],
            )

            # Store data for signal emission after dialog closes
            self._pending_add_data = (
                cabinet_type_id,
                self.target_project.id,
                quantity,
                options,
            )

            # Close the dialog first - signal will be emitted in done()
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się dodać szafki do projektu: {str(e)}"
            )

    def done(self, result):
        """Override done to emit signal after dialog is closed."""
        # Emit pending signal if any
        if hasattr(self, "_pending_add_data") and self._pending_add_data:
            data = self._pending_add_data
            self._pending_add_data = None
            # Use QTimer to defer signal emission to after dialog is fully closed
            QTimer.singleShot(0, lambda: self.sig_added_to_project.emit(*data))
        super().done(result)
