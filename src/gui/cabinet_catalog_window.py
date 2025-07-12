from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QTableView,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from sqlalchemy.orm import Session

from src.services.cabinet_type_service import CabinetTypeService


class CabinetTypeModel(QAbstractTableModel):
    """Model for displaying cabinet types in a table view"""

    def __init__(self, cabinet_types, parent=None):
        super().__init__(parent)
        self.cabinet_types = cabinet_types
        self.headers = [
            "ID",
            "Nazwa",
            "Typ kuchni",
            "Plecy HDF",
            "Listwy",
            "Wieńce",
            "Boki",
            "Fronty",
            "Półki",
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self.cabinet_types)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            cabinet_type = self.cabinet_types[index.row()]
            col = index.column()

            if col == 0:
                return cabinet_type.id
            elif col == 1:
                return cabinet_type.nazwa
            elif col == 2:
                return cabinet_type.kitchen_type
            elif col == 3:
                return "Tak" if cabinet_type.hdf_plecy else "Nie"
            elif col == 4:
                return str(cabinet_type.listwa_count)
            elif col == 5:
                return str(cabinet_type.wieniec_count)
            elif col == 6:
                return str(cabinet_type.bok_count)
            elif col == 7:
                return str(cabinet_type.front_count)
            elif col == 8:
                return str(cabinet_type.polka_count)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_cabinet_types(self, cabinet_types):
        self.beginResetModel()
        self.cabinet_types = cabinet_types
        self.endResetModel()

    def get_cabinet_type_at_row(self, row):
        if 0 <= row < len(self.cabinet_types):
            return self.cabinet_types[row]
        return None


