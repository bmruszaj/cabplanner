"""
Parts form for editing cabinet parts in the cabinet editor.

Handles part-level fields like dimensions, materials, quantities, etc.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QSpinBox,
    QTextEdit,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
)
from PySide6.QtCore import Signal, Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont

from src.gui.resources.resources import get_icon
from src.gui.resources.styles import get_theme, PRIMARY


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
            "Grubość",
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
                return f"{part.thickness_mm}mm" if part.thickness_mm else "-"
            elif col == 5:
                return part.wrapping or "-"

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col in [1, 2, 4]:  # Dimensions, quantity, thickness
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


class PartEditDialog(QDialog):
    """Dialog for editing a cabinet part"""

    def __init__(self, part=None, parent=None):
        super().__init__(parent)
        self.part = part
        self.is_edit_mode = part is not None

        self.setWindowTitle("Edytuj część" if self.is_edit_mode else "Nowa część")
        self.resize(400, 500)

        self._setup_ui()
        self._setup_connections()

        if self.is_edit_mode:
            self._load_part_data()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Basic information group
        basic_group = QGroupBox("Podstawowe informacje")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(16)

        # Part name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. bok lewy, front, półka...")
        basic_layout.addRow("Nazwa części*:", self.name_edit)

        # Dimensions
        dimensions_layout = QHBoxLayout()

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(0, 5000)
        self.width_spinbox.setSuffix(" mm")
        self.width_spinbox.setValue(600)
        dimensions_layout.addWidget(QLabel("Szerokość:"))
        dimensions_layout.addWidget(self.width_spinbox)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(0, 5000)
        self.height_spinbox.setSuffix(" mm")
        self.height_spinbox.setValue(720)
        dimensions_layout.addWidget(QLabel("Wysokość:"))
        dimensions_layout.addWidget(self.height_spinbox)

        basic_layout.addRow("Wymiary:", dimensions_layout)

        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        basic_layout.addRow("Ilość:", self.quantity_spinbox)

        layout.addWidget(basic_group)

        # Material information group
        material_group = QGroupBox("Informacje o materiale")
        material_layout = QFormLayout(material_group)
        material_layout.setSpacing(16)

        # Material type
        self.material_combo = QComboBox()
        self.material_combo.addItems(["PLYTA", "HDF", "FRONT", "INNE"])
        self.material_combo.setEditable(True)
        material_layout.addRow("Materiał:", self.material_combo)

        # Thickness
        self.thickness_spinbox = QSpinBox()
        self.thickness_spinbox.setRange(0, 100)
        self.thickness_spinbox.setSuffix(" mm")
        self.thickness_spinbox.setValue(18)
        material_layout.addRow("Grubość:", self.thickness_spinbox)

        # Wrapping
        self.wrapping_edit = QLineEdit()
        self.wrapping_edit.setPlaceholderText("np. D, K, DDKK...")
        material_layout.addRow("Okleina:", self.wrapping_edit)

        layout.addWidget(material_group)

        # Comments group
        comments_group = QGroupBox("Uwagi")
        comments_layout = QVBoxLayout(comments_group)

        self.comments_edit = QTextEdit()
        self.comments_edit.setMaximumHeight(80)
        self.comments_edit.setPlaceholderText("Dodatkowe uwagi dotyczące części...")
        comments_layout.addWidget(self.comments_edit)

        layout.addWidget(comments_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _setup_connections(self):
        """Setup signal connections."""
        pass

    def _load_part_data(self):
        """Load part data into the form."""
        if not self.part:
            return

        self.name_edit.setText(self.part.part_name or "")
        self.width_spinbox.setValue(self.part.width_mm or 0)
        self.height_spinbox.setValue(self.part.height_mm or 0)
        self.quantity_spinbox.setValue(self.part.pieces or 1)

        if self.part.material:
            index = self.material_combo.findText(self.part.material)
            if index >= 0:
                self.material_combo.setCurrentIndex(index)
            else:
                self.material_combo.setCurrentText(self.part.material)

        self.thickness_spinbox.setValue(self.part.thickness_mm or 0)
        self.wrapping_edit.setText(self.part.wrapping or "")
        self.comments_edit.setPlainText(self.part.comments or "")

    def accept(self):
        """Handle dialog acceptance."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa części jest wymagana.")
            self.name_edit.setFocus()
            return

        # Create part data
        self.part_data = {
            "part_name": name,
            "width_mm": self.width_spinbox.value(),
            "height_mm": self.height_spinbox.value(),
            "pieces": self.quantity_spinbox.value(),
            "material": self.material_combo.currentText() or None,
            "thickness_mm": self.thickness_spinbox.value() or None,
            "wrapping": self.wrapping_edit.text().strip() or None,
            "comments": self.comments_edit.toPlainText().strip() or None,
        }

        super().accept()


