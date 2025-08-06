"""
Modern cabinet catalog window for the Cabplanner application.
"""

import logging
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
    QFrame,
    QGroupBox,
    QStackedWidget,
    QSizePolicy,
    QScrollArea,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal

from sqlalchemy.orm import Session

from src.services.cabinet_type_service import CabinetTypeService
from src.gui.resources.resources import get_icon

# Configure logging
logger = logging.getLogger(__name__)


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

        elif role == Qt.TextAlignmentRole:
            col = index.column()
            if col in [0, 4, 5, 6, 7, 8]:  # IDs and counts
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

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
        self.resize(600, 700)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Create a scrollable form area
        scroll_widget = QWidget()
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setSpacing(20)

        # Basic info group
        basic_group = QGroupBox("Podstawowe informacje")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(10)

        self.nazwa_edit = QLineEdit()
        basic_layout.addRow("Nazwa:", self.nazwa_edit)

        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(["LOFT", "PARIS", "WINO"])
        basic_layout.addRow("Typ kuchni:", self.kitchen_type_combo)

        self.hdf_plecy_check = QCheckBox()
        basic_layout.addRow("Plecy HDF:", self.hdf_plecy_check)

        form_layout.addWidget(basic_group)

        # Listwa section
        listwa_group = QGroupBox("Listwy")
        listwa_layout = QFormLayout(listwa_group)

        self.listwa_count_spin = QSpinBox()
        self.listwa_count_spin.setRange(0, 10)
        listwa_layout.addRow("Ilość:", self.listwa_count_spin)

        self.listwa_w_spin = QDoubleSpinBox()
        self.listwa_w_spin.setRange(0, 2000)
        self.listwa_w_spin.setSuffix(" mm")
        listwa_layout.addRow("Szerokość:", self.listwa_w_spin)

        self.listwa_h_spin = QDoubleSpinBox()
        self.listwa_h_spin.setRange(0, 2000)
        self.listwa_h_spin.setSuffix(" mm")
        listwa_layout.addRow("Wysokość:", self.listwa_h_spin)

        form_layout.addWidget(listwa_group)

        # Wieniec section
        wieniec_group = QGroupBox("Wieńce")
        wieniec_layout = QFormLayout(wieniec_group)

        self.wieniec_count_spin = QSpinBox()
        self.wieniec_count_spin.setRange(0, 10)
        wieniec_layout.addRow("Ilość:", self.wieniec_count_spin)

        self.wieniec_w_spin = QDoubleSpinBox()
        self.wieniec_w_spin.setRange(0, 2000)
        self.wieniec_w_spin.setSuffix(" mm")
        wieniec_layout.addRow("Szerokość:", self.wieniec_w_spin)

        self.wieniec_h_spin = QDoubleSpinBox()
        self.wieniec_h_spin.setRange(0, 2000)
        self.wieniec_h_spin.setSuffix(" mm")
        wieniec_layout.addRow("Wysokość:", self.wieniec_h_spin)

        form_layout.addWidget(wieniec_group)

        # Bok section
        bok_group = QGroupBox("Boki")
        bok_layout = QFormLayout(bok_group)

        self.bok_count_spin = QSpinBox()
        self.bok_count_spin.setRange(0, 10)
        bok_layout.addRow("Ilość:", self.bok_count_spin)

        self.bok_w_spin = QDoubleSpinBox()
        self.bok_w_spin.setRange(0, 2000)
        self.bok_w_spin.setSuffix(" mm")
        bok_layout.addRow("Szerokość:", self.bok_w_spin)

        self.bok_h_spin = QDoubleSpinBox()
        self.bok_h_spin.setRange(0, 2000)
        self.bok_h_spin.setSuffix(" mm")
        bok_layout.addRow("Wysokość:", self.bok_h_spin)

        form_layout.addWidget(bok_group)

        # Front section
        front_group = QGroupBox("Fronty")
        front_layout = QFormLayout(front_group)

        self.front_count_spin = QSpinBox()
        self.front_count_spin.setRange(0, 10)
        front_layout.addRow("Ilość:", self.front_count_spin)

        self.front_w_spin = QDoubleSpinBox()
        self.front_w_spin.setRange(0, 2000)
        self.front_w_spin.setSuffix(" mm")
        front_layout.addRow("Szerokość:", self.front_w_spin)

        self.front_h_spin = QDoubleSpinBox()
        self.front_h_spin.setRange(0, 2000)
        self.front_h_spin.setSuffix(" mm")
        front_layout.addRow("Wysokość:", self.front_h_spin)

        form_layout.addWidget(front_group)

        # Polka section
        polka_group = QGroupBox("Półki")
        polka_layout = QFormLayout(polka_group)

        self.polka_count_spin = QSpinBox()
        self.polka_count_spin.setRange(0, 10)
        polka_layout.addRow("Ilość:", self.polka_count_spin)

        self.polka_w_spin = QDoubleSpinBox()
        self.polka_w_spin.setRange(0, 2000)
        self.polka_w_spin.setSuffix(" mm")
        polka_layout.addRow("Szerokość:", self.polka_w_spin)

        self.polka_h_spin = QDoubleSpinBox()
        self.polka_h_spin.setRange(0, 2000)
        self.polka_h_spin.setSuffix(" mm")
        polka_layout.addRow("Wysokość:", self.polka_h_spin)

        form_layout.addWidget(polka_group)

        # Add the form to the main layout
        main_layout.addWidget(scroll_widget)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_cabinet_type_data(self):
        """Load cabinet type data into the form"""
        if not self.cabinet_type:
            return

        # Basic info
        self.nazwa_edit.setText(self.cabinet_type.nazwa)

        index = self.kitchen_type_combo.findText(self.cabinet_type.kitchen_type)
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
        if not nazwa:
            QMessageBox.warning(self, "Błąd", "Nazwa szafki jest wymagana.")
            self.nazwa_edit.setFocus()
            return

        kitchen_type = self.kitchen_type_combo.currentText()
        hdf_plecy = self.hdf_plecy_check.isChecked()

        # Get values for measurements
        listwa_count = self.listwa_count_spin.value()
        listwa_w_mm = self.listwa_w_spin.value() if listwa_count > 0 else None
        listwa_h_mm = self.listwa_h_spin.value() if listwa_count > 0 else None

        wieniec_count = self.wieniec_count_spin.value()
        wieniec_w_mm = self.wieniec_w_spin.value() if wieniec_count > 0 else None
        wieniec_h_mm = self.wieniec_h_spin.value() if wieniec_count > 0 else None

        bok_count = self.bok_count_spin.value()
        bok_w_mm = self.bok_w_spin.value() if bok_count > 0 else None
        bok_h_mm = self.bok_h_spin.value() if bok_count > 0 else None

        front_count = self.front_count_spin.value()
        front_w_mm = self.front_w_spin.value() if front_count > 0 else None
        front_h_mm = self.front_h_spin.value() if front_count > 0 else None

        polka_count = self.polka_count_spin.value()
        polka_w_mm = self.polka_w_spin.value() if polka_count > 0 else None
        polka_h_mm = self.polka_h_spin.value() if polka_count > 0 else None

        try:
            cabinet_data = {
                "nazwa": nazwa,
                "kitchen_type": kitchen_type,
                "hdf_plecy": hdf_plecy,
                "listwa_count": listwa_count,
                "listwa_w_mm": listwa_w_mm,
                "listwa_h_mm": listwa_h_mm,
                "wieniec_count": wieniec_count,
                "wieniec_w_mm": wieniec_w_mm,
                "wieniec_h_mm": wieniec_h_mm,
                "bok_count": bok_count,
                "bok_w_mm": bok_w_mm,
                "bok_h_mm": bok_h_mm,
                "front_count": front_count,
                "front_w_mm": front_w_mm,
                "front_h_mm": front_h_mm,
                "polka_count": polka_count,
                "polka_w_mm": polka_w_mm,
                "polka_h_mm": polka_h_mm,
            }

            if self.cabinet_type_id:
                # Update existing cabinet type
                self.cabinet_type_service.update_cabinet_type(
                    self.cabinet_type_id, **cabinet_data
                )
                logger.info(f"Updated cabinet type ID: {self.cabinet_type_id}")
            else:
                # Create new cabinet type
                new_cabinet = self.cabinet_type_service.create_cabinet_type(
                    **cabinet_data
                )
                logger.info(f"Created new cabinet type ID: {new_cabinet.id}")

            super().accept()

        except Exception as e:
            logger.error(f"Error saving cabinet type: {e}")
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zapisać typu szafki: {str(e)}"
            )


