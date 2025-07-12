from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt
import logging

from sqlalchemy.orm import Session
from src.services.project_service import ProjectService

# Configure logging
logger = logging.getLogger(__name__)


class ProjectDialog(QDialog):
    """
    Dialog for creating or editing a project.
    Handles UI interactions and delegates data operations to ProjectService.
    """

    def __init__(self, db_session: Session, project_id=None, parent=None):
        super().__init__(parent)
        logger.debug(f"Initializing ProjectDialog with project_id: {project_id}")

        # Store session and create service
        self.session = db_session
        self.project_service = ProjectService(db_session)

        # Store project ID and load project if editing
        self.project_id = project_id
        self.project = None
        self.load_project()

        # Initialize UI components
        self.init_ui()

        # Set window title based on mode
        if self.project:
            self.setWindowTitle("Edytuj projekt")
            self.load_project_data()
        else:
            self.setWindowTitle("Nowy projekt")

        logger.debug("ProjectDialog initialization complete")

    def load_project(self):
        """Load project from database if editing an existing project"""
        if self.project_id:
            try:
                logger.debug(f"Loading project with ID: {self.project_id}")
                self.project = self.project_service.get_project(self.project_id)

                if not self.project:
                    logger.warning(f"Project with ID {self.project_id} not found")
                    QMessageBox.warning(
                        self,
                        "Projekt nie znaleziony",
                        f"Projekt o ID {self.project_id} nie został znaleziony.",
                    )
            except Exception as e:
                logger.error(f"Error loading project: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Błąd",
                    f"Wystąpił błąd podczas wczytywania projektu: {str(e)}",
                )

    def init_ui(self):
        """Initialize the UI components"""
        self.setMinimumWidth(400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Form layout for inputs
        form_layout = QFormLayout()

        # Project name field
        self.name_edit = QLineEdit()
        form_layout.addRow("Nazwa projektu:", self.name_edit)

        # Kitchen type selection
        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(["LOFT", "PARIS", "WINO"])
        form_layout.addRow("Typ kuchni:", self.kitchen_type_combo)

        # Order number field
        self.order_number_edit = QLineEdit()
        form_layout.addRow("Numer zamówienia:", self.order_number_edit)

        # Client information (optional fields)
        form_layout.addRow(QLabel("Informacje o kliencie (opcjonalne):"))

        self.client_name_edit = QLineEdit()
        form_layout.addRow("Imię i nazwisko:", self.client_name_edit)

        self.client_address_edit = QLineEdit()
        form_layout.addRow("Adres:", self.client_address_edit)

        self.client_phone_edit = QLineEdit()
        form_layout.addRow("Telefon:", self.client_phone_edit)

        self.client_email_edit = QLineEdit()
        form_layout.addRow("E-mail:", self.client_email_edit)

        main_layout.addLayout(form_layout)

        # Button box (OK/Cancel)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def load_project_data(self):
        """Load existing project data into form fields"""
        if not self.project:
            logger.warning("Attempted to load data from None project")
            return

        logger.debug(f"Loading data for project: {self.project.name}")

        self.name_edit.setText(self.project.name)

        # Find the index of the project's kitchen type in the combo box
        kitchen_type_index = self.kitchen_type_combo.findText(
            self.project.kitchen_type, Qt.MatchExactly
        )
        if kitchen_type_index >= 0:
            self.kitchen_type_combo.setCurrentIndex(kitchen_type_index)

        self.order_number_edit.setText(self.project.order_number)

        # Client information
        if self.project.client_name:
            self.client_name_edit.setText(self.project.client_name)
        if self.project.client_address:
            self.client_address_edit.setText(self.project.client_address)
        if self.project.client_phone:
            self.client_phone_edit.setText(self.project.client_phone)
        if self.project.client_email:
            self.client_email_edit.setText(self.project.client_email)

    def validate_inputs(self) -> tuple[bool, str]:
        """Validate user inputs and return (is_valid, error_message)"""
        # Validate required fields
        name = self.name_edit.text().strip()
        order_number = self.order_number_edit.text().strip()

        if not name:
            return False, "Nazwa projektu jest wymagana."

        if not order_number:
            return False, "Numer zamówienia jest wymagany."

        return True, ""

    def collect_project_data(self) -> dict:
        """Collect form data into a dictionary ready for service use"""
        return {
            "name": self.name_edit.text().strip(),
            "kitchen_type": self.kitchen_type_combo.currentText(),
            "order_number": self.order_number_edit.text().strip(),
            "client_name": self.client_name_edit.text().strip() or None,
            "client_address": self.client_address_edit.text().strip() or None,
            "client_phone": self.client_phone_edit.text().strip() or None,
            "client_email": self.client_email_edit.text().strip() or None,
        }

    def accept(self):
        """Handle dialog acceptance (OK button)"""
        logger.debug("Project dialog accept button clicked")

        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            logger.debug(f"Validation failed: {error_message}")
            QMessageBox.warning(self, "Brakujące dane", error_message)
            return

        # Collect form data
        project_data = self.collect_project_data()
        logger.debug(f"Collected project data: {project_data}")

        try:
            if self.project_id:
                # Update existing project
                logger.info(f"Updating existing project ID: {self.project_id}")
                self.project_service.update_project(self.project_id, **project_data)
                logger.info(f"Project ID: {self.project_id} updated successfully")
            else:
                # Create new project
                logger.info("Creating new project")
                new_project = self.project_service.create_project(**project_data)
                logger.info(f"New project created with ID: {new_project.id}")

            super().accept()  # Close the dialog with accept status

        except ValueError as e:
            # Handle validation errors from service
            logger.warning(f"Validation error in service: {str(e)}")
            QMessageBox.warning(self, "Nieprawidłowe dane", str(e))
        except Exception as e:
            # Handle other errors
            logger.error(f"Error saving project: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Błąd", f"Wystąpił błąd: {str(e)}")