class PartsForm(QWidget):
    """Form for editing cabinet parts."""

    sig_dirty_changed = Signal(bool)

    def __init__(self, catalog_service=None, project_service=None, parent=None):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self.project_service = project_service
        self.cabinet_type = None
        self._is_dirty = False

        # Pending changes - trzymane w pamięci do czasu zapisu
        self.pending_parts_to_add = []  # Lista części do dodania
        self.pending_parts_to_remove = []  # Lista ID części do usunięcia
        self.pending_parts_changes = {}  # Dict {part_id: part_data} dla edytowanych części

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

    def _add_part(self):
        """Add a new part (kept in memory until save)."""
        if not self.cabinet_type and not hasattr(self, "custom_parts"):
            QMessageBox.warning(self, "Błąd", "Najpierw wybierz szafkę.")
            return

        dialog = PartEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                # Get part data from dialog
                part_data = dialog.part_data

                # For catalog cabinets, add cabinet_type_id
                if self.cabinet_type:
                    part_data["cabinet_type_id"] = self.cabinet_type.id

                # Add to pending changes instead of calling service immediately
                self.pending_parts_to_add.append(part_data)

                self._mark_dirty()
                self._refresh_parts_display()

            except Exception as e:
                QMessageBox.critical(
                    self, "Błąd", f"Nie udało się dodać części: {str(e)}"
                )

    def _edit_part(self):
        """Edit the selected part."""
        current_row = self.parts_table.currentIndex().row()
        if current_row < 0:
            return

        if not self.catalog_service:
            QMessageBox.warning(self, "Błąd", "Serwis katalogu nie jest dostępny.")
            return

        if hasattr(self, "parts_model"):
            part = self.parts_model.get_part_at_row(current_row)
            if part:
                dialog = PartEditDialog(part, parent=self)
                if dialog.exec() == QDialog.Accepted:
                    try:
                        # Update part using TemplateService
                        part_data = dialog.part_data
                        template_service = self.catalog_service.cabinet_type_service

                        # Update the part in the database
                        for key, value in part_data.items():
                            if hasattr(part, key):
                                setattr(part, key, value)

                        # Commit changes - TemplateService doesn't have update_part method,
                        # so we'll use the session directly
                        template_service.db.commit()
                        template_service.db.refresh(part)

                        self._mark_dirty()
                        self._refresh_parts()

                        QMessageBox.information(
                            self,
                            "Sukces",
                            f"Część '{part.part_name}' została zaktualizowana.",
                        )
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Błąd",
                            f"Nie udało się zaktualizować części: {str(e)}",
                        )

    def _delete_part(self):
        """Delete the selected part."""
        current_row = self.parts_table.currentIndex().row()
        if current_row < 0:
            return

        if not self.catalog_service:
            QMessageBox.warning(self, "Błąd", "Serwis katalogu nie jest dostępny.")
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
                        # Delete part using TemplateService
                        template_service = self.catalog_service.cabinet_type_service
                        success = template_service.delete_part(part.id)

                        if success:
                            self._mark_dirty()
                            self._refresh_parts()
                            QMessageBox.information(
                                self,
                                "Sukces",
                                f"Część '{part.part_name}' została usunięta.",
                            )
                        else:
                            QMessageBox.warning(
                                self, "Błąd", "Nie udało się usunąć części."
                            )
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
        # Start with current database parts
        existing_parts = []

        if self.cabinet_type and hasattr(self.cabinet_type, "parts"):
            existing_parts = list(self.cabinet_type.parts)
        elif hasattr(self, "custom_parts"):
            existing_parts = self.custom_parts

        # Filter out parts marked for removal
        filtered_parts = [
            part
            for part in existing_parts
            if part.id not in self.pending_parts_to_remove
        ]

        # Apply changes to existing parts
        for part in filtered_parts:
            if part.id in self.pending_parts_changes:
                updated_data = self.pending_parts_changes[part.id]
                for key, value in updated_data.items():
                    if hasattr(part, key):
                        setattr(part, key, value)

        # Add pending new parts (create temporary objects for display)
        from types import SimpleNamespace

        for pending_part in self.pending_parts_to_add:
            temp_part = SimpleNamespace(
                id=-1,  # Temporary ID
                part_name=pending_part.get("part_name", ""),
                height_mm=pending_part.get("height_mm", 0),
                width_mm=pending_part.get("width_mm", 0),
                pieces=pending_part.get("pieces", 1),
                material=pending_part.get("material", ""),
                thickness_mm=pending_part.get("thickness_mm", 0),
                wrapping=pending_part.get("wrapping", ""),
                comments=pending_part.get("comments", ""),
            )
            filtered_parts.append(temp_part)

        # Update display
        total_count = len(filtered_parts)
        pending_count = len(self.pending_parts_to_add)

        if pending_count > 0:
            self.info_label.setText(
                f"Znaleziono {total_count} części ({pending_count} do zapisania)"
            )
        else:
            self.info_label.setText(f"Znaleziono {total_count} części")

        if not hasattr(self, "parts_model"):
            self.parts_model = PartsTableModel(filtered_parts)
            self.parts_table.setModel(self.parts_model)
        else:
            self.parts_model.update_parts(filtered_parts)

    def _mark_dirty(self):
        """Mark form as dirty and emit signal."""
        if not self._is_dirty:
            self._is_dirty = True
            self.sig_dirty_changed.emit(True)

    def load(self, cabinet_type):
        """Load cabinet type data."""
        self.cabinet_type = cabinet_type

        # Reset pending changes when loading new data
        self.pending_parts_to_add = []
        self.pending_parts_to_remove = []
        self.pending_parts_changes = {}

        if not cabinet_type:
            self.setEnabled(False)
            self.info_label.setText("Nie wybrano szafki do edycji")
            return

        self.setEnabled(True)
        self._refresh_parts_display()  # Use new method that shows pending changes

        # Reset dirty flag
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

    def load_custom_parts(self, custom_parts):
        """Load custom cabinet parts data."""
        self.cabinet_type = None  # No catalog type for custom cabinets
        self.custom_parts = custom_parts or []

        # Reset pending changes when loading new data
        self.pending_parts_to_add = []
        self.pending_parts_to_remove = []
        self.pending_parts_changes = {}

        self.setEnabled(True)
        self._refresh_parts_display()  # Use new method that shows pending changes

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
        # Clear pending changes since they've been saved
        self.pending_parts_to_add = []
        self.pending_parts_to_remove = []
        self.pending_parts_changes = {}

        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

        # Refresh display to show current state without pending changes
        self._refresh_parts_display()

    def values(self) -> dict:
        """Get pending changes for saving."""
        # For custom cabinets, return the complete updated parts list
        if hasattr(self, "custom_parts"):
            # Start with current custom parts
            updated_parts = []

            # Add existing parts (with any pending changes applied)
            for part in self.custom_parts:
                if part.id not in self.pending_parts_to_remove:
                    part_dict = {
                        "part_name": part.part_name,
                        "height_mm": part.height_mm,
                        "width_mm": part.width_mm,
                        "pieces": part.pieces,
                        "material": part.material,
                        "thickness_mm": part.thickness_mm,
                        "wrapping": part.wrapping,
                        "comments": getattr(part, "comments", None),
                        "processing_json": getattr(part, "processing_json", None),
                    }

                    # Apply any pending changes for this part
                    if part.id in self.pending_parts_changes:
                        part_dict.update(self.pending_parts_changes[part.id])

                    # Include source information if available
                    if hasattr(part, "source_template_id"):
                        part_dict["source_template_id"] = part.source_template_id
                    if hasattr(part, "source_part_id"):
                        part_dict["source_part_id"] = part.source_part_id
                    if hasattr(part, "calc_context_json"):
                        part_dict["calc_context_json"] = part.calc_context_json

                    updated_parts.append(part_dict)

            # Add new pending parts
            for pending_part in self.pending_parts_to_add:
                updated_parts.append(pending_part)

            return updated_parts

        else:
            # For catalog cabinets, return pending changes
            return {
                "parts_to_add": self.pending_parts_to_add.copy(),
                "parts_to_remove": self.pending_parts_to_remove.copy(),
                "parts_changes": self.pending_parts_changes.copy(),
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
                "thickness_mm": part.thickness_mm,
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