class CabinetTypeCard(QFrame):
    """A card widget displaying cabinet type information"""

    clicked = Signal(object)  # Signal emits the cabinet type object

    def __init__(self, cabinet_type, parent=None):
        super().__init__(parent)
        self.cabinet_type = cabinet_type
        self.setObjectName("cabinetTypeCard")
        self.setProperty("class", "card")
        self.setFixedHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.init_ui()

    def init_ui(self):
        """Initialize the UI components for this card"""
        layout = QVBoxLayout(self)

        # Header with cabinet name and type
        header_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{self.cabinet_type.nazwa}</b>")
        name_label.setStyleSheet("font-size: 14pt;")
        header_layout.addWidget(name_label)

        kitchen_type_label = QLabel(self.cabinet_type.kitchen_type)
        kitchen_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(kitchen_type_label)
        layout.addLayout(header_layout)

        # Cabinet details in a grid
        details_layout = QFormLayout()
        details_layout.setHorizontalSpacing(20)
        details_layout.setVerticalSpacing(5)

        # Combine component counts in a readable format
        components_label = QLabel(
            f"Boki: {self.cabinet_type.bok_count}, "
            f"Wieńce: {self.cabinet_type.wieniec_count}, "
            f"Półki: {self.cabinet_type.polka_count}, "
            f"Fronty: {self.cabinet_type.front_count}, "
            f"Listwy: {self.cabinet_type.listwa_count}"
        )
        components_label.setWordWrap(True)
        details_layout.addRow("Komponenty:", components_label)

        # HDF back indicator
        hdf_value = "Tak" if self.cabinet_type.hdf_plecy else "Nie"
        details_layout.addRow("Plecy HDF:", QLabel(hdf_value))

        layout.addLayout(details_layout)

        # Button bar at bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        edit_btn = QPushButton("Edytuj")
        edit_btn.setProperty("class", "secondary")
        edit_btn.setIcon(get_icon("edit"))
        edit_btn.clicked.connect(lambda: self.clicked.emit(self.cabinet_type))
        button_layout.addWidget(edit_btn)

        layout.addLayout(button_layout)

        # Add stretch to push content to the top
        layout.addStretch()

    def mousePressEvent(self, event):
        """Handle mouse press events to make the entire card clickable"""
        super().mousePressEvent(event)
        self.clicked.emit(self.cabinet_type)


