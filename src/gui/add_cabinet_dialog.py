from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDialogButtonBox,
    QLabel,
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
import logging

from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project, CabinetType, ProjectCabinet
from src.services.cabinet_type_service import CabinetTypeService
from src.services.project_service import ProjectService

# Configure logging
logger = logging.getLogger(__name__)


class CabinetTypeTableModel(QAbstractTableModel):
    """Model for displaying cabinet types in a table view"""

    def __init__(self, cabinet_types, parent=None):
        super().__init__(parent)
        self.cabinet_types = cabinet_types
        self.headers = [
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
                return cabinet_type.nazwa
            elif col == 1:
                return cabinet_type.kitchen_type
            elif col == 2:
                return "Tak" if cabinet_type.hdf_plecy else "Nie"
            elif col == 3:
                return str(cabinet_type.listwa_count)
            elif col == 4:
                return str(cabinet_type.wieniec_count)
            elif col == 5:
                return str(cabinet_type.bok_count)
            elif col == 6:
                return str(cabinet_type.front_count)
            elif col == 7:
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


class AddCabinetDialog(QDialog):
    """
    Dialog for adding a cabinet from catalog to a project.

    This dialog handles UI interactions for catalog cabinet selection
    and delegates business logic to CabinetTypeService and ProjectService.
    """

    def __init__(self, db_session: Session, project: Project, cabinet_id=None, parent=None):
        super().__init__(parent)
        logger.debug(f"Initializing AddCabinetDialog with cabinet_id: {cabinet_id}")

        # Store session, project and services
        self.session = db_session
        self.project = project
        self.cabinet_id = cabinet_id

        self.cabinet_type_service = CabinetTypeService(self.session)
        self.project_service = ProjectService(self.session)

        # Load cabinet if editing existing one
        self.cabinet = None
        self.load_cabinet()

        # Initialize UI components
        self.init_ui()

        # Load cabinet types and populate table
        self.load_cabinet_types()

        # Set window title and load data if editing
        if self.cabinet:
            self.setWindowTitle("Edytuj szafkę z katalogu")
            self.load_cabinet_data()
        else:
            self.setWindowTitle("Dodaj szafkę z katalogu")

        logger.debug("AddCabinetDialog initialization complete")

    def load_cabinet(self):
        """Load cabinet from database if editing an existing cabinet"""
        if not self.cabinet_id:
            return

        try:
            logger.debug(f"Loading cabinet with ID: {self.cabinet_id}")
            self.cabinet = self.project_service.get_cabinet(self.cabinet_id)

            if not self.cabinet:
                logger.warning(f"Cabinet with ID {self.cabinet_id} not found")
                raise ValueError(f"Cabinet with ID {self.cabinet_id} not found")

            # Verify this is a catalog cabinet (has a type_id)
            if not self.cabinet.type_id:
                logger.warning(f"Cabinet ID {self.cabinet_id} is not a catalog cabinet")
                raise ValueError("This is not a catalog cabinet")

        except Exception as e:
            logger.error(f"Error loading cabinet: {str(e)}")
            QMessageBox.critical(
                self,
                "Błąd",
                f"Wystąpił błąd podczas wczytywania szafki: {str(e)}"
            )
            self.reject()  # Close dialog on error

    def init_ui(self):
        """Initialize the UI components"""
        self.resize(800, 600)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Two-pane layout
        pane_layout = QHBoxLayout()

        # Left side: Cabinet types table
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Katalog szafek:"))

        self.cabinet_types_table = QTableView()
        self.cabinet_types_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cabinet_types_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cabinet_types_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        left_layout.addWidget(self.cabinet_types_table)

        pane_layout.addLayout(left_layout, 2)  # 2:1 ratio

        # Right side: Cabinet details form
        right_layout = QFormLayout()
        right_layout.addRow(QLabel("Szczegóły szafki:"))

        # Sequence number
        self.sequence_number_spin = QSpinBox()
        self.sequence_number_spin.setMinimum(1)
        self.sequence_number_spin.setMaximum(999)
        right_layout.addRow("Lp.:", self.sequence_number_spin)

        # Body color
        self.body_color_edit = QLineEdit()
        right_layout.addRow("Kolor korpusu:", self.body_color_edit)

        # Front color
        self.front_color_edit = QLineEdit()
        right_layout.addRow("Kolor frontu:", self.front_color_edit)

        # Handle type
        self.handle_type_edit = QLineEdit()
        right_layout.addRow("Rodzaj uchwytu:", self.handle_type_edit)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999)
        self.quantity_spin.setValue(1)
        right_layout.addRow("Ilość:", self.quantity_spin)

        # Formula offset (advanced)
        self.offset_spin = QSpinBox()
        self.offset_spin.setMinimum(-100)
        self.offset_spin.setMaximum(100)
        self.offset_spin.setValue(-2)  # Default from Setting model
        self.offset_spin.setSuffix(" mm")
        right_layout.addRow("Przesunięcie formuły:", self.offset_spin)

        # Selected cabinet type info
        self.selected_type_label = QLabel("Wybierz typ szafki z listy")
        self.selected_type_label.setWordWrap(True)
        right_layout.addRow("Wybrana szafka:", self.selected_type_label)

        pane_layout.addLayout(right_layout, 1)  # 2:1 ratio

        main_layout.addLayout(pane_layout)

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Disable OK button initially until a cabinet type is selected
        if not self.cabinet:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def load_cabinet_types(self):
        """Load cabinet types filtered by project's kitchen type"""
        try:
            logger.debug(f"Loading cabinet types for kitchen type: {self.project.kitchen_type}")
            cabinet_types = self.cabinet_type_service.list_cabinet_types(
                kitchen_type=self.project.kitchen_type
            )
            logger.debug(f"Loaded {len(cabinet_types)} cabinet types")

            # Create model and set it to table view
            self.cabinet_type_model = CabinetTypeTableModel(cabinet_types)
            self.cabinet_types_table.setModel(self.cabinet_type_model)

            # Now connect the selection signal after the model is set
            self.cabinet_types_table.selectionModel().selectionChanged.connect(self.on_cabinet_type_selected)

        except Exception as e:
            logger.error(f"Error loading cabinet types: {str(e)}")
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie udało się załadować typów szafek: {str(e)}"
            )

    def load_cabinet_data(self):
        """Load existing cabinet data into form fields"""
        try:
            if not self.cabinet:
                logger.warning("Attempted to load data from None cabinet")
                return

            logger.debug(f"Loading data for cabinet ID: {self.cabinet.id}")

            # Set form values from cabinet
            self.sequence_number_spin.setValue(self.cabinet.sequence_number)
            self.body_color_edit.setText(self.cabinet.body_color)
            self.front_color_edit.setText(self.cabinet.front_color)
            self.handle_type_edit.setText(self.cabinet.handle_type)
            self.quantity_spin.setValue(self.cabinet.quantity)

            if self.cabinet.formula_offset_mm is not None:
                self.offset_spin.setValue(int(self.cabinet.formula_offset_mm))

            # Select the cabinet type in the table
            logger.debug(f"Selecting cabinet type ID: {self.cabinet.type_id}")
            self.select_cabinet_type_row(self.cabinet.type_id)

        except Exception as e:
            logger.error(f"Error loading cabinet data: {str(e)}")
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie wszystkie dane szafki zostały wczytane prawidłowo: {str(e)}"
            )

    def select_cabinet_type_row(self, type_id):
        """Select the row in the table view corresponding to the cabinet type ID"""
        try:
            for row in range(self.cabinet_type_model.rowCount()):
                cabinet_type = self.cabinet_type_model.get_cabinet_type_at_row(row)
                if cabinet_type and cabinet_type.id == type_id:
                    logger.debug(f"Found cabinet type at row {row}")
                    self.cabinet_types_table.selectRow(row)
                    break
        except Exception as e:
            logger.error(f"Error selecting cabinet type row: {str(e)}")

    def on_cabinet_type_selected(self):
        """Handle cabinet type selection in the table view"""
        selected_indexes = self.cabinet_types_table.selectionModel().selectedRows()
        if not selected_indexes:
            logger.debug("No cabinet type selected")
            self.selected_type_label.setText("Wybierz typ szafki z listy")
            if not self.cabinet:
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            return

        try:
            row = selected_indexes[0].row()
            cabinet_type = self.cabinet_type_model.get_cabinet_type_at_row(row)

            if cabinet_type:
                logger.debug(f"Selected cabinet type: {cabinet_type.nazwa}")
                self.selected_type_label.setText(f"{cabinet_type.nazwa} ({cabinet_type.kitchen_type})")
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        except Exception as e:
            logger.error(f"Error handling cabinet type selection: {str(e)}")

    def get_next_sequence_number(self):
        """Get the next available sequence number for a new cabinet"""
        try:
            next_seq = self.project_service.get_next_cabinet_sequence(self.project.id)
            logger.debug(f"Next sequence number: {next_seq}")
            return next_seq
        except Exception as e:
            logger.error(f"Error getting next sequence number: {str(e)}")
            return 1  # Fallback to 1

    def get_selected_cabinet_type(self):
        """Get the currently selected cabinet type"""
        selected_indexes = self.cabinet_types_table.selectionModel().selectedRows()
        if not selected_indexes:
            logger.debug("No cabinet type selected when trying to get selected type")
            return None

        row = selected_indexes[0].row()
        cabinet_type = self.cabinet_type_model.get_cabinet_type_at_row(row)
        logger.debug(f"Selected cabinet type ID: {cabinet_type.id if cabinet_type else None}")
        return cabinet_type

    def validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs and return (is_valid, error_message)"""
        # Validate required fields
        body_color = self.body_color_edit.text().strip()
        front_color = self.front_color_edit.text().strip()
        handle_type = self.handle_type_edit.text().strip()

        if not body_color:
            return False, "Kolor korpusu jest wymagany."

        if not front_color:
            return False, "Kolor frontu jest wymagany."

        if not handle_type:
            return False, "Rodzaj uchwytu jest wymagany."

        # Check if cabinet type is selected
        cabinet_type = self.get_selected_cabinet_type()
        if not cabinet_type:
            return False, "Proszę wybrać typ szafki z katalogu."

        return True, ""

    def collect_cabinet_data(self) -> dict:
        """Collect form data into a dictionary ready for service use"""
        cabinet_type = self.get_selected_cabinet_type()
        if not cabinet_type:
            logger.error("Attempting to collect data without a selected cabinet type")
            raise ValueError("No cabinet type selected")

        return {
            "body_color": self.body_color_edit.text().strip(),
            "front_color": self.front_color_edit.text().strip(),
            "handle_type": self.handle_type_edit.text().strip(),
            "quantity": self.quantity_spin.value(),
            "formula_offset_mm": float(self.offset_spin.value()),
            "type_id": cabinet_type.id
        }

    def accept(self):
        """Handle dialog acceptance (OK button)"""
        logger.debug("AddCabinetDialog accept button clicked")

        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            logger.debug(f"Validation failed: {error_message}")
            QMessageBox.warning(self, "Brakujące dane", error_message)
            return

        try:
            # Collect form data
            cabinet_data = self.collect_cabinet_data()
            logger.debug(f"Collected cabinet data: {cabinet_data}")

            if self.cabinet:
                # Update existing cabinet
                logger.info(f"Updating existing cabinet ID: {self.cabinet.id}")
                self.project_service.update_cabinet(self.cabinet.id, **cabinet_data)
                logger.info(f"Cabinet ID: {self.cabinet.id} updated successfully")
            else:
                # Create new cabinet
                sequence_number = self.sequence_number_spin.value()
                cabinet_data["sequence_number"] = sequence_number

                logger.info(f"Creating new catalog cabinet in project ID: {self.project.id}")
                new_cabinet = self.project_service.add_cabinet(self.project.id, **cabinet_data)
                logger.info(f"New catalog cabinet created with ID: {new_cabinet.id}")

            super().accept()  # Close dialog with accept status

        except ValueError as e:
            # Handle validation errors from service
            logger.warning(f"Validation error in service: {str(e)}")
            QMessageBox.warning(self, "Nieprawidłowe dane", str(e))
        except Exception as e:
            # Handle other errors
            logger.error(f"Error saving catalog cabinet: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {str(e)}")

    def showEvent(self, event):
        """Called when dialog is shown"""
        super().showEvent(event)

        try:
            # If creating a new cabinet, set the next available sequence number
            if not self.cabinet:
                next_seq = self.get_next_sequence_number()
                self.sequence_number_spin.setValue(next_seq)
        except Exception as e:
            logger.error(f"Error in showEvent: {str(e)}")