class CabinetTypeDialog(QDialog):
    """Dialog for creating or editing a cabinet type"""

    def __init__(self, db_session: Session, cabinet_type_id=None, parent=None):
        super().__init__(parent)

        self.session = db_session
        self.cabinet_type_service = CabinetTypeService(self.session)

        self.cabinet_type_id = cabinet_type_id
        self.cabinet_type = None

        if cabinet_type_id:
            self.cabinet_type = self.cabinet_type_service.get_cabinet_type(
                cabinet_type_id
            )

        self.init_ui()

        if self.cabinet_type:
            self.setWindowTitle("Edytuj typ szafki")
            self.load_cabinet_type_data()
        else:
            self.setWindowTitle("Nowy typ szafki")

    def init_ui(self):
        """Initialize the UI components"""
        self.resize(500, 600)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Form layout for cabinet type details
        form_layout = QFormLayout()

        # Basic info
        self.nazwa_edit = QLineEdit()
        form_layout.addRow("Nazwa:", self.nazwa_edit)

        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(["LOFT", "PARIS", "WINO"])
        form_layout.addRow("Typ kuchni:", self.kitchen_type_combo)

        self.hdf_plecy_check = QCheckBox()
        form_layout.addRow("Plecy HDF:", self.hdf_plecy_check)

        # Listwa section
        form_layout.addRow(QLabel("Listwy:"))

        self.listwa_count_spin = QSpinBox()
        self.listwa_count_spin.setRange(0, 10)
        form_layout.addRow("Ilość:", self.listwa_count_spin)

        self.listwa_w_spin = QDoubleSpinBox()
        self.listwa_w_spin.setRange(0, 2000)
        self.listwa_w_spin.setSuffix(" mm")
        form_layout.addRow("Szerokość:", self.listwa_w_spin)

        self.listwa_h_spin = QDoubleSpinBox()
        self.listwa_h_spin.setRange(0, 2000)
        self.listwa_h_spin.setSuffix(" mm")
        form_layout.addRow("Wysokość:", self.listwa_h_spin)

        # Wieniec section
        form_layout.addRow(QLabel("Wieńce:"))

        self.wieniec_count_spin = QSpinBox()
        self.wieniec_count_spin.setRange(0, 10)
        form_layout.addRow("Ilość:", self.wieniec_count_spin)

        self.wieniec_w_spin = QDoubleSpinBox()
        self.wieniec_w_spin.setRange(0, 2000)
        self.wieniec_w_spin.setSuffix(" mm")
        form_layout.addRow("Szerokość:", self.wieniec_w_spin)

        self.wieniec_h_spin = QDoubleSpinBox()
        self.wieniec_h_spin.setRange(0, 2000)
        self.wieniec_h_spin.setSuffix(" mm")
        form_layout.addRow("Wysokość:", self.wieniec_h_spin)

        # Bok section
        form_layout.addRow(QLabel("Boki:"))

        self.bok_count_spin = QSpinBox()
        self.bok_count_spin.setRange(0, 10)
        form_layout.addRow("Ilość:", self.bok_count_spin)

        self.bok_w_spin = QDoubleSpinBox()
        self.bok_w_spin.setRange(0, 2000)
        self.bok_w_spin.setSuffix(" mm")
        form_layout.addRow("Szerokość:", self.bok_w_spin)

        self.bok_h_spin = QDoubleSpinBox()
        self.bok_h_spin.setRange(0, 2000)
        self.bok_h_spin.setSuffix(" mm")
        form_layout.addRow("Wysokość:", self.bok_h_spin)

        # Front section
        form_layout.addRow(QLabel("Fronty:"))

        self.front_count_spin = QSpinBox()
        self.front_count_spin.setRange(0, 10)
        form_layout.addRow("Ilość:", self.front_count_spin)

        self.front_w_spin = QDoubleSpinBox()
        self.front_w_spin.setRange(0, 2000)
        self.front_w_spin.setSuffix(" mm")
        form_layout.addRow("Szerokość:", self.front_w_spin)

        self.front_h_spin = QDoubleSpinBox()
        self.front_h_spin.setRange(0, 2000)
        self.front_h_spin.setSuffix(" mm")
        form_layout.addRow("Wysokość:", self.front_h_spin)

        # Polka section
        form_layout.addRow(QLabel("Półki:"))

        self.polka_count_spin = QSpinBox()
        self.polka_count_spin.setRange(0, 10)
        form_layout.addRow("Ilość:", self.polka_count_spin)

        self.polka_w_spin = QDoubleSpinBox()
        self.polka_w_spin.setRange(0, 2000)
        self.polka_w_spin.setSuffix(" mm")
        form_layout.addRow("Szerokość:", self.polka_w_spin)

        self.polka_h_spin = QDoubleSpinBox()
        self.polka_h_spin.setRange(0, 2000)
        self.polka_h_spin.setSuffix(" mm")
        form_layout.addRow("Wysokość:", self.polka_h_spin)

        main_layout.addLayout(form_layout)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_cabinet_type_data(self):
        """Load cabinet type data into the form fields"""
        if not self.cabinet_type:
            return

        # Basic info
        self.nazwa_edit.setText(self.cabinet_type.nazwa)

        index = self.kitchen_type_combo.findText(
            self.cabinet_type.kitchen_type, Qt.MatchExactly
        )
        if index >= 0:
            self.kitchen_type_combo.setCurrentIndex(index)

        self.hdf_plecy_check.setChecked(self.cabinet_type.hdf_plecy)

        # Listwa
        self.listwa_count_spin.setValue(self.cabinet_type.listwa_count)
        if self.cabinet_type.listwa_w_mm:
            self.listwa_w_spin.setValue(self.cabinet_type.listwa_w_mm)
        if self.cabinet_type.listwa_h_mm:
            self.listwa_h_spin.setValue(self.cabinet_type.listwa_h_mm)

        # Wieniec
        self.wieniec_count_spin.setValue(self.cabinet_type.wieniec_count)
        if self.cabinet_type.wieniec_w_mm:
            self.wieniec_w_spin.setValue(self.cabinet_type.wieniec_w_mm)
        if self.cabinet_type.wieniec_h_mm:
            self.wieniec_h_spin.setValue(self.cabinet_type.wieniec_h_mm)

        # Bok
        self.bok_count_spin.setValue(self.cabinet_type.bok_count)
        if self.cabinet_type.bok_w_mm:
            self.bok_w_spin.setValue(self.cabinet_type.bok_w_mm)
        if self.cabinet_type.bok_h_mm:
            self.bok_h_spin.setValue(self.cabinet_type.bok_h_mm)

        # Front
        self.front_count_spin.setValue(self.cabinet_type.front_count)
        if self.cabinet_type.front_w_mm:
            self.front_w_spin.setValue(self.cabinet_type.front_w_mm)
        if self.cabinet_type.front_h_mm:
            self.front_h_spin.setValue(self.cabinet_type.front_h_mm)

        # Polka
        self.polka_count_spin.setValue(self.cabinet_type.polka_count)
        if self.cabinet_type.polka_w_mm:
            self.polka_w_spin.setValue(self.cabinet_type.polka_w_mm)
        if self.cabinet_type.polka_h_mm:
            self.polka_h_spin.setValue(self.cabinet_type.polka_h_mm)

    def accept(self):
        """Handle dialog acceptance"""
        nazwa = self.nazwa_edit.text().strip()
        kitchen_type = self.kitchen_type_combo.currentText()

        if not nazwa:
            QMessageBox.warning(self, "Brakujące dane", "Nazwa szafki jest wymagana.")
            return

        try:
            # Collect form data
            cabinet_data = {
                "nazwa": nazwa,
                "kitchen_type": kitchen_type,
                "hdf_plecy": self.hdf_plecy_check.isChecked(),
                "listwa_count": self.listwa_count_spin.value(),
                "listwa_w_mm": self.listwa_w_spin.value()
                if self.listwa_count_spin.value() > 0
                else None,
                "listwa_h_mm": self.listwa_h_spin.value()
                if self.listwa_count_spin.value() > 0
                else None,
                "wieniec_count": self.wieniec_count_spin.value(),
                "wieniec_w_mm": self.wieniec_w_spin.value()
                if self.wieniec_count_spin.value() > 0
                else None,
                "wieniec_h_mm": self.wieniec_h_spin.value()
                if self.wieniec_count_spin.value() > 0
                else None,
                "bok_count": self.bok_count_spin.value(),
                "bok_w_mm": self.bok_w_spin.value()
                if self.bok_count_spin.value() > 0
                else None,
                "bok_h_mm": self.bok_h_spin.value()
                if self.bok_count_spin.value() > 0
                else None,
                "front_count": self.front_count_spin.value(),
                "front_w_mm": self.front_w_spin.value()
                if self.front_count_spin.value() > 0
                else None,
                "front_h_mm": self.front_h_spin.value()
                if self.front_count_spin.value() > 0
                else None,
                "polka_count": self.polka_count_spin.value(),
                "polka_w_mm": self.polka_w_spin.value()
                if self.polka_count_spin.value() > 0
                else None,
                "polka_h_mm": self.polka_h_spin.value()
                if self.polka_count_spin.value() > 0
                else None,
            }

            if self.cabinet_type_id:
                # Update existing cabinet type
                self.cabinet_type = self.cabinet_type_service.update_cabinet_type(
                    self.cabinet_type_id, **cabinet_data
                )
            else:
                # Create new cabinet type
                self.cabinet_type = self.cabinet_type_service.create_cabinet_type(
                    **cabinet_data
                )

            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {str(e)}")


