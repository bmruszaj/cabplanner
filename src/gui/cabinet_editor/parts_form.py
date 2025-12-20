"""
Parts form for editing cabinet parts in the cabinet editor.

Handles part-level fields like dimensions, materials, quantities, etc.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QDialog,
)
from PySide6.QtCore import Signal, Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont

from src.gui.resources.resources import get_icon
from src.gui.resources.styles import get_theme, PRIMARY
from src.gui.dialogs.part_edit_dialog import PartEditDialog
from .pending_changes import PendingChanges


class PartsTableModel(QAbstractTableModel):
    """Model for displaying cabinet parts in a table view"""

    def __init__(self, parts, parent=None):
        super().__init__(parent)
        self.parts = parts
        self.headers = [
            "Nazwa",
            "Wymiary (mm)",
            "Ilość",
            "Materiał",
            "Okleina",
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self.parts)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            part = self.parts[index.row()]
            col = index.column()

            if col == 0:
                return part.part_name
            elif col == 1:
                return f"{part.width_mm} × {part.height_mm}"
            elif col == 2:
                return part.pieces
            elif col == 3:
                return part.material or "-"
            elif col == 4:
                return part.wrapping or "-"

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col in [1, 2]:  # Dimensions, quantity
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_parts(self, parts):
        self.beginResetModel()
        self.parts = parts
        self.endResetModel()

    def get_part_at_row(self, row):
        if 0 <= row < len(self.parts):
            return self.parts[row]
        return None


class PartsForm(QWidget):
    """Form for editing cabinet parts."""

    sig_dirty_changed = Signal(bool)

    def __init__(self, catalog_service=None, project_service=None, parent=None):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self.project_service = project_service
        self.cabinet_type = None
        self.project_cabinet = None  # For project instances
        self._is_dirty = False

        # Pending changes - held in memory until Save button is clicked
        self.pending = PendingChanges()

        self._setup_ui()
        self._setup_connections()
        self._apply_styles()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header_layout = QHBoxLayout()

        header_label = QLabel("Części szafki")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Buttons
        self.add_part_btn = QPushButton("Dodaj część")
        self.add_part_btn.setIcon(get_icon("add"))
        self.add_part_btn.clicked.connect(self._add_part)
        header_layout.addWidget(self.add_part_btn)

        self.edit_part_btn = QPushButton("Edytuj")
        self.edit_part_btn.setIcon(get_icon("edit"))
        self.edit_part_btn.clicked.connect(self._edit_part)
        self.edit_part_btn.setEnabled(False)
        header_layout.addWidget(self.edit_part_btn)

        self.delete_part_btn = QPushButton("Usuń")
        self.delete_part_btn.setIcon(get_icon("remove"))
        self.delete_part_btn.clicked.connect(self._delete_part)
        self.delete_part_btn.setEnabled(False)
        header_layout.addWidget(self.delete_part_btn)

        layout.addLayout(header_layout)

        # Parts table
        self.parts_table = QTableView()
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parts_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.parts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.parts_table.setAlternatingRowColors(True)
        self.parts_table.setSortingEnabled(True)
        self.parts_table.verticalHeader().setVisible(False)
        self.parts_table.setMinimumHeight(300)

        layout.addWidget(self.parts_table)

        # Info label
        self.info_label = QLabel("Wybierz szafkę, aby wyświetlić jej części")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # Spacer
        layout.addStretch()

    def _setup_connections(self):
        """Setup signal connections."""
        # Connect selection model after the table is properly initialized
        # Use a timer to ensure the table is fully initialized
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, self._connect_selection_model)

    def _connect_selection_model(self):
        """Connect to the selection model after table initialization."""
        selection_model = self.parts_table.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)
        # Connect double-click to edit
        self.parts_table.doubleClicked.connect(self._on_double_click)

    def _apply_styles(self):
        """Apply visual styling."""
        get_theme()

        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: white;
            }}
            QLineEdit, QSpinBox, QComboBox, QTextEdit {{
                padding: 8px;
                min-height: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
                border-color: {PRIMARY};
            }}
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
                opacity: 0.9;
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """)

    def _on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.parts_table.selectionModel().selectedRows()) > 0
        self.edit_part_btn.setEnabled(has_selection)
        self.delete_part_btn.setEnabled(has_selection)

    def _on_double_click(self, index):
        """Handle double-click on table row to edit the part."""
        if index.isValid():
            self._edit_part()

    def _add_part(self):
        """Add a new part to pending changes (saved on dialog save button)."""
        if (
            not self.cabinet_type
            and not self.project_cabinet
            and not hasattr(self, "custom_parts")
        ):
            QMessageBox.warning(self, "Błąd", "Najpierw wybierz szafkę.")
            return

        dialog = PartEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                part_data = dialog.part_data
                self.pending.add_item(part_data)
                self._mark_dirty()
                self._refresh_parts_display()

            except Exception as e:
                QMessageBox.critical(
                    self, "Błąd", f"Nie udało się dodać części: {str(e)}"
                )

    def _edit_part(self):
        """Edit the selected part (saved on dialog save button)."""
        current_row = self.parts_table.currentIndex().row()
        if current_row < 0:
            return

        if hasattr(self, "parts_model"):
            part = self.parts_model.get_part_at_row(current_row)
            if part:
                dialog = PartEditDialog(part, parent=self)
                if dialog.exec() == QDialog.Accepted:
                    try:
                        part_data = dialog.part_data
                        part_id = getattr(part, "id", None) or getattr(
                            part, "temp_id", None
                        )

                        if part_id:
                            self.pending.update_item(part_id, part_data)
                            self._mark_dirty()
                            self._refresh_parts_display()

                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Błąd",
                            f"Nie udało się zaktualizować części: {str(e)}",
                        )

    def _delete_part(self):
        """Delete the selected part (saved on dialog save button)."""
        current_row = self.parts_table.currentIndex().row()
        if current_row < 0:
            return

        if hasattr(self, "parts_model"):
            part = self.parts_model.get_part_at_row(current_row)
            if part:
                reply = QMessageBox.question(
                    self,
                    "Potwierdź usunięcie",
                    f"Czy na pewno chcesz usunąć część '{part.part_name}'?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    try:
                        part_id = getattr(part, "id", None) or getattr(
                            part, "temp_id", None
                        )
                        if part_id:
                            self.pending.remove_item(part_id)
                            self._mark_dirty()
                            self._refresh_parts_display()

                    except Exception as e:
                        QMessageBox.critical(
                            self, "Błąd", f"Nie udało się usunąć części: {str(e)}"
                        )

    def _refresh_parts(self):
        """Refresh the parts table (original method - loads from database)."""
        if self.cabinet_type and hasattr(self.cabinet_type, "parts"):
            parts = list(self.cabinet_type.parts)
            if not hasattr(self, "parts_model"):
                self.parts_model = PartsTableModel(parts)
                self.parts_table.setModel(self.parts_model)
            else:
                self.parts_model.update_parts(parts)

            self.info_label.setText(f"Znaleziono {len(parts)} części")
        else:
            self.info_label.setText("Brak części do wyświetlenia")

    def _refresh_parts_display(self):
        """Refresh parts display including pending changes."""
        display_parts = self._get_display_parts()
        self._update_parts_table(display_parts)

    def _get_display_parts(self) -> list:
        """Get list of parts to display, including pending changes."""
        from types import SimpleNamespace

        # Start with current database parts
        existing_parts = []
        if self.project_cabinet and hasattr(self.project_cabinet, "parts"):
            existing_parts = list(self.project_cabinet.parts)
        elif self.cabinet_type and hasattr(self.cabinet_type, "parts"):
            existing_parts = list(self.cabinet_type.parts)
        elif hasattr(self, "custom_parts"):
            existing_parts = self.custom_parts

        # Filter out parts marked for removal
        filtered_parts = [
            part for part in existing_parts if part.id not in self.pending.to_remove
        ]

        # Apply changes to existing parts (create copies to avoid mutating originals)
        result_parts = []
        for part in filtered_parts:
            if part.id in self.pending.changes:
                updated_data = self.pending.changes[part.id]
                part_copy = SimpleNamespace(
                    id=part.id,
                    part_name=updated_data.get("part_name", part.part_name),
                    height_mm=updated_data.get("height_mm", part.height_mm),
                    width_mm=updated_data.get("width_mm", part.width_mm),
                    pieces=updated_data.get("pieces", part.pieces),
                    material=updated_data.get("material", part.material),
                    wrapping=updated_data.get("wrapping", part.wrapping),
                    comments=updated_data.get(
                        "comments", getattr(part, "comments", None)
                    ),
                )
                result_parts.append(part_copy)
            else:
                result_parts.append(part)

        # Add pending new parts
        for pending_part in self.pending.to_add:
            temp_part = SimpleNamespace(
                id=None,
                temp_id=pending_part.get("temp_id"),
                part_name=pending_part.get("part_name", ""),
                height_mm=pending_part.get("height_mm", 0),
                width_mm=pending_part.get("width_mm", 0),
                pieces=pending_part.get("pieces", 1),
                material=pending_part.get("material", ""),
                wrapping=pending_part.get("wrapping", ""),
                comments=pending_part.get("comments", ""),
            )
            result_parts.append(temp_part)

        return result_parts

    def _update_parts_table(self, parts: list) -> None:
        """Update the parts table with given parts list."""
        total_count = len(parts)
        pending_count = len(self.pending.to_add)

        if pending_count > 0:
            self.info_label.setText(
                f"Znaleziono {total_count} części ({pending_count} do zapisania)"
            )
        else:
            self.info_label.setText(f"Znaleziono {total_count} części")

        if not hasattr(self, "parts_model"):
            self.parts_model = PartsTableModel(parts)
            self.parts_table.setModel(self.parts_model)
        else:
            self.parts_model.update_parts(parts)

    def _mark_dirty(self):
        """Mark form as dirty and emit signal."""
        if not self._is_dirty:
            self._is_dirty = True
            self.sig_dirty_changed.emit(True)

    def load(self, cabinet_type, project_cabinet=None):
        """Load cabinet type data and optionally project cabinet."""
        self.cabinet_type = cabinet_type
        self.project_cabinet = project_cabinet

        # Reset pending changes when loading new data
        self.pending.clear()

        if not cabinet_type and not project_cabinet:
            self.setEnabled(False)
            self.info_label.setText("Nie wybrano szafki do edycji")
            return

        self.setEnabled(True)
        self._refresh_parts_display()

        # Reset dirty flag
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

    def load_custom_parts(self, custom_parts, project_cabinet=None):
        """Load custom cabinet parts data."""
        self.cabinet_type = None  # No catalog type for custom cabinets
        self.project_cabinet = project_cabinet
        self.custom_parts = custom_parts or []

        # Reset pending changes when loading new data
        self.pending.clear()

        self.setEnabled(True)
        self._refresh_parts_display()

        # Update info label
        if self.custom_parts:
            self.info_label.setText(
                f"Niestandardowa szafka z {len(self.custom_parts)} częściami"
            )
        else:
            self.info_label.setText("Niestandardowa szafka bez części")

        # Reset dirty flag
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

    def is_dirty(self) -> bool:
        """Check if form has unsaved changes."""
        return self._is_dirty

    def is_valid(self) -> bool:
        """Check if form data is valid."""
        # For parts form, we consider it valid if we have either a cabinet type or custom parts
        return self.cabinet_type is not None or hasattr(self, "custom_parts")

    def reset_dirty(self):
        """Reset dirty flag after saving and clear pending changes."""
        self.pending.clear()
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)
        self._refresh_parts_display()

    def values(self) -> dict:
        """Get pending changes for saving.

        Returns a dict with consistent structure:
        - parts_to_add: list of part data dicts
        - parts_to_remove: list of part IDs
        - parts_changes: dict of {part_id: updated_data}
        """
        # For custom cabinets, return the complete updated parts list
        if hasattr(self, "custom_parts"):
            updated_parts = []

            # Add existing parts (with any pending changes applied)
            for part in self.custom_parts:
                if part.id not in self.pending.to_remove:
                    part_dict = {
                        "part_name": part.part_name,
                        "height_mm": part.height_mm,
                        "width_mm": part.width_mm,
                        "pieces": part.pieces,
                        "material": part.material,
                        "wrapping": part.wrapping,
                        "comments": getattr(part, "comments", None),
                        "processing_json": getattr(part, "processing_json", None),
                    }

                    # Apply any pending changes for this part
                    if part.id in self.pending.changes:
                        part_dict.update(self.pending.changes[part.id])

                    # Include source information if available
                    if hasattr(part, "source_template_id"):
                        part_dict["source_template_id"] = part.source_template_id
                    if hasattr(part, "source_part_id"):
                        part_dict["source_part_id"] = part.source_part_id
                    if hasattr(part, "calc_context_json"):
                        part_dict["calc_context_json"] = part.calc_context_json

                    updated_parts.append(part_dict)

            # Add new pending parts
            updated_parts.extend(self.pending.get_additions())
            return updated_parts

        # For regular cabinets, return structured pending changes
        return {
            "parts_to_add": self.pending.get_additions(),
            "parts_to_remove": self.pending.get_removals(),
            "parts_changes": self.pending.get_updates(),
        }

    def get_all_parts_data(self) -> list:
        """Get current parts data from the table model."""
        if not hasattr(self, "parts_model") or not self.parts_model:
            return []

        parts_data = []
        for part in self.parts_model.parts:
            # Convert part object to dictionary format expected by ProjectService
            part_dict = {
                "part_name": part.part_name,
                "height_mm": part.height_mm,
                "width_mm": part.width_mm,
                "pieces": part.pieces,
                "material": part.material,
                "wrapping": part.wrapping,
                "comments": getattr(part, "comments", None),
                "processing_json": getattr(part, "processing_json", None),
            }

            # Include source information if available (for regular cabinets)
            if hasattr(part, "source_template_id"):
                part_dict["source_template_id"] = part.source_template_id
            if hasattr(part, "source_part_id"):
                part_dict["source_part_id"] = part.source_part_id
            if hasattr(part, "calc_context_json"):
                part_dict["calc_context_json"] = part.calc_context_json

            parts_data.append(part_dict)

        return parts_data
