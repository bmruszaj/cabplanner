"""
Modern project dialog for creating and editing projects.
"""

import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QDialogButtonBox,
    QMessageBox,
    QGroupBox,
    QTabWidget,
    QWidget,
    QTextEdit,
    QCheckBox,
)

from sqlalchemy.orm import Session

from src.services.project_service import ProjectService

# Configure logging
logger = logging.getLogger(__name__)


class ProjectDialog(QDialog):
    """Dialog for creating and editing projects"""

    def __init__(self, db_session: Session, project_id=None, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.project_service = ProjectService(self.session)
        self.project_id = project_id
        self.project = None

        # If project_id is provided, load project
        if self.project_id:
            self.project = self.project_service.get_project(self.project_id)

        self.init_ui()

        # Set window title based on mode
        if self.project:
            self.setWindowTitle(f"Edytuj projekt: {self.project.name}")
            self.load_project_data()
        else:
            self.setWindowTitle("Nowy projekt")
            self.generate_order_number()

    def init_ui(self):
        """Initialize the UI components"""
        self.resize(600, 400)

        # Main layout
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.basic_tab = self.create_basic_tab()
        self.client_tab = self.create_client_tab()

        # Add tabs to widget
        self.tab_widget.addTab(self.basic_tab, "Podstawowe")
        self.tab_widget.addTab(self.client_tab, "Dane klienta")

        layout.addWidget(self.tab_widget)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def create_basic_tab(self):
        """Create the basic project information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Project info group
        project_group = QGroupBox("Informacje o projekcie")
        form_layout = QFormLayout(project_group)

        # Order number
        order_layout = QHBoxLayout()
        self.order_number_edit = QLineEdit()
        order_layout.addWidget(self.order_number_edit)

        self.generate_btn = QPushButton("Generuj")
        self.generate_btn.clicked.connect(self.generate_order_number)
        self.generate_btn.setProperty("class", "secondary")
        order_layout.addWidget(self.generate_btn)

        form_layout.addRow("Numer zamówienia:", order_layout)

        # Project name
        self.name_edit = QLineEdit()
        form_layout.addRow("Nazwa projektu:", self.name_edit)

        # Kitchen type
        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(["LOFT", "PARIS", "WINO"])
        form_layout.addRow("Typ kuchni:", self.kitchen_type_combo)

        # Notes field
        self.notes_edit = QTextEdit()
        form_layout.addRow("Uwagi:", self.notes_edit)

        layout.addWidget(project_group)

        # Flags group
        flags_group = QGroupBox("Flagi")
        flags_layout = QVBoxLayout(flags_group)

        # Blaty checkbox and notes
        self.blaty_check = QCheckBox("Blaty")
        self.blaty_check.toggled.connect(self.toggle_blaty_note)
        flags_layout.addWidget(self.blaty_check)

        self.blaty_note_edit = QTextEdit()
        self.blaty_note_edit.setPlaceholderText("Informacje o blatach...")
        self.blaty_note_edit.setVisible(False)
        flags_layout.addWidget(self.blaty_note_edit)

        # Cokoly checkbox and notes
        self.cokoly_check = QCheckBox("Cokoły")
        self.cokoly_check.toggled.connect(self.toggle_cokoly_note)
        flags_layout.addWidget(self.cokoly_check)

        self.cokoly_note_edit = QTextEdit()
        self.cokoly_note_edit.setPlaceholderText("Informacje o cokołach...")
        self.cokoly_note_edit.setVisible(False)
        flags_layout.addWidget(self.cokoly_note_edit)

        # Uwagi checkbox and notes
        self.uwagi_check = QCheckBox("Uwagi dodatkowe")
        self.uwagi_check.toggled.connect(self.toggle_uwagi_note)
        flags_layout.addWidget(self.uwagi_check)

        self.uwagi_note_edit = QTextEdit()
        self.uwagi_note_edit.setPlaceholderText("Dodatkowe uwagi...")
        self.uwagi_note_edit.setVisible(False)
        flags_layout.addWidget(self.uwagi_note_edit)

        layout.addWidget(flags_group)

        return tab

    def create_client_tab(self):
        """Create the client information tab"""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.client_name_edit = QLineEdit()
        layout.addRow("Nazwa klienta:", self.client_name_edit)

        self.client_address_edit = QLineEdit()
        layout.addRow("Adres:", self.client_address_edit)

        self.client_phone_edit = QLineEdit()
        layout.addRow("Telefon:", self.client_phone_edit)

        self.client_email_edit = QLineEdit()
        layout.addRow("Email:", self.client_email_edit)

        return tab

    def generate_order_number(self):
        """Generate a new order number based on current date"""
        today = datetime.now()
        order_number = f"{today.year}{today.month:02d}{today.day:02d}-{today.hour:02d}{today.minute:02d}"
        self.order_number_edit.setText(order_number)

    def toggle_blaty_note(self, checked):
        """Show/hide blaty note field based on checkbox state"""
        self.blaty_note_edit.setVisible(checked)

    def toggle_cokoly_note(self, checked):
        """Show/hide cokoly note field based on checkbox state"""
        self.cokoly_note_edit.setVisible(checked)

    def toggle_uwagi_note(self, checked):
        """Show/hide uwagi note field based on checkbox state"""
        self.uwagi_note_edit.setVisible(checked)

    def load_project_data(self):
        """Load project data into the form"""
        if not self.project:
            return

        # Basic info
        self.order_number_edit.setText(self.project.order_number)
        self.name_edit.setText(self.project.name)

        index = self.kitchen_type_combo.findText(self.project.kitchen_type)
        if index >= 0:
            self.kitchen_type_combo.setCurrentIndex(index)

        # Flags and notes
        self.blaty_check.setChecked(self.project.blaty)
        if self.project.blaty_note:
            self.blaty_note_edit.setText(self.project.blaty_note)

        self.cokoly_check.setChecked(self.project.cokoly)
        if self.project.cokoly_note:
            self.cokoly_note_edit.setText(self.project.cokoly_note)

        self.uwagi_check.setChecked(self.project.uwagi)
        if self.project.uwagi_note:
            self.uwagi_note_edit.setText(self.project.uwagi_note)

        # Client info
        if self.project.client_name:
            self.client_name_edit.setText(self.project.client_name)

        if self.project.client_address:
            self.client_address_edit.setText(self.project.client_address)

        if self.project.client_phone:
            self.client_phone_edit.setText(self.project.client_phone)

        if self.project.client_email:
            self.client_email_edit.setText(self.project.client_email)

    def accept(self):
        """Handle dialog acceptance (Save button)"""
        try:
            # Validate required fields
            if not self.name_edit.text().strip():
                QMessageBox.warning(
                    self, "Brak danych", "Nazwa projektu jest wymagana."
                )
                self.name_edit.setFocus()
                return

            if not self.order_number_edit.text().strip():
                QMessageBox.warning(
                    self, "Brak danych", "Numer zamówienia jest wymagany."
                )
                self.order_number_edit.setFocus()
                return

            # Prepare data for save
            project_data = {
                "order_number": self.order_number_edit.text().strip(),
                "name": self.name_edit.text().strip(),
                "kitchen_type": self.kitchen_type_combo.currentText(),
                "client_name": self.client_name_edit.text().strip(),
                "client_address": self.client_address_edit.text().strip(),
                "client_phone": self.client_phone_edit.text().strip(),
                "client_email": self.client_email_edit.text().strip(),
                "blaty": self.blaty_check.isChecked(),
                "blaty_note": self.blaty_note_edit.toPlainText()
                if self.blaty_check.isChecked()
                else None,
                "cokoly": self.cokoly_check.isChecked(),
                "cokoly_note": self.cokoly_note_edit.toPlainText()
                if self.cokoly_check.isChecked()
                else None,
                "uwagi": self.uwagi_check.isChecked(),
                "uwagi_note": self.uwagi_note_edit.toPlainText()
                if self.uwagi_check.isChecked()
                else None,
            }

            # Save project
            if self.project:
                # Update existing project
                self.project = self.project_service.update_project(
                    self.project.id, **project_data
                )
                logger.info(f"Project updated: {self.project.id}")
            else:
                # Create new project
                self.project = self.project_service.create_project(**project_data)
                logger.info(f"New project created: {self.project.id}")

            super().accept()

        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")
            QMessageBox.critical(
                self,
                "Błąd zapisu",
                f"Wystąpił błąd podczas zapisywania projektu: {str(e)}",
            )