class CabinetCatalogWindow(QMainWindow):
    """Window for managing cabinet catalog (CabinetType)"""

    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)

        self.session = db_session
        self.cabinet_type_service = CabinetTypeService(self.session)

        self.init_ui()
        self.load_cabinet_types()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Katalog szafek")
        self.resize(900, 600)

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Filter controls
        filter_layout = QHBoxLayout()

        self.filter_kitchen_combo = QComboBox()
        self.filter_kitchen_combo.addItem("Wszystkie")
        self.filter_kitchen_combo.addItems(["LOFT", "PARIS", "WINO"])
        self.filter_kitchen_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Filtruj typ kuchni:"))
        filter_layout.addWidget(self.filter_kitchen_combo)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Button controls
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("Dodaj nowy")
        self.add_btn.clicked.connect(self.add_cabinet_type)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edytuj")
        self.edit_btn.clicked.connect(self.edit_cabinet_type)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Usuń")
        self.delete_btn.clicked.connect(self.delete_cabinet_type)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # Cabinet types table
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.doubleClicked.connect(self.edit_cabinet_type)
        main_layout.addWidget(self.table_view)

    def load_cabinet_types(self):
        """Load cabinet types from database with optional filtering"""
        kitchen_type = None
        filter_text = self.filter_kitchen_combo.currentText()

        if filter_text != "Wszystkie":
            kitchen_type = filter_text

        cabinet_types = self.cabinet_type_service.list_cabinet_types(
            kitchen_type=kitchen_type
        )

        # Create or update model
        if not hasattr(self, "model"):
            self.model = CabinetTypeModel(cabinet_types)
            self.table_view.setModel(self.model)
        else:
            self.model.update_cabinet_types(cabinet_types)

    def apply_filters(self):
        """Apply selected filters and refresh the table"""
        self.load_cabinet_types()

    def add_cabinet_type(self):
        """Open dialog to add a new cabinet type"""
        dialog = CabinetTypeDialog(self.session, parent=self)
        if dialog.exec():
            self.load_cabinet_types()

    def edit_cabinet_type(self):
        """Open dialog to edit the selected cabinet type"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(
                self, "Wybierz typ szafki", "Proszę wybrać typ szafki do edycji."
            )
            return

        row = selected_indexes[0].row()
        cabinet_type = self.model.get_cabinet_type_at_row(row)

        if cabinet_type:
            dialog = CabinetTypeDialog(self.session, cabinet_type.id, parent=self)
            if dialog.exec():
                self.load_cabinet_types()

    def delete_cabinet_type(self):
        """Delete the selected cabinet type"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.information(
                self, "Wybierz typ szafki", "Proszę wybrać typ szafki do usunięcia."
            )
            return

        row = selected_indexes[0].row()
        cabinet_type = self.model.get_cabinet_type_at_row(row)

        if cabinet_type:
            reply = QMessageBox.question(
                self,
                "Potwierdzenie usunięcia",
                f"Czy na pewno chcesz usunąć typ szafki '{cabinet_type.nazwa}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                try:
                    self.cabinet_type_service.delete_cabinet_type(cabinet_type.id)
                    self.load_cabinet_types()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Błąd usuwania",
                        f"Nie udało się usunąć typu szafki. Może być używana przez istniejące szafki. Błąd: {str(e)}",
                    )
