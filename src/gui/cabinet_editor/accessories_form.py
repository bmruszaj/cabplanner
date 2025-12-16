"""
Accessories form for editing cabinet accessories in the cabinet editor.

Handles accessory-level fields like SKU, quantities, etc.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QSpinBox,
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


class AccessoriesTableModel(QAbstractTableModel):
    """Model for displaying cabinet accessories in a table view"""

    def __init__(self, accessories, parent=None):
        super().__init__(parent)
        self.accessories = accessories
        self.headers = ["Nazwa", "SKU", "Ilość"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.accessories)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            accessory = self.accessories[index.row()]
            col = index.column()

            if col == 0:
                # Handle both legacy (with .accessory) and snapshot (direct fields)
                if hasattr(accessory, "accessory") and accessory.accessory:
                    return accessory.accessory.name
                else:
                    return accessory.name
            elif col == 1:
                # Handle both legacy (with .accessory) and snapshot (direct fields)
                if hasattr(accessory, "accessory") and accessory.accessory:
                    return accessory.accessory.sku
                else:
                    return accessory.sku
            elif col == 2:
                return accessory.count

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col == 2:  # Quantity
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_accessories(self, accessories):
        self.beginResetModel()
        self.accessories = accessories
        self.endResetModel()

    def get_accessory_at_row(self, row):
        if 0 <= row < len(self.accessories):
            return self.accessories[row]
        return None


class AccessorySelectionDialog(QDialog):
    """Dialog for selecting accessories to add to a cabinet"""

    def __init__(self, available_accessories, parent=None):
        super().__init__(parent)
        self.available_accessories = available_accessories
        self.selected_accessory = None
        self.selected_quantity = 1

        self.setWindowTitle("Wybierz akcesorium")
        self.resize(400, 300)

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Accessory selection
        selection_group = QGroupBox("Wybierz akcesorium")
        selection_layout = QFormLayout(selection_group)
        selection_layout.setSpacing(16)

        # Accessory name (free text)
        self.accessory_name_edit = QLineEdit()
        self.accessory_name_edit.setPlaceholderText(
            "np. Uchwyt standardowy, Zawias automatyczny..."
        )
        selection_layout.addRow("Nazwa akcesorium*:", self.accessory_name_edit)

        # Accessory SKU (free text)
        self.accessory_sku_edit = QLineEdit()
        self.accessory_sku_edit.setPlaceholderText("np. UCH-001, ZAW-001...")
        selection_layout.addRow("SKU:", self.accessory_sku_edit)

        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        selection_layout.addRow("Ilość:", self.quantity_spinbox)

        layout.addWidget(selection_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _setup_connections(self):
        """Setup signal connections."""
        pass

    def _on_accessory_changed(self, index):
        """Handle accessory selection change."""
        pass

    def accept(self):
        """Handle dialog acceptance."""
        name = self.accessory_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa akcesorium jest wymagana.")
            self.accessory_name_edit.setFocus()
            return

        # Create accessory data
        self.accessory_data = {
            "name": name,
            "sku": self.accessory_sku_edit.text().strip() or None,
            "quantity": self.quantity_spinbox.value(),
        }

        super().accept()


class AccessoryQuantityDialog(QDialog):
    """Dialog for editing accessory quantity"""

    def __init__(self, accessory, parent=None):
        super().__init__(parent)
        self.accessory = accessory
        self.new_quantity = accessory.count

        self.setWindowTitle("Zmień ilość")
        self.resize(300, 150)

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Info label - handle both legacy and snapshot accessories
        accessory_name = ""
        if hasattr(self.accessory, "accessory") and self.accessory.accessory:
            accessory_name = self.accessory.accessory.name
        else:
            accessory_name = self.accessory.name

        info_label = QLabel(f"Akcesorium: {accessory_name}")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        # Quantity selection
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Nowa ilość:"))

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(self.accessory.count)
        quantity_layout.addWidget(self.quantity_spinbox)

        layout.addLayout(quantity_layout)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _setup_connections(self):
        """Setup signal connections."""
        pass

    def accept(self):
        """Handle dialog acceptance."""
        self.new_quantity = self.quantity_spinbox.value()
        super().accept()


class AccessoriesForm(QWidget):
    """Form for editing cabinet accessories."""

    sig_dirty_changed = Signal(bool)

    def __init__(self, catalog_service=None, project_service=None, parent=None):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self.project_service = project_service
        self.project_cabinet = None
        self.cabinet_type = None
        self._is_dirty = False

        # Pending changes - trzymane w pamięci do czasu zapisu
        self.pending_accessories_to_add = []  # Lista akcesoriów do dodania
        self.pending_accessories_to_remove = []  # Lista ID akcesoriów do usunięcia
        self.pending_quantity_changes = {}  # Dict {accessory_id: new_quantity}

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

        header_label = QLabel("Akcesoria szafki")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Buttons
        self.add_accessory_btn = QPushButton("Dodaj akcesorium")
        self.add_accessory_btn.setIcon(get_icon("add"))
        self.add_accessory_btn.clicked.connect(self._add_accessory)
        header_layout.addWidget(self.add_accessory_btn)

        self.edit_quantity_btn = QPushButton("Zmień ilość")
        self.edit_quantity_btn.setIcon(get_icon("edit"))
        self.edit_quantity_btn.clicked.connect(self._edit_quantity)
        self.edit_quantity_btn.setEnabled(False)
        header_layout.addWidget(self.edit_quantity_btn)

        self.delete_accessory_btn = QPushButton("Usuń")
        self.delete_accessory_btn.setIcon(get_icon("remove"))
        self.delete_accessory_btn.clicked.connect(self._delete_accessory)
        self.delete_accessory_btn.setEnabled(False)
        header_layout.addWidget(self.delete_accessory_btn)

        layout.addLayout(header_layout)

        # Accessories table
        self.accessories_table = QTableView()
        self.accessories_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accessories_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.accessories_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.accessories_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.accessories_table.setAlternatingRowColors(True)
        self.accessories_table.setSortingEnabled(True)
        self.accessories_table.verticalHeader().setVisible(False)
        self.accessories_table.setMinimumHeight(300)

        layout.addWidget(self.accessories_table)

        # Info label
        self.info_label = QLabel("Wybierz szafkę, aby wyświetlić jej akcesoria")
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
        selection_model = self.accessories_table.selectionModel()
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
            QLineEdit, QSpinBox, QComboBox {{
                padding: 8px;
                min-height: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
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
        has_selection = len(self.accessories_table.selectionModel().selectedRows()) > 0
        self.edit_quantity_btn.setEnabled(has_selection)
        self.delete_accessory_btn.setEnabled(has_selection)

    def _add_accessory(self):
        """Add a new accessory directly to the database."""
        if not self.project_cabinet and not self.cabinet_type:
            QMessageBox.warning(self, "Błąd", "Najpierw wybierz szafkę.")
            return

        # Create empty list for available accessories (not used in free text mode)
        available_accessories = []

        dialog = AccessorySelectionDialog(available_accessories, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                # Get accessory data from dialog
                accessory_data = dialog.accessory_data

                # Save directly to database
                if self.project_cabinet and self.project_service:
                    success = self.project_service.add_accessory_to_cabinet(
                        cabinet_id=self.project_cabinet.id,
                        name=accessory_data["name"],
                        sku=accessory_data["sku"],
                        count=accessory_data["quantity"],
                    )
                    if success:
                        # Reload cabinet from database to get fresh data
                        refreshed_cabinet = self.project_service.get_cabinet(
                            self.project_cabinet.id
                        )
                        if refreshed_cabinet:
                            self.project_cabinet = refreshed_cabinet
                        self._refresh_accessories_display()
                    else:
                        QMessageBox.warning(
                            self, "Błąd", "Nie udało się dodać akcesorium do bazy."
                        )
                elif self.cabinet_type:
                    # For catalog templates, keep pending behavior
                    self.pending_accessories_to_add.append(
                        {
                            "name": accessory_data["name"],
                            "sku": accessory_data["sku"],
                            "count": accessory_data["quantity"],
                        }
                    )
                    self._mark_dirty()
                    self._refresh_accessories_display()

            except Exception as e:
                QMessageBox.critical(
                    self, "Błąd", f"Nie udało się dodać akcesorium:\n{str(e)}"
                )

    def _edit_quantity(self):
        """Edit the quantity of the selected accessory."""
        current_row = self.accessories_table.currentIndex().row()
        if current_row < 0:
            return

        if hasattr(self, "accessories_model"):
            accessory = self.accessories_model.get_accessory_at_row(current_row)
            if accessory:
                dialog = AccessoryQuantityDialog(accessory, parent=self)
                if dialog.exec() == QDialog.Accepted:
                    # Update quantity using ProjectService directly
                    if (
                        self.project_cabinet
                        and self.project_service
                        and hasattr(accessory, "id")
                        and accessory.id > 0
                    ):
                        success = self.project_service.update_accessory_quantity(
                            accessory.id, dialog.new_quantity
                        )
                        if success:
                            # Reload cabinet from database
                            refreshed_cabinet = self.project_service.get_cabinet(
                                self.project_cabinet.id
                            )
                            if refreshed_cabinet:
                                self.project_cabinet = refreshed_cabinet
                            self._refresh_accessories_display()
                        else:
                            QMessageBox.warning(
                                self, "Błąd", "Nie udało się zaktualizować ilości."
                            )
                    elif self.cabinet_type:
                        # For catalog templates, use pending changes
                        acc_id = getattr(accessory, "id", None) or getattr(
                            accessory, "accessory_id", None
                        )
                        if acc_id:
                            self.pending_quantity_changes[acc_id] = dialog.new_quantity
                        self._mark_dirty()
                        self._refresh_accessories_display()

    def _delete_accessory(self):
        """Delete the selected accessory."""
        current_row = self.accessories_table.currentIndex().row()
        if current_row < 0:
            return

        if hasattr(self, "accessories_model"):
            accessory = self.accessories_model.get_accessory_at_row(current_row)
            if accessory:
                # Handle both legacy and snapshot accessories for name display
                accessory_name = ""
                if hasattr(accessory, "accessory") and accessory.accessory:
                    accessory_name = accessory.accessory.name
                else:
                    accessory_name = accessory.name

                reply = QMessageBox.question(
                    self,
                    "Potwierdź usunięcie",
                    f"Czy na pewno chcesz usunąć akcesorium '{accessory_name}'?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply == QMessageBox.Yes:
                    # Remove accessory using ProjectService directly
                    if (
                        self.project_cabinet
                        and self.project_service
                        and hasattr(accessory, "id")
                        and accessory.id > 0
                    ):
                        success = self.project_service.remove_accessory_from_cabinet(
                            accessory.id
                        )
                        if success:
                            # Reload cabinet from database
                            refreshed_cabinet = self.project_service.get_cabinet(
                                self.project_cabinet.id
                            )
                            if refreshed_cabinet:
                                self.project_cabinet = refreshed_cabinet
                            self._refresh_accessories_display()
                        else:
                            QMessageBox.warning(
                                self, "Błąd", "Nie udało się usunąć akcesorium."
                            )
                    elif self.cabinet_type:
                        # For catalog templates, use pending removal
                        acc_id = getattr(accessory, "id", None) or getattr(
                            accessory, "accessory_id", None
                        )
                        if acc_id:
                            self.pending_accessories_to_remove.append(acc_id)
                        self._mark_dirty()
                        self._refresh_accessories_display()

    def _refresh_accessories(self):
        """Refresh the accessories table (original method - loads from database)."""
        accessories = []

        if self.project_cabinet and hasattr(
            self.project_cabinet, "accessory_snapshots"
        ):
            # Project instance mode - show project-specific accessories from snapshots
            accessories = list(self.project_cabinet.accessory_snapshots)
            self.info_label.setText(
                f"Znaleziono {len(accessories)} akcesoriów w projekcie"
            )
        elif self.cabinet_type and hasattr(self.cabinet_type, "accessories"):
            # Catalog type mode - show catalog-level accessories from template
            accessories = list(self.cabinet_type.accessories)
            self.info_label.setText(
                f"Znaleziono {len(accessories)} akcesoriów w katalogu"
            )
        else:
            self.info_label.setText("Brak akcesoriów do wyświetlenia")

        if not hasattr(self, "accessories_model"):
            self.accessories_model = AccessoriesTableModel(accessories)
            self.accessories_table.setModel(self.accessories_model)
        else:
            self.accessories_model.update_accessories(accessories)

    def _refresh_accessories_display(self):
        """Refresh accessories display including pending changes."""
        # Start with current database accessories
        existing_accessories = []

        if self.project_cabinet and hasattr(
            self.project_cabinet, "accessory_snapshots"
        ):
            existing_accessories = list(self.project_cabinet.accessory_snapshots)
        elif self.cabinet_type and hasattr(self.cabinet_type, "accessories"):
            # Load accessories from cabinet template
            existing_accessories = list(self.cabinet_type.accessories)

        # Filter out accessories marked for removal
        # For CabinetTemplateAccessory, use accessory_id; for snapshots, use id
        filtered_accessories = []
        for acc in existing_accessories:
            # Get the appropriate ID for this accessory type
            acc_id = getattr(acc, "id", None) or getattr(acc, "accessory_id", None)
            if acc_id not in self.pending_accessories_to_remove:
                filtered_accessories.append(acc)

        # Apply quantity changes
        for acc in filtered_accessories:
            acc_id = getattr(acc, "id", None) or getattr(acc, "accessory_id", None)
            if acc_id in self.pending_quantity_changes:
                acc.count = self.pending_quantity_changes[acc_id]

        # Add pending new accessories (create temporary objects for display)
        from types import SimpleNamespace

        for pending_acc in self.pending_accessories_to_add:
            temp_acc = SimpleNamespace(
                id=-1,  # Temporary ID
                name=pending_acc["name"],
                sku=pending_acc["sku"],
                count=pending_acc["count"],
            )
            filtered_accessories.append(temp_acc)

        # Update display
        total_count = len(filtered_accessories)
        pending_count = len(self.pending_accessories_to_add)

        if pending_count > 0:
            self.info_label.setText(
                f"Znaleziono {total_count} akcesoriów ({pending_count} do zapisania)"
            )
        else:
            self.info_label.setText(f"Znaleziono {total_count} akcesoriów")

        if not hasattr(self, "accessories_model"):
            self.accessories_model = AccessoriesTableModel(filtered_accessories)
            self.accessories_table.setModel(self.accessories_model)
        else:
            self.accessories_model.update_accessories(filtered_accessories)

    def _mark_dirty(self):
        """Mark form as dirty and emit signal."""
        if not self._is_dirty:
            self._is_dirty = True
            self.sig_dirty_changed.emit(True)

    def load(self, project_cabinet, cabinet_type=None):
        """Load project cabinet data."""
        self.project_cabinet = project_cabinet
        self.cabinet_type = cabinet_type

        # Reset pending changes when loading new data
        self.pending_accessories_to_add = []
        self.pending_accessories_to_remove = []
        self.pending_quantity_changes = {}

        if not project_cabinet and not cabinet_type:
            self.setEnabled(False)
            self.info_label.setText("Nie wybrano szafki do edycji")
            return

        self.setEnabled(True)
        self._refresh_accessories_display()  # Use new method that shows pending changes

        # Reset dirty flag
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

    def is_dirty(self) -> bool:
        """Check if form has unsaved changes."""
        return self._is_dirty

    def is_valid(self) -> bool:
        """Check if form data is valid."""
        # For accessories form, we consider it valid if we have a project cabinet or cabinet type
        return self.project_cabinet is not None or self.cabinet_type is not None

    def reset_dirty(self):
        """Reset dirty flag after saving and clear pending changes."""
        # Clear pending changes since they've been saved
        self.pending_accessories_to_add = []
        self.pending_accessories_to_remove = []
        self.pending_quantity_changes = {}

        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

        # Reload project_cabinet from database to get fresh accessory_snapshots
        # (with proper IDs for newly added accessories)
        if self.project_cabinet and self.project_service:
            refreshed_cabinet = self.project_service.get_cabinet(
                self.project_cabinet.id
            )
            if refreshed_cabinet:
                self.project_cabinet = refreshed_cabinet

        # Refresh display to show current state without pending changes
        self._refresh_accessories_display()

    def values(self) -> dict:
        """Get pending changes for saving."""
        return {
            "accessories_to_add": self.pending_accessories_to_add.copy(),
            "accessories_to_remove": self.pending_accessories_to_remove.copy(),
            "quantity_changes": self.pending_quantity_changes.copy(),
        }
