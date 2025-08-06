"""
Modern accessory management dialog for the Cabplanner application.
"""

import logging
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from sqlalchemy.orm import Session

from src.services.accessory_service import AccessoryService
from src.gui.resources.resources import get_icon

# Configure logging
logger = logging.getLogger(__name__)


class AccessoryModel(QAbstractTableModel):
    """Model for displaying accessories in a table view"""

    def __init__(self, accessories, parent=None):
        super().__init__(parent)
        self.accessories = accessories
        self.headers = ["ID", "Nazwa", "SKU", "Data utworzenia"]

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
                return accessory.id
            elif col == 1:
                return accessory.name
            elif col == 2:
                return accessory.sku
            elif col == 3:
                return accessory.created_at.strftime("%Y-%m-%d")

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col == 0:  # ID column
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


class AccessoryDialog(QDialog):
    """Dialog for creating or editing an accessory"""

    def __init__(self, db_session: Session, accessory_id=None, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.accessory_service = AccessoryService(self.session)

        self.accessory_id = accessory_id
        self.accessory = None

        if accessory_id:
            self.accessory = self.accessory_service.get_accessory(accessory_id)

        self.init_ui()

        if self.accessory:
            self.setWindowTitle("Edytuj akcesorium")
            self.load_accessory_data()
        else:
            self.setWindowTitle("Nowe akcesorium")

    def init_ui(self):
        """Initialize the UI components"""
        self.resize(400, 250)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Form group
        form_group = QGroupBox("Dane akcesorium")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)

        # Accessory name
        self.name_edit = QLineEdit()
        form_layout.addRow("Nazwa:", self.name_edit)

        # SKU/code
        self.sku_edit = QLineEdit()
        form_layout.addRow("SKU/Kod:", self.sku_edit)

        main_layout.addWidget(form_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_accessory_data(self):
        """Load accessory data into the form"""
        if not self.accessory:
            return

        self.name_edit.setText(self.accessory.name)
        self.sku_edit.setText(self.accessory.sku)

    def accept(self):
        """Handle dialog acceptance"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa akcesorium jest wymagana.")
            self.name_edit.setFocus()
            return

        sku = self.sku_edit.text().strip()
        if not sku:
            QMessageBox.warning(self, "Błąd", "SKU/Kod akcesorium jest wymagany.")
            self.sku_edit.setFocus()
            return

        try:
            if self.accessory_id:
                # Update existing accessory
                self.accessory_service.update_accessory(
                    self.accessory_id, name=name, sku=sku
                )
                logger.info(f"Updated accessory ID: {self.accessory_id}")
            else:
                # Create new accessory
                new_accessory = self.accessory_service.create_accessory(
                    name=name, sku=sku
                )
                logger.info(f"Created new accessory ID: {new_accessory.id}")

            super().accept()

        except Exception as e:
            logger.error(f"Error saving accessory: {e}")
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zapisać akcesorium: {str(e)}"
            )


class AccessorySelectionDialog(QDialog):
    """Dialog for selecting accessories to add to a cabinet"""

    def __init__(self, db_session: Session, cabinet_id: int, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.accessory_service = AccessoryService(self.session)
        self.cabinet_id = cabinet_id

        self.selected_accessories = []

        self.init_ui()
        self.load_accessories()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Wybierz akcesoria")
        self.resize(600, 500)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Search and filter
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_label = QLabel("Szukaj:")
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Wpisz nazwę lub SKU...")
        self.search_edit.textChanged.connect(self.filter_accessories)
        search_layout.addWidget(self.search_edit)

        self.add_accessory_btn = QPushButton("Nowe akcesorium")
        self.add_accessory_btn.setIcon(get_icon("add"))
        self.add_accessory_btn.clicked.connect(self.add_new_accessory)
        search_layout.addWidget(self.add_accessory_btn)

        main_layout.addWidget(search_frame)

        # Accessories table
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table_view)

        # Quantity selection
        quantity_frame = QFrame()
        quantity_layout = QHBoxLayout(quantity_frame)
        quantity_layout.setContentsMargins(0, 0, 0, 0)

        quantity_label = QLabel("Ilość:")
        quantity_layout.addWidget(quantity_label)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(100)
        self.quantity_spin.setValue(1)
        quantity_layout.addWidget(self.quantity_spin)

        quantity_layout.addStretch()

        main_layout.addWidget(quantity_frame)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_accessories(self):
        """Load accessories from database"""
        accessories = self.accessory_service.list_accessories()

        # Create model and set to table view
        self.model = AccessoryModel(accessories)
        self.table_view.setModel(self.model)

        # Set column widths
        self.table_view.setColumnWidth(0, 60)  # ID
        self.table_view.setColumnWidth(2, 120)  # SKU
        self.table_view.setColumnWidth(3, 120)  # Created date

    def filter_accessories(self, text):
        """Filter accessories based on search text"""
        # Implement filtering logic if needed
        pass

    def add_new_accessory(self):
        """Open dialog to add a new accessory"""
        dialog = AccessoryDialog(self.session, parent=self)
        if dialog.exec():
            # Refresh accessory list
            self.load_accessories()

    def accept(self):
        """Handle dialog acceptance"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(
                self, "Wybierz akcesorium", "Proszę wybrać akcesorium."
            )
            return

        row = selected_indexes[0].row()
        accessory = self.model.get_accessory_at_row(row)
        if accessory:
            quantity = self.quantity_spin.value()
            self.selected_accessories = [(accessory, quantity)]
            super().accept()


