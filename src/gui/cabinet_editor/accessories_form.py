"""
Accessories form for editing cabinet accessories in the cabinet editor.

Handles accessory-level fields like names and quantities.
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
    QStyledItemDelegate,
    QToolTip,
)
from PySide6.QtCore import Signal, Qt, QAbstractTableModel, QModelIndex, QEvent
from PySide6.QtGui import QFont

from src.gui.resources.resources import get_icon
from src.gui.resources.styles import get_theme, PRIMARY
from src.gui.dialogs.accessory_edit_dialog import AccessoryEditDialog
from src.services.accessory_service import AccessoryService
from .pending_changes import PendingChanges


class AccessoriesTableModel(QAbstractTableModel):
    """Model for displaying cabinet accessories in a table view"""

    def __init__(self, accessories, parent=None):
        super().__init__(parent)
        self.accessories = accessories
        self.headers = ["Nazwa", "Ilość"]

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
                return accessory.count

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col == 1:  # Quantity
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


class ElidedTextTooltipDelegate(QStyledItemDelegate):
    """Show tooltip with full text only when it is elided in the cell."""

    def helpEvent(self, event, view, option, index):
        if event is None or view is None:
            return super().helpEvent(event, view, option, index)

        if event.type() == QEvent.ToolTip:
            text = index.data(Qt.DisplayRole)
            if text is None:
                return False

            text = str(text).strip()
            if not text:
                return False

            # Account for table cell padding/margins.
            available_width = max(0, option.rect.width() - 8)
            is_elided = option.fontMetrics.horizontalAdvance(text) > available_width
            if is_elided:
                QToolTip.showText(event.globalPos(), text, view)
                return True

            QToolTip.hideText()
            event.ignore()
            return False

        return super().helpEvent(event, view, option, index)


class AccessoriesForm(QWidget):
    """Form for editing cabinet accessories."""

    sig_dirty_changed = Signal(bool)
    QUANTITY_COLUMN_INDEX = 1
    QUANTITY_COLUMN_WIDTH = 100

    def __init__(
        self,
        catalog_service=None,
        project_service=None,
        parent=None,
        is_dark_mode: bool = False,
    ):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self.project_service = project_service
        self.is_dark_mode = is_dark_mode
        self.project_cabinet = None
        self.cabinet_type = None
        self._is_dirty = False

        # Create accessory service from catalog session for catalog integration
        self.accessory_service = None
        if catalog_service and hasattr(catalog_service, "session"):
            self.accessory_service = AccessoryService(catalog_service.session)

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

        self.edit_accessory_btn = QPushButton("Edytuj")
        self.edit_accessory_btn.setIcon(get_icon("edit"))
        self.edit_accessory_btn.clicked.connect(self._edit_accessory)
        self.edit_accessory_btn.setEnabled(False)
        header_layout.addWidget(self.edit_accessory_btn)

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
        self.accessories_table.setItemDelegateForColumn(
            0, ElidedTextTooltipDelegate(self.accessories_table)
        )
        self.accessories_table.setAlternatingRowColors(True)
        self.accessories_table.setSortingEnabled(True)
        self.accessories_table.verticalHeader().setVisible(False)
        self.accessories_table.setMinimumHeight(300)

        layout.addWidget(self.accessories_table)

        # Info label
        self.info_label = QLabel("Wybierz szafkę, aby wyświetlić jej akcesoria")
        info_color = "#B0B0B0" if self.is_dark_mode else "#666666"
        self.info_label.setStyleSheet(f"color: {info_color}; font-style: italic;")
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
        # Connect double-click to edit
        self.accessories_table.doubleClicked.connect(self._on_double_click)

    def _apply_column_layout(self):
        """Keep name column stretched and quantity column fixed to the right."""
        model = self.accessories_table.model()
        if model is None or model.columnCount() <= self.QUANTITY_COLUMN_INDEX:
            return

        header = self.accessories_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(self.QUANTITY_COLUMN_INDEX, QHeaderView.Fixed)
        self.accessories_table.setColumnWidth(
            self.QUANTITY_COLUMN_INDEX, self.QUANTITY_COLUMN_WIDTH
        )

    def _apply_styles(self):
        """Apply visual styling."""
        panel_border = "#4A4A4A" if self.is_dark_mode else "#E0E0E0"
        panel_bg = "#333333" if self.is_dark_mode else "#FFFFFF"
        input_bg = "#333333" if self.is_dark_mode else "#FFFFFF"
        input_border = "#5A5A5A" if self.is_dark_mode else "#DDDDDD"
        text_color = "#E0E0E0" if self.is_dark_mode else "#333333"
        disabled_bg = "#555555" if self.is_dark_mode else "#CCCCCC"
        disabled_text = "#9A9A9A" if self.is_dark_mode else "#666666"

        self.setStyleSheet(
            get_theme(self.is_dark_mode)
            + f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid {panel_border};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: {panel_bg};
                color: {text_color};
            }}
            QLineEdit, QSpinBox, QComboBox {{
                padding: 8px;
                min-height: 20px;
                border: 1px solid {input_border};
                border-radius: 4px;
                background-color: {input_bg};
                color: {text_color};
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
                background-color: {disabled_bg};
                color: {disabled_text};
            }}
        """
        )

    def _on_selection_changed(self):
        """Handle table selection changes."""
        has_selection = len(self.accessories_table.selectionModel().selectedRows()) > 0
        self.edit_accessory_btn.setEnabled(has_selection)
        self.delete_accessory_btn.setEnabled(has_selection)

    def _on_double_click(self, index):
        """Handle double-click on table row to edit the accessory."""
        if index.isValid():
            self._edit_accessory()

    def _get_existing_accessory_names(self):
        """Get list of existing accessory names for uniqueness validation."""
        names = []
        if hasattr(self, "accessories_model"):
            for acc in self.accessories_model.accessories:
                name = getattr(acc, "name", None)
                if not name and hasattr(acc, "accessory") and acc.accessory:
                    name = acc.accessory.name
                if name:
                    names.append(name)
        return names

    def _add_accessory(self):
        """Add a new accessory to pending changes (saved on dialog save button)."""
        if not self.project_cabinet and not self.cabinet_type:
            QMessageBox.warning(self, "Błąd", "Najpierw wybierz szafkę.")
            return

        existing_names = self._get_existing_accessory_names()
        dialog = AccessoryEditDialog(
            existing_names=existing_names,
            accessory_service=self.accessory_service,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            try:
                accessory_data = dialog.accessory_data
                self.pending.add_item(
                    {
                        "name": accessory_data["name"],
                        "count": accessory_data["count"],
                    }
                )
                self._mark_dirty()
                self._refresh_accessories_display()

            except Exception as e:
                QMessageBox.critical(
                    self, "Błąd", f"Nie udało się dodać akcesorium:\n{str(e)}"
                )

    def _edit_accessory(self):
        """Edit the selected accessory (saved on dialog save button)."""
        current_row = self.accessories_table.currentIndex().row()
        if current_row < 0:
            return

        if hasattr(self, "accessories_model"):
            accessory = self.accessories_model.get_accessory_at_row(current_row)
            if accessory:
                # Convert accessory object to dict for AccessoryEditDialog
                accessory_dict = {
                    "name": getattr(accessory, "name", "")
                    or (
                        accessory.accessory.name
                        if hasattr(accessory, "accessory") and accessory.accessory
                        else ""
                    ),
                    "count": getattr(accessory, "count", 1),
                }
                existing_names = self._get_existing_accessory_names()
                dialog = AccessoryEditDialog(
                    accessory=accessory_dict,
                    existing_names=existing_names,
                    accessory_service=self.accessory_service,
                    parent=self,
                )
                if dialog.exec() == QDialog.Accepted:
                    acc_id = (
                        getattr(accessory, "id", None)
                        or getattr(accessory, "accessory_id", None)
                        or getattr(accessory, "temp_id", None)
                    )
                    if acc_id:
                        accessory_data = dialog.accessory_data
                        self.pending.update_item(
                            acc_id,
                            {
                                "name": accessory_data["name"],
                                "count": accessory_data["count"],
                            },
                        )
                        self._mark_dirty()
                        self._refresh_accessories_display()

    def _delete_accessory(self):
        """Delete the selected accessory (saved on dialog save button)."""
        current_row = self.accessories_table.currentIndex().row()
        if current_row < 0:
            return

        if hasattr(self, "accessories_model"):
            accessory = self.accessories_model.get_accessory_at_row(current_row)
            if accessory:
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
                    acc_id = (
                        getattr(accessory, "id", None)
                        or getattr(accessory, "accessory_id", None)
                        or getattr(accessory, "temp_id", None)
                    )
                    if acc_id:
                        self.pending.remove_item(acc_id)
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

        self._apply_column_layout()

    def _refresh_accessories_display(self):
        """Refresh accessories display including pending changes."""
        display_accessories = self._get_display_accessories()
        self._update_accessories_table(display_accessories)

    def _get_display_accessories(self) -> list:
        """Get list of accessories to display, including pending changes."""
        from types import SimpleNamespace

        # Start with current database accessories
        existing_accessories = []
        if self.project_cabinet and hasattr(
            self.project_cabinet, "accessory_snapshots"
        ):
            existing_accessories = list(self.project_cabinet.accessory_snapshots)
        elif self.cabinet_type and hasattr(self.cabinet_type, "accessories"):
            existing_accessories = list(self.cabinet_type.accessories)

        # Filter out accessories marked for removal
        result_accessories = []
        for acc in existing_accessories:
            acc_id = getattr(acc, "id", None) or getattr(acc, "accessory_id", None)
            if acc_id not in self.pending.to_remove:
                current_name = getattr(acc, "name", None) or (
                    acc.accessory.name
                    if hasattr(acc, "accessory") and acc.accessory
                    else ""
                )

                # Apply pending changes (name and quantity) if any
                if acc_id in self.pending.changes:
                    updated_data = self.pending.changes[acc_id]
                    acc_copy = SimpleNamespace(
                        id=acc_id,
                        name=updated_data.get("name", current_name),
                        count=updated_data.get("count", acc.count),
                    )
                    result_accessories.append(acc_copy)
                else:
                    result_accessories.append(acc)

        # Add pending new accessories
        for pending_acc in self.pending.to_add:
            temp_acc = SimpleNamespace(
                id=None,
                temp_id=pending_acc.get("temp_id"),
                name=pending_acc.get("name", ""),
                count=pending_acc.get("count", 1),
            )
            result_accessories.append(temp_acc)

        return result_accessories

    def _update_accessories_table(self, accessories: list) -> None:
        """Update the accessories table with given list."""
        total_count = len(accessories)
        pending_count = len(self.pending.to_add)

        if pending_count > 0:
            self.info_label.setText(
                f"Znaleziono {total_count} akcesoriów ({pending_count} do zapisania)"
            )
        else:
            self.info_label.setText(f"Znaleziono {total_count} akcesoriów")

        if not hasattr(self, "accessories_model"):
            self.accessories_model = AccessoriesTableModel(accessories)
            self.accessories_table.setModel(self.accessories_model)
        else:
            self.accessories_model.update_accessories(accessories)

        self._apply_column_layout()

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
        self.pending.clear()

        if not project_cabinet and not cabinet_type:
            self.setEnabled(False)
            self.info_label.setText("Nie wybrano szafki do edycji")
            return

        self.setEnabled(True)
        self._refresh_accessories_display()

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
        self.pending.clear()
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

        # Reload project_cabinet from database to get fresh accessory_snapshots
        if self.project_cabinet and self.project_service:
            refreshed_cabinet = self.project_service.get_cabinet(
                self.project_cabinet.id
            )
            if refreshed_cabinet:
                self.project_cabinet = refreshed_cabinet

        self._refresh_accessories_display()

    def values(self) -> dict:
        """Get pending changes for saving.

        Returns a dict with consistent structure:
        - accessories_to_add: list of accessory data dicts
        - accessories_to_remove: list of accessory IDs
        - accessories_changes: dict of {acc_id: updated_data}
        - quantity_changes: dict of {acc_id: new_count}
        """
        accessories_changes = self.pending.get_updates()

        # Extract quantity changes from changes dict
        quantity_changes = {
            acc_id: data.get("count")
            for acc_id, data in accessories_changes.items()
            if "count" in data
        }

        return {
            "accessories_to_add": self.pending.get_additions(),
            "accessories_to_remove": self.pending.get_removals(),
            "accessories_changes": accessories_changes,
            "quantity_changes": quantity_changes,
        }
