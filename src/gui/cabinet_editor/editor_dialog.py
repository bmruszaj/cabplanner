"""
Unified cabinet editor dialog for both project instances and catalog types.

This dialog provides a tabbed interface with preview panel and form editing.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QMessageBox,
)
from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtGui import QFont

from src.gui.resources.resources import get_icon
from src.gui.resources.styles import get_theme, PRIMARY
from src.services.catalog_service import CatalogService
from src.services.project_service import ProjectService

from .instance_form import InstanceForm
from .parts_form import PartsForm
from .accessories_form import AccessoriesForm


class CabinetEditorDialog(QDialog):
    """Unified editor for cabinet instances and types."""

    # Signals
    sig_saved = Signal()  # Emitted when data is saved

    def __init__(
        self,
        catalog_service: CatalogService,
        project_service: ProjectService = None,
        parent=None,
    ):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self.project_service = project_service

        self.cabinet_type = None
        self.project_instance = None
        self.mode = None  # 'instance' or 'type'

        self._setup_ui()
        self._setup_connections()
        self._apply_styles()
        self.setModal(True)

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Edytor szafek")
        self.setWindowIcon(get_icon("cabinet"))
        self.resize(900, 750)
        self.setMinimumSize(800, 600)
        # Enable window resizing and minimize/maximize buttons
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)

        # Position window at top of screen with small margin
        self._position_at_top()

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header with title and subtitle
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)

        self.title_label = QLabel("Edytor szafek")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)

        # Editable name field (visible only in type mode)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nazwa szafki...")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                font-size: 12pt;
                font-weight: bold;
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
            }
            QLineEdit:focus {
                border-color: #0A766C;
            }
        """)
        self.name_edit.hide()  # Hidden by default
        header_layout.addWidget(self.name_edit)

        self.subtitle_label = QLabel("Wybierz element do edycji")
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.subtitle_label)

        layout.addWidget(header_frame)

        # Main content area with preview and forms
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Left side: Cabinet drawing panel (1/3 width)
        self.drawing_panel = QFrame()
        self.drawing_panel.setFrameStyle(QFrame.StyledPanel)
        self.drawing_panel.setMinimumWidth(280)
        self.drawing_panel.setMaximumWidth(400)

        drawing_layout = QVBoxLayout(self.drawing_panel)
        drawing_layout.setContentsMargins(16, 16, 16, 16)

        # Drawing panel header
        drawing_header = QLabel("Rysunek szafki")
        drawing_header_font = QFont()
        drawing_header_font.setPointSize(12)
        drawing_header_font.setBold(True)
        drawing_header.setFont(drawing_header_font)
        drawing_layout.addWidget(drawing_header)

        # Placeholder for cabinet drawing
        self.drawing_placeholder = QLabel(
            "Miejsce na rysunek szafki\n(bazowany na wymiarach)"
        )
        self.drawing_placeholder.setAlignment(Qt.AlignCenter)
        self.drawing_placeholder.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px;
                background-color: #f9f9f9;
            }
        """)
        drawing_layout.addWidget(self.drawing_placeholder)

        drawing_layout.addStretch()
        content_layout.addWidget(self.drawing_panel)

        # Right side: Tabbed forms (2/3 width)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # Instance tab
        self.instance_form = InstanceForm()
        self.tab_widget.addTab(
            self.instance_form, get_icon("project"), "Instancja w projekcie"
        )

        # Parts tab
        self.parts_form = PartsForm(
            catalog_service=self.catalog_service, project_service=self.project_service
        )
        self.tab_widget.addTab(self.parts_form, get_icon("parts"), "Części")

        # Accessories tab
        self.accessories_form = AccessoriesForm(
            catalog_service=self.catalog_service, project_service=self.project_service
        )
        self.tab_widget.addTab(
            self.accessories_form, get_icon("accessories"), "Akcesoria"
        )

        content_layout.addWidget(self.tab_widget)
        layout.addLayout(content_layout)

        # Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        # Left side status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 9pt;")
        buttons_layout.addWidget(self.status_label)

        buttons_layout.addStretch()

        # Right side buttons
        icon_size = int(self.fontMetrics().height() * 0.8)

        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.setIcon(get_icon("cancel"))
        self.cancel_button.setIconSize(QSize(icon_size, icon_size))
        buttons_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Zapisz")
        self.save_button.setIcon(get_icon("save"))
        self.save_button.setIconSize(QSize(icon_size, icon_size))
        self.save_button.setDefault(True)
        buttons_layout.addWidget(self.save_button)

        layout.addLayout(buttons_layout)

        # Initial state
        self._update_buttons()

    def _setup_connections(self):
        """Setup signal connections."""
        # Tab switching
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Form dirty tracking
        self.instance_form.sig_dirty_changed.connect(self._on_dirty_changed)
        self.parts_form.sig_dirty_changed.connect(self._on_dirty_changed)
        self.accessories_form.sig_dirty_changed.connect(self._on_dirty_changed)

        # Name edit tracking
        self.name_edit.textChanged.connect(self._on_name_changed)

        # Buttons
        self.cancel_button.clicked.connect(self._cancel)
        self.save_button.clicked.connect(self._save)

    def _position_at_top(self):
        """Position the dialog near the top of the screen with small margin."""
        from PySide6.QtGui import QGuiApplication

        # Get the primary screen
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            # Position at top with 20px margin
            top_margin = 20
            left_center = (
                screen_geometry.left() + (screen_geometry.width() - self.width()) // 2
            )
            self.move(left_center, screen_geometry.top() + top_margin)

    def _apply_styles(self):
        """Apply visual styling."""
        get_theme()

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f8f9fa;
            }}
            QFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
            QTabWidget::pane {{
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                margin-top: -1px;
            }}
            QTabWidget QTabBar::tab {{
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 9pt;
            }}
            QTabWidget QTabBar::tab:selected {{
                background-color: white;
                color: #333333;
                border-bottom: 1px solid white;
            }}
            QTabWidget QTabBar::tab:hover:!selected {{
                background-color: #e8e8e8;
                color: #333333;
            }}
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 9pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
            QPushButton#cancel_button {{
                background-color: #757575;
            }}
        """)

        # Set object names for styling
        self.cancel_button.setObjectName("cancel_button")

    def _on_tab_changed(self, index):
        """Handle tab switching."""
        current_tab = self.tab_widget.widget(index)

        if current_tab == self.instance_form:
            self.mode = "instance"
            self.subtitle_label.setText("Edycja instancji szafki w projekcie")
            # Update drawing
            self._update_drawing()

        elif current_tab == self.parts_form:
            self.mode = "parts"
            self.subtitle_label.setText("Edycja części szafki")
            # Update drawing
            self._update_drawing()

        elif current_tab == self.accessories_form:
            self.mode = "accessories"
            self.subtitle_label.setText("Edycja akcesoriów szafki")
            # Update drawing
            self._update_drawing()

        self._update_buttons()

    def _on_dirty_changed(self, is_dirty):
        """Handle dirty state changes."""
        self._update_buttons()

        if is_dirty:
            self.status_label.setText("Są niezapisane zmiany")
        else:
            self.status_label.setText("")

    def _update_buttons(self):
        """Update button states based on current state."""
        current_form = self._get_current_form()

        # We have data if we have either a cabinet type or a project instance
        has_data = self.cabinet_type is not None or self.project_instance is not None
        is_dirty = current_form.is_dirty() if current_form else False
        is_valid = current_form.is_valid() if current_form else True

        # Check if name was changed (in type mode)
        name_changed = self._is_name_changed()
        name_valid = len(self.name_edit.text().strip()) > 0

        # Enable save if: has data AND (form is dirty+valid OR name changed+valid)
        can_save = has_data and (
            (is_dirty and is_valid) or (name_changed and name_valid)
        )

        self.save_button.setEnabled(can_save)

    def _is_name_changed(self) -> bool:
        """Check if the name field was modified."""
        # We're in type-editing mode if we have cabinet_type but no project_instance
        if not self.cabinet_type or self.project_instance is not None:
            return False
        return self.name_edit.text().strip() != self.cabinet_type.name

    def _on_name_changed(self):
        """Handle name field text change."""
        self._update_buttons()

    def _get_current_form(self):
        """Get currently active form widget."""
        current_widget = self.tab_widget.currentWidget()
        if current_widget == self.instance_form:
            return self.instance_form
        elif current_widget == self.parts_form:
            return self.parts_form
        elif current_widget == self.accessories_form:
            return self.accessories_form
        return None

    def _update_drawing(self):
        """Update cabinet drawing based on current dimensions."""
        if not self.cabinet_type:
            self.drawing_placeholder.setText("Miejsce na rysunek szafki\n(brak danych)")
            return

        # Calculate dimensions from parts
        width = height = 0
        if hasattr(self.cabinet_type, "parts") and self.cabinet_type.parts:
            for part in self.cabinet_type.parts:
                width = max(width, part.width_mm or 0)
                height = max(height, part.height_mm or 0)

        # Use kitchen type to determine depth (standard cabinet depths)
        depth = (
            560 if self.cabinet_type.kitchen_type in ["LOFT", "PARIS", "WINO"] else 320
        )

        if width and height:
            self.drawing_placeholder.setText(
                f"Rysunek szafki\n"
                f"(Implementacja rysunku w przyszłości)"
            )
        else:
            self.drawing_placeholder.setText(
                "Miejsce na rysunek szafki\n(brak wymiarów)"
            )

    def _save(self):
        """Save changes and close dialog."""
        if self._save_all_forms():
            self.sig_saved.emit()
            self.accept()

    def _cancel(self):
        """Cancel editing with dirty check."""
        # Check for unsaved changes in all forms
        has_unsaved = (
            self.instance_form.is_dirty()
            or self.parts_form.is_dirty()
            or self.accessories_form.is_dirty()
        )

        if has_unsaved:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Niezapisane zmiany")
            msg_box.setText(
                "Masz niezapisane zmiany. Czy na pewno chcesz zamknąć okno?"
            )
            msg_box.setIcon(QMessageBox.Question)

            tak_button = msg_box.addButton("Tak", QMessageBox.YesRole)
            nie_button = msg_box.addButton("Nie", QMessageBox.NoRole)
            msg_box.setDefaultButton(nie_button)

            msg_box.exec()

            if msg_box.clickedButton() != tak_button:
                return

        self.reject()

    def _refresh_cabinet_data(self) -> None:
        """Reload cabinet from database and update form references."""
        if self.project_instance and self.project_service:
            refreshed = self.project_service.get_cabinet(self.project_instance.id)
            if refreshed:
                self.project_instance = refreshed
                self.parts_form.project_cabinet = refreshed
                self.accessories_form.project_cabinet = refreshed

    def _save_all_forms(self) -> bool:
        """Save all forms that have changes."""
        if self.project_instance:
            return self._save_project_instance_forms()
        elif self.cabinet_type:
            return self._save_catalog_template_forms()
        return True

    def _save_project_instance_forms(self) -> bool:
        """Save all dirty forms for project instance."""
        try:
            # Save instance form
            if self.instance_form.is_dirty():
                values = self.instance_form.values()
                updated = self.project_service.update_cabinet(
                    self.project_instance.id, **values
                )
                if not updated:
                    self._show_save_error("instancji")
                    return False
                self.project_instance = updated
                self.instance_form.reset_dirty()

            # Save parts form
            if self.parts_form.is_dirty():
                parts_changes = self.parts_form.values()
                if not self._apply_parts_changes(parts_changes):
                    self._show_save_error("części")
                    return False
                self._refresh_cabinet_data()
                self.parts_form.reset_dirty()

            # Save accessories form
            if self.accessories_form.is_dirty():
                accessories_changes = self.accessories_form.values()
                if not self._apply_accessories_changes(accessories_changes):
                    self._show_save_error("akcesoriów")
                    return False
                self._refresh_cabinet_data()
                self.accessories_form.reset_dirty()

            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Błąd zapisu", f"Nie udało się zapisać zmian:\n{str(e)}"
            )
            return False

    def _save_catalog_template_forms(self) -> bool:
        """Save all dirty forms for catalog template."""
        try:
            # Save name if changed
            new_name = self.name_edit.text().strip()
            if new_name and self.cabinet_type and new_name != self.cabinet_type.name:
                self.catalog_service.cabinet_type_service.update_template_name(
                    self.cabinet_type.id, new_name
                )

            # Parts - apply pending changes
            if self.parts_form.is_dirty():
                parts_changes = self.parts_form.values()
                if not self._apply_template_parts_changes(parts_changes):
                    self._show_save_error("części")
                    return False
                self.parts_form.reset_dirty()

            # Save accessories
            if self.accessories_form.is_dirty():
                accessories_changes = self.accessories_form.values()
                if not self._apply_template_accessories_changes(accessories_changes):
                    self._show_save_error("akcesoriów")
                    return False
                self.accessories_form.reset_dirty()

            return True

        except Exception as e:
            QMessageBox.critical(
                self, "Błąd zapisu", f"Nie udało się zapisać zmian:\n{str(e)}"
            )
            return False

    def _show_save_error(self, item_type: str) -> None:
        """Show save error message."""
        QMessageBox.critical(self, "Błąd zapisu", f"Nie udało się zapisać {item_type}.")

    def load_instance(self, cabinet_type, project_instance):
        """Load data for editing project instance."""
        self.cabinet_type = cabinet_type
        self.project_instance = project_instance
        self.mode = "instance"

        # Update title and hide name editor
        self.title_label.setText(f"Edytor: {cabinet_type.name}")
        self.name_edit.hide()
        self.subtitle_label.setText("Edycja instancji szafki w projekcie")

        # Load forms
        self.instance_form.load(project_instance, cabinet_type)
        # Load parts from project instance snapshot (not from catalog template)
        self.parts_form.load_custom_parts(
            list(project_instance.parts), project_instance
        )
        self.accessories_form.load(project_instance, cabinet_type)

        # Switch to instance tab
        self.tab_widget.setCurrentWidget(self.instance_form)

        # Update drawing
        self._update_drawing()

        # Update buttons
        self._update_buttons()

    def load_type(self, cabinet_type):
        """Load data for editing catalog type."""
        self.cabinet_type = cabinet_type
        self.project_instance = None
        self.mode = "type"

        # Update title and show name editor
        self.title_label.setText("Edytor typu szafki")
        self.name_edit.setText(cabinet_type.name)
        self.name_edit.show()
        self.subtitle_label.setText("Edycja typu szafki w katalogu")

        # Load forms
        self.parts_form.load(cabinet_type)
        self.accessories_form.load(None, cabinet_type)  # Load with catalog type only

        # Disable instance tab when editing type only
        self.tab_widget.setTabEnabled(0, False)  # Instance tab
        # Keep accessories tab enabled for catalog-level accessory management

        # Switch to parts tab (first available tab for catalog)
        self.tab_widget.setCurrentWidget(self.parts_form)

        # Update drawing
        self._update_drawing()

        # Update buttons
        self._update_buttons()

    def load_custom_instance(self, project_instance):
        """Load data for editing custom cabinet instance (type_id=NULL)."""
        self.cabinet_type = None  # No catalog type for custom cabinets
        self.project_instance = project_instance
        self.mode = "custom_instance"

        # Hide name edit for custom instances
        self.name_edit.hide()

        # Update title - try to get template name from calc_context
        template_name = "Niestandardowa"
        if hasattr(project_instance, "parts") and project_instance.parts:
            for part in project_instance.parts:
                if (
                    part.calc_context_json
                    and isinstance(part.calc_context_json, dict)
                    and "template_name" in part.calc_context_json
                ):
                    template_name = (
                        f"{part.calc_context_json['template_name']} + niestandardowa"
                    )
                    break

        self.title_label.setText(
            f"Edytor: {template_name} #{project_instance.sequence_number}"
        )
        self.subtitle_label.setText("Edycja niestandardowej szafki w projekcie")

        # Load forms - only instance form is relevant for custom cabinets
        self.instance_form.load(project_instance, None)  # No cabinet type

        # Load custom parts in parts form (they are stored in project_instance.parts as ProjectCabinetPart)
        if hasattr(project_instance, "parts") and project_instance.parts:
            # Convert ProjectCabinetPart objects to the format expected by parts form
            custom_parts_for_form = []
            for part in project_instance.parts:
                # Use the actual part object instead of SimpleNamespace to avoid missing attributes
                custom_parts_for_form.append(part)

            self.parts_form.load_custom_parts(custom_parts_for_form, project_instance)
        else:
            self.parts_form.load_custom_parts([], project_instance)

        # Load accessories (custom cabinets can still have accessories)
        self.accessories_form.load(project_instance, None)  # No cabinet type

        # Disable type tab for custom cabinets (no catalog type to edit)
        self.tab_widget.setTabEnabled(1, False)  # Type tab

        # Switch to instance tab
        self.tab_widget.setCurrentWidget(self.instance_form)

        # Update drawing
        self._update_drawing()

        # Update buttons
        self._update_buttons()

    def _apply_parts_changes(self, parts_changes) -> bool:
        """Apply pending parts changes using ProjectService."""
        try:
            if not self.project_instance or not self.project_service:
                return False

            # Check if parts_changes is a list (custom cabinet mode) or dict (regular mode)
            if isinstance(parts_changes, list):
                # Custom cabinet mode - replace all parts
                success = self.project_service.update_cabinet_parts(
                    self.project_instance.id, parts_changes
                )
                return success
            else:
                # Regular mode - apply individual changes
                # Apply parts to remove first
                for part_id in parts_changes.get("parts_to_remove", []):
                    success = self.project_service.remove_part_from_cabinet(part_id)
                    if not success:
                        return False

                # Apply parts changes (edits)
                for part_id, part_data in parts_changes.get(
                    "parts_changes", {}
                ).items():
                    success = self.project_service.update_part(part_id, part_data)
                    if not success:
                        return False

                # Apply parts to add
                for part_data in parts_changes.get("parts_to_add", []):
                    success = self.project_service.add_part_to_cabinet(
                        cabinet_id=self.project_instance.id,
                        part_name=part_data.get("part_name", ""),
                        width_mm=part_data.get("width_mm", 0),
                        height_mm=part_data.get("height_mm", 0),
                        pieces=part_data.get("pieces", 1),
                        material=part_data.get("material"),
                        wrapping=part_data.get("wrapping"),
                        comments=part_data.get("comments"),
                    )
                    if not success:
                        return False

                return True

        except Exception as e:
            print(f"Error applying parts changes: {e}")
            return False

    def _apply_accessories_changes(self, accessories_changes: dict) -> bool:
        """Apply pending accessories changes using ProjectService."""
        try:
            if not self.project_instance or not self.project_service:
                return False

            # Apply accessories to add
            for acc_data in accessories_changes.get("accessories_to_add", []):
                success = self.project_service.add_accessory_to_cabinet(
                    cabinet_id=self.project_instance.id,
                    name=acc_data["name"],
                    unit=acc_data.get("unit", "szt"),
                    count=acc_data["count"],
                )
                if not success:
                    return False

            # Apply accessories to remove
            for acc_id in accessories_changes.get("accessories_to_remove", []):
                success = self.project_service.remove_accessory_from_cabinet(acc_id)
                if not success:
                    return False

            # Apply quantity changes
            for acc_id, new_quantity in accessories_changes.get(
                "quantity_changes", {}
            ).items():
                success = self.project_service.update_accessory_quantity(
                    acc_id, new_quantity
                )
                if not success:
                    return False

            return True

        except Exception as e:
            print(f"Error applying accessories changes: {e}")
            return False

    def _apply_template_parts_changes(self, parts_changes: dict) -> bool:
        """Apply pending parts changes for catalog template."""
        try:
            if not self.cabinet_type or not self.catalog_service:
                return False

            template_service = self.catalog_service.cabinet_type_service

            # Apply parts to remove first
            for part_id in parts_changes.get("parts_to_remove", []):
                success = template_service.delete_part(part_id)
                if not success:
                    return False

            # Apply parts changes (edits)
            for part_id, part_data in parts_changes.get("parts_changes", {}).items():
                success = template_service.update_part(part_id, **part_data)
                if not success:
                    return False

            # Apply parts to add
            for part_data in parts_changes.get("parts_to_add", []):
                template_service.add_part(
                    cabinet_type_id=self.cabinet_type.id,
                    part_name=part_data.get("part_name", ""),
                    height_mm=part_data.get("height_mm", 0),
                    width_mm=part_data.get("width_mm", 0),
                    pieces=part_data.get("pieces", 1),
                    material=part_data.get("material"),
                    wrapping=part_data.get("wrapping"),
                    comments=part_data.get("comments"),
                )

            return True

        except Exception as e:
            print(f"Error applying template parts changes: {e}")
            return False

    def _apply_template_accessories_changes(self, accessories_changes: dict) -> bool:
        """Apply pending accessories changes for catalog template."""
        try:
            if not self.cabinet_type or not self.catalog_service:
                return False

            template_service = self.catalog_service.cabinet_type_service

            # Apply accessories to add
            for acc_data in accessories_changes.get("accessories_to_add", []):
                template_service.add_accessory_by_name(
                    cabinet_type_id=self.cabinet_type.id,
                    name=acc_data["name"],
                    unit=acc_data.get("unit", "szt"),
                    count=acc_data["count"],
                )

            # Apply accessories to remove
            for acc_id in accessories_changes.get("accessories_to_remove", []):
                template_service.delete_accessory(self.cabinet_type.id, acc_id)

            # Note: Quantity changes for template accessories would need
            # additional implementation in template_service if needed

            return True

        except Exception as e:
            print(f"Error applying template accessories changes: {e}")
            return False

    def closeEvent(self, event):
        """Handle window close event."""
        self._cancel()
        event.ignore()  # _cancel will accept/reject as needed