class AccessoryManagementDialog(QDialog):
    """Dialog for managing cabinet accessories"""

    def __init__(self, db_session: Session, cabinet_id: int, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.accessory_service = AccessoryService(self.session)
        self.cabinet_id = cabinet_id

        self.init_ui()
        self.load_cabinet_accessories()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Zarządzanie akcesoriami")
        self.resize(600, 500)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Header
        header = QLabel("<h3>Akcesoria szafki</h3>")
        main_layout.addWidget(header)

        # Buttons toolbar
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("Dodaj akcesorium")
        self.add_btn.setIcon(get_icon("add"))
        self.add_btn.clicked.connect(self.add_accessory)
        btn_layout.addWidget(self.add_btn)

        btn_layout.addStretch()

        self.edit_btn = QPushButton("Zmień ilość")
        self.edit_btn.setIcon(get_icon("edit"))
        self.edit_btn.setProperty("class", "secondary")
        self.edit_btn.clicked.connect(self.edit_accessory)
        btn_layout.addWidget(self.edit_btn)

        self.remove_btn = QPushButton("Usuń")
        self.remove_btn.setIcon(get_icon("remove"))
        self.remove_btn.setProperty("class", "danger")
        self.remove_btn.clicked.connect(self.remove_accessory)
        btn_layout.addWidget(self.remove_btn)

        main_layout.addLayout(btn_layout)

        # Accessories table
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table_view)

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_cabinet_accessories(self):
        """Load accessories for the current cabinet"""
        # This would typically call a service method to get accessories for a cabinet
        # For now, we'll create a placeholder implementation
        accessories = []  # Replace with actual data

        # Create or update model
        if not hasattr(self, "model") or self.model is None:
            self.model = AccessoryModel(accessories)
            self.table_view.setModel(self.model)
        else:
            self.model.update_accessories(accessories)

    def add_accessory(self):
        """Open dialog to add an accessory to the cabinet"""
        dialog = AccessorySelectionDialog(self.session, self.cabinet_id, parent=self)
        if dialog.exec():
            # Process selected accessories and refresh the view
            if dialog.selected_accessories:
                for accessory, quantity in dialog.selected_accessories:
                    # Add accessory to cabinet
                    # This would typically call a service method
                    pass
                self.load_cabinet_accessories()

    def edit_accessory(self):
        """Edit the quantity of the selected accessory"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(
                self, "Wybierz akcesorium", "Proszę wybrać akcesorium do edycji."
            )
            return

        # Implement editing logic here
        # This would typically open a dialog to edit the quantity

    def remove_accessory(self):
        """Remove the selected accessory from the cabinet"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(
                self, "Wybierz akcesorium", "Proszę wybrać akcesorium do usunięcia."
            )
            return

        row = selected_indexes[0].row()
        accessory = self.model.get_accessory_at_row(row)
        if accessory:
            reply = QMessageBox.question(
                self,
                "Potwierdzenie usunięcia",
                f"Czy na pewno chcesz usunąć akcesorium '{accessory.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                try:
                    # Remove accessory from cabinet
                    # This would typically call a service method
                    self.load_cabinet_accessories()
                except Exception as e:
                    logger.error(f"Error removing accessory: {e}")
                    QMessageBox.critical(
                        self, "Błąd", f"Nie udało się usunąć akcesorium: {str(e)}"
                    )