class CabinetCatalogWindow(QMainWindow):
    """Modern cabinet catalog window for the Cabplanner application"""

    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.cabinet_type_service = CabinetTypeService(self.session)

        # Track the current view mode
        self.current_view_mode = "table"  # Default to table view

        self.init_ui()
        self.load_cabinet_types()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Katalog szafek")
        self.resize(1000, 600)

        # Create central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Header section with title and filtering
        header_frame = QFrame()
        header_frame.setProperty("class", "card")
        header_layout = QHBoxLayout(header_frame)

        # Title
        title_label = QLabel("<h2>Katalog szafek</h2>")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Filter by kitchen type
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtruj typ kuchni:"))

        self.filter_kitchen_combo = QComboBox()
        self.filter_kitchen_combo.addItem("Wszystkie")
        self.filter_kitchen_combo.addItems(["LOFT", "PARIS", "WINO"])
        self.filter_kitchen_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_kitchen_combo)

        header_layout.addLayout(filter_layout)

        main_layout.addWidget(header_frame)

        # Toolbar with actions
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("Dodaj szafkę")
        self.add_btn.setIcon(get_icon("add"))
        self.add_btn.clicked.connect(self.add_cabinet_type)
        btn_layout.addWidget(self.add_btn)

        # Toggle view buttons (Cards vs Table)
        self.card_view_btn = QPushButton("Karty")
        self.card_view_btn.setCheckable(True)
        self.card_view_btn.clicked.connect(lambda: self.set_view_mode("cards"))
        btn_layout.addWidget(self.card_view_btn)

        self.table_view_btn = QPushButton("Tabela")
        self.table_view_btn.setCheckable(True)
        self.table_view_btn.setChecked(True)  # Default to table view
        self.table_view_btn.clicked.connect(lambda: self.set_view_mode("table"))
        btn_layout.addWidget(self.table_view_btn)

        btn_layout.addStretch()

        self.edit_btn = QPushButton("Edytuj")
        self.edit_btn.setIcon(get_icon("edit"))
        self.edit_btn.setProperty("class", "secondary")
        self.edit_btn.clicked.connect(self.edit_cabinet_type)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Usuń")
        self.delete_btn.setIcon(get_icon("delete"))
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_cabinet_type)
        btn_layout.addWidget(self.delete_btn)

        main_layout.addLayout(btn_layout)

        # Stacked widget to switch between table and card views
        self.view_stack = QStackedWidget()
        main_layout.addWidget(self.view_stack)

        # Table view
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.doubleClicked.connect(self.edit_cabinet_type)
        self.view_stack.addWidget(self.table_view)

        # Card view (scrollable grid of cabinet cards)
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_scroll.setWidget(self.card_container)
        self.view_stack.addWidget(self.card_scroll)

        # Set the default view mode
        self.set_view_mode("table")

        # Status bar
        self.statusBar().showMessage("Gotowy")

    def set_view_mode(self, mode):
        """Switch between card and table view modes"""
        self.current_view_mode = mode

        if mode == "cards":
            self.view_stack.setCurrentIndex(1)  # Card view is second widget
            self.card_view_btn.setChecked(True)
            self.table_view_btn.setChecked(False)
        else:  # Default to table view
            self.view_stack.setCurrentIndex(0)  # Table view is first widget
            self.table_view_btn.setChecked(True)
            self.card_view_btn.setChecked(False)

    def clear_card_layout(self):
        """Clear all widgets from the card layout"""
        while self.card_layout.count() > 0:
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_cabinet_types(self):
        """Load cabinet types from database with optional filtering"""
        kitchen_type = None
        filter_text = self.filter_kitchen_combo.currentText()

        if filter_text != "Wszystkie":
            kitchen_type = filter_text

        cabinet_types = self.cabinet_type_service.list_cabinet_types(
            kitchen_type=kitchen_type
        )

        # Update table view
        if not hasattr(self, "model"):
            self.model = CabinetTypeModel(cabinet_types)
            self.table_view.setModel(self.model)

            # Set column widths
            self.table_view.setColumnWidth(0, 60)  # ID
            for i in range(3, 9):  # Count columns
                self.table_view.setColumnWidth(i, 70)
        else:
            self.model.update_cabinet_types(cabinet_types)

        # Update card view
        self.clear_card_layout()
        for cabinet_type in cabinet_types:
            card = CabinetTypeCard(cabinet_type)
            card.clicked.connect(self.on_card_clicked)
            self.card_layout.addWidget(card)

        # Add stretch at the end to keep cards at the top
        self.card_layout.addStretch()

        # Update status bar
        self.statusBar().showMessage(f"Załadowano {len(cabinet_types)} typów szafek")

    def on_card_clicked(self, cabinet_type):
        """Handle cabinet card click event"""
        self.edit_cabinet_type(cabinet_type)

    def apply_filters(self):
        """Apply selected filters and refresh the table"""
        self.load_cabinet_types()

    def add_cabinet_type(self):
        """Open dialog to add a new cabinet type"""
        dialog = CabinetTypeDialog(self.session, parent=self)
        if dialog.exec():
            self.load_cabinet_types()

    def edit_cabinet_type(self, cabinet_type_or_index=None):
        """Open dialog to edit the selected cabinet type"""
        cabinet_type = None

        # Handle direct cabinet type object from card click
        if hasattr(cabinet_type_or_index, "id"):
            cabinet_type = cabinet_type_or_index
        # Handle table selection
        elif self.current_view_mode == "table":
            selected_indexes = self.table_view.selectionModel().selectedRows()
            if selected_indexes:
                row = selected_indexes[0].row()
                cabinet_type = self.model.get_cabinet_type_at_row(row)

        if not cabinet_type:
            QMessageBox.information(
                self, "Wybierz szafkę", "Proszę wybrać typ szafki do edycji."
            )
            return

        dialog = CabinetTypeDialog(self.session, cabinet_type.id, parent=self)
        if dialog.exec():
            self.load_cabinet_types()

    def delete_cabinet_type(self):
        """Delete the selected cabinet type"""
        cabinet_type = None

        # Get selected cabinet type from current view mode
        if self.current_view_mode == "table":
            selected_indexes = self.table_view.selectionModel().selectedRows()
            if selected_indexes:
                row = selected_indexes[0].row()
                cabinet_type = self.model.get_cabinet_type_at_row(row)
        else:
            QMessageBox.information(
                self,
                "Wybierz szafkę",
                "Aby usunąć szafkę, wybierz ją w widoku tabeli lub przejdź do edycji.",
            )
            return

        if not cabinet_type:
            QMessageBox.information(
                self, "Wybierz szafkę", "Proszę wybrać typ szafki do usunięcia."
            )
            return

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
                self.statusBar().showMessage("Typ szafki został usunięty")
            except Exception as e:
                logger.error(f"Error deleting cabinet type: {e}")
                QMessageBox.critical(
                    self, "Błąd", f"Nie udało się usunąć typu szafki: {str(e)}"
                )
