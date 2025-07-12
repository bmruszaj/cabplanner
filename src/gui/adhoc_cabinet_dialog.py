from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QSlider,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
import logging

from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project, ProjectCabinet
from src.services.project_service import ProjectService
from src.services.formula_engine import FormulaEngine

# Configure logging
logger = logging.getLogger(__name__)


class AdhocCabinetDialog(QDialog):
    """
    Dialog for adding or editing a custom (ad-hoc) cabinet.

    This dialog handles UI interactions for ad-hoc cabinets and
    delegates business logic to ProjectService and FormulaEngine.
    """

    def __init__(
        self, db_session: Session, project: Project, cabinet_id=None, parent=None
    ):
        super().__init__(parent)
        logger.debug(f"Initializing AdhocCabinetDialog with cabinet_id: {cabinet_id}")

        # Store session, project and services
        self.session = db_session
        self.project = project
        self.cabinet_id = cabinet_id
        self.project_service = ProjectService(self.session)
        self.formula_engine = FormulaEngine(self.session)

        # Load cabinet if editing existing one
        self.cabinet = None
        self.load_cabinet()

        # Initialize UI components
        self.init_ui()

        # Set window title and load data if editing
        if self.cabinet:
            self.setWindowTitle("Edytuj szafkę niestandardową")
            self.load_cabinet_data()
        else:
            self.setWindowTitle("Dodaj szafkę niestandardową")

        logger.debug("AdhocCabinetDialog initialization complete")

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

            # Verify this is an ad-hoc cabinet (not a catalog cabinet)
            if self.cabinet.type_id is not None:
                logger.warning(f"Cabinet ID {self.cabinet_id} is not an ad-hoc cabinet")
                raise ValueError("This is not an ad-hoc cabinet")

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
        self.resize(500, 450)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # Sequence number
        self.sequence_number_spin = QSpinBox()
        self.sequence_number_spin.setMinimum(1)
        self.sequence_number_spin.setMaximum(999)
        form_layout.addRow("Lp.:", self.sequence_number_spin)

        # Dimensions group
        form_layout.addRow(QLabel("Wymiary szafki:"))

        # Width
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setMinimum(100)
        self.width_spin.setMaximum(2000)
        self.width_spin.setSingleStep(10)
        self.width_spin.setSuffix(" mm")
        self.width_spin.valueChanged.connect(self.update_preview)
        form_layout.addRow("Szerokość:", self.width_spin)

        # Height
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setMinimum(100)
        self.height_spin.setMaximum(2000)
        self.height_spin.setSingleStep(10)
        self.height_spin.setSuffix(" mm")
        self.height_spin.valueChanged.connect(self.update_preview)
        form_layout.addRow("Wysokość:", self.height_spin)

        # Depth
        self.depth_spin = QDoubleSpinBox()
        self.depth_spin.setMinimum(100)
        self.depth_spin.setMaximum(1000)
        self.depth_spin.setSingleStep(10)
        self.depth_spin.setSuffix(" mm")
        self.depth_spin.setValue(570)  # Common default depth
        self.depth_spin.valueChanged.connect(self.update_preview)
        form_layout.addRow("Głębokość:", self.depth_spin)

        # Formula offset with slider
        offset_layout = QHBoxLayout()
        self.offset_label = QLabel("-2 mm")

        self.offset_slider = QSlider(Qt.Horizontal)
        self.offset_slider.setMinimum(-20)
        self.offset_slider.setMaximum(20)
        self.offset_slider.setValue(-2)  # Default from Setting model
        self.offset_slider.setTickPosition(QSlider.TicksBelow)
        self.offset_slider.setTickInterval(5)
        self.offset_slider.valueChanged.connect(self.on_offset_changed)

        offset_layout.addWidget(self.offset_slider)
        offset_layout.addWidget(self.offset_label)
        form_layout.addRow("Przesunięcie formuły:", offset_layout)

        # Cabinet appearance
        form_layout.addRow(QLabel("Wygląd szafki:"))

        # Body color
        self.body_color_edit = QLineEdit()
        form_layout.addRow("Kolor korpusu:", self.body_color_edit)

        # Front color
        self.front_color_edit = QLineEdit()
        form_layout.addRow("Kolor frontu:", self.front_color_edit)

        # Handle type
        self.handle_type_edit = QLineEdit()
        form_layout.addRow("Rodzaj uchwytu:", self.handle_type_edit)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999)
        self.quantity_spin.setValue(1)
        form_layout.addRow("Ilość:", self.quantity_spin)

        # Preview section
        form_layout.addRow(QLabel("Podgląd obliczeń:"))
        self.preview_label = QLabel("...")
        self.preview_label.setWordWrap(True)
        form_layout.addRow(self.preview_label)

        main_layout.addLayout(form_layout)

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_cabinet_data(self):
        """Load existing cabinet data into form fields"""
        try:
            if not self.cabinet:
                logger.warning("Attempted to load data from None cabinet")
                return

            logger.debug(f"Loading data for cabinet ID: {self.cabinet.id}")

            self.sequence_number_spin.setValue(self.cabinet.sequence_number)

            if self.cabinet.adhoc_width_mm is not None:
                self.width_spin.setValue(self.cabinet.adhoc_width_mm)

            if self.cabinet.adhoc_height_mm is not None:
                self.height_spin.setValue(self.cabinet.adhoc_height_mm)

            if self.cabinet.adhoc_depth_mm is not None:
                self.depth_spin.setValue(self.cabinet.adhoc_depth_mm)

            if self.cabinet.formula_offset_mm is not None:
                offset = int(self.cabinet.formula_offset_mm)
                self.offset_slider.setValue(offset)
                self.offset_label.setText(f"{offset} mm")

            self.body_color_edit.setText(self.cabinet.body_color)
            self.front_color_edit.setText(self.cabinet.front_color)
            self.handle_type_edit.setText(self.cabinet.handle_type)
            self.quantity_spin.setValue(self.cabinet.quantity)

            # Update preview after loading all values
            self.update_preview()

        except Exception as e:
            logger.error(f"Error loading cabinet data: {str(e)}")
            QMessageBox.warning(
                self,
                "Błąd",
                f"Nie wszystkie dane szafki zostały wczytane prawidłowo: {str(e)}"
            )

    def on_offset_changed(self, value):
        """Handle changes to the offset slider"""
        try:
            self.offset_label.setText(f"{value} mm")
            self.update_preview()
        except Exception as e:
            logger.error(f"Error updating offset: {str(e)}")

    def update_preview(self):
        """Update the preview of calculated dimensions"""
        try:
            width = self.width_spin.value()
            height = self.height_spin.value()
            depth = self.depth_spin.value()
            offset = self.offset_slider.value()

            logger.debug(f"Updating preview with dimensions: {width}x{height}x{depth}, offset: {offset}")

            # Calculate dimensions using FormulaEngine
            result = self.formula_engine.compute(
                width_mm=width,
                height_mm=height,
                depth_mm=depth,
                formula_offset_mm=offset
            )

            # Format preview text
            preview_text = (
                f"<b>Elementy:</b><br>"
                f"Boki: 2x {result.get('bok_w_mm', 0):.1f} x {result.get('bok_h_mm', 0):.1f} mm<br>"
                f"Wieńce: 2x {result.get('wieniec_w_mm', 0):.1f} x {result.get('wieniec_h_mm', 0):.1f} mm<br>"
                f"Plecy: 1x {result.get('plyta_tylna_w_mm', 0):.1f} x {result.get('plyta_tylna_h_mm', 0):.1f} mm<br>"
            )

            if 'polka_w_mm' in result and 'polka_h_mm' in result:
                preview_text += f"Półki: 2x {result.get('polka_w_mm', 0):.1f} x {result.get('polka_h_mm', 0):.1f} mm<br>"

            if 'front_w_mm' in result and 'front_h_mm' in result:
                preview_text += f"Front: 1x {result.get('front_w_mm', 0):.1f} x {result.get('front_h_mm', 0):.1f} mm<br>"

            self.preview_label.setText(preview_text)

        except Exception as e:
            logger.error(f"Error updating preview: {str(e)}")
            self.preview_label.setText(f"Błąd obliczeń: {str(e)}")

    def get_next_sequence_number(self):
        """Get the next available sequence number for a new cabinet"""
        try:
            next_seq = self.project_service.get_next_cabinet_sequence(self.project.id)
            logger.debug(f"Next sequence number: {next_seq}")
            return next_seq
        except Exception as e:
            logger.error(f"Error getting next sequence number: {str(e)}")
            return 1  # Fallback to 1

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

        return True, ""

    def collect_cabinet_data(self) -> dict:
        """Collect form data into a dictionary ready for service use"""
        return {
            "body_color": self.body_color_edit.text().strip(),
            "front_color": self.front_color_edit.text().strip(),
            "handle_type": self.handle_type_edit.text().strip(),
            "quantity": self.quantity_spin.value(),
            "type_id": None,  # Ad-hoc cabinet (no catalog type)
            "adhoc_width_mm": self.width_spin.value(),
            "adhoc_height_mm": self.height_spin.value(),
            "adhoc_depth_mm": self.depth_spin.value(),
            "formula_offset_mm": float(self.offset_slider.value())
        }

    def accept(self):
        """Handle dialog acceptance (OK button)"""
        logger.debug("AdhocCabinetDialog accept button clicked")

        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            logger.debug(f"Validation failed: {error_message}")
            QMessageBox.warning(self, "Brakujące dane", error_message)
            return

        # Collect form data
        cabinet_data = self.collect_cabinet_data()
        logger.debug(f"Collected cabinet data: {cabinet_data}")

        try:
            if self.cabinet:
                # Update existing cabinet
                logger.info(f"Updating existing ad-hoc cabinet ID: {self.cabinet.id}")
                self.project_service.update_cabinet(self.cabinet.id, **cabinet_data)
                logger.info(f"Ad-hoc cabinet ID: {self.cabinet.id} updated successfully")
            else:
                # Create new cabinet
                sequence_number = self.sequence_number_spin.value()
                cabinet_data["sequence_number"] = sequence_number

                logger.info(f"Creating new ad-hoc cabinet in project ID: {self.project.id}")
                new_cabinet = self.project_service.add_cabinet(self.project.id, **cabinet_data)
                logger.info(f"New ad-hoc cabinet created with ID: {new_cabinet.id}")

            super().accept()  # Close the dialog with accept status

        except ValueError as e:
            # Handle validation errors from service
            logger.warning(f"Validation error in service: {str(e)}")
            QMessageBox.warning(self, "Nieprawidłowe dane", str(e))
        except Exception as e:
            # Handle other errors
            logger.error(f"Error saving ad-hoc cabinet: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {str(e)}")

    def showEvent(self, event):
        """Called when dialog is shown"""
        super().showEvent(event)

        try:
            # If creating a new cabinet, set the next available sequence number
            if not self.cabinet:
                next_seq = self.get_next_sequence_number()
                self.sequence_number_spin.setValue(next_seq)

            # Update preview when dialog is shown
            self.update_preview()
        except Exception as e:
            logger.error(f"Error in showEvent: {str(e)}")
