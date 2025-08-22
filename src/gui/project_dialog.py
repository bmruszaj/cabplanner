"""
Modern single-page project dialog for creating and editing projects.
"""

import logging
import re
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
    QWidget,
    QTextEdit,
    QCheckBox,
    QLabel,
    QScrollArea,
    QCompleter,
    QFrame,
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QKeySequence, QRegularExpressionValidator, QShortcut

from sqlalchemy.orm import Session

from src.services.project_service import ProjectService
from src.constants import KITCHEN_TYPES

# Configure logging
logger = logging.getLogger(__name__)


class ProjectDialog(QDialog):
    """Modern single-page dialog for creating and editing projects"""

    def __init__(self, db_session: Session, project_id=None, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.project_service = ProjectService(self.session)
        self.project_id = project_id
        self.project = None
        self._dirty = False

        # If project_id is provided, load project
        if self.project_id:
            self.project = self.project_service.get_project(self.project_id)

        self.init_ui()
        self._wire_shortcuts()
        self._bind_dirty_tracking()

        # Set window title and initial focus
        if self.project:
            self.setWindowTitle(f"Edytuj projekt: {self.project.name}")
            self.load_project_data()
            self.order_number_edit.setFocus()
        else:
            self.setWindowTitle("Nowy projekt")
            self.generate_order_number()
            self.name_edit.setFocus()

        # Update header to show correct mode
        self._update_header()

    def init_ui(self):
        """Initialize the UI components"""
        self.resize(700, 600)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for responsive design
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Central widget
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignTop)

        # Build sections
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_project_section())
        layout.addWidget(self._build_client_section())
        layout.addWidget(self._build_flags_section())

        # Set scroll area content
        scroll_area.setWidget(central_widget)
        main_layout.addWidget(scroll_area)

        # Footer
        main_layout.addWidget(self._build_footer())

        # Apply initial styles
        self._apply_header_styles()

    def _build_header(self):
        """Build the header section with title and order number display"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)

        # Title
        self.title_label = QLabel()
        self.title_label.setObjectName("titleLabel")
        header_layout.addWidget(self.title_label)

        # Subheader with order number
        self.subheader_label = QLabel()
        self.subheader_label.setObjectName("subheaderLabel")
        header_layout.addWidget(self.subheader_label)

        # Mode chip
        self.mode_label = QLabel()
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setMaximumWidth(80)
        header_layout.addWidget(self.mode_label)

        return header_frame

    def _build_project_section(self):
        """Build the project information section"""
        project_group = QGroupBox(self.tr("Informacje o projekcie"))
        project_group.setObjectName("projectGroup")
        form_layout = QFormLayout(project_group)

        # Order number with generate button
        order_layout = QHBoxLayout()
        self.order_number_edit = QLineEdit()
        self.order_number_edit.setObjectName("order_number_edit")
        self.order_number_edit.setPlaceholderText("YYYYMMDD-HHMM")
        self.order_number_edit.setToolTip("Numer zamówienia w formacie YYYYMMDD-HHMM")
        order_layout.addWidget(self.order_number_edit)

        self.generate_btn = QPushButton(self.tr("Generuj"))
        self.generate_btn.setObjectName("generateBtn")
        self.generate_btn.clicked.connect(self.generate_order_number)
        self.generate_btn.setToolTip("Generuj numer zamówienia (Ctrl+G)")
        self.generate_btn.setMaximumWidth(80)
        order_layout.addWidget(self.generate_btn)

        form_layout.addRow(self.tr("Numer zamówienia: *"), order_layout)

        # Project name (required)
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("name_edit")
        self.name_edit.setPlaceholderText("Wprowadź nazwę projektu...")
        self.name_edit.setToolTip("Nazwa projektu (wymagane)")
        form_layout.addRow(self.tr("Nazwa projektu: *"), self.name_edit)

        # Kitchen type with completer
        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.setObjectName("kitchen_type_combo")
        self.kitchen_type_combo.addItems(KITCHEN_TYPES)
        self.kitchen_type_combo.setEditable(True)

        # Add completer for case-insensitive matching
        completer = QCompleter(KITCHEN_TYPES)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.kitchen_type_combo.setCompleter(completer)
        self.kitchen_type_combo.setToolTip("Wybierz lub wprowadź typ kuchni")

        form_layout.addRow(self.tr("Typ kuchni:"), self.kitchen_type_combo)

        # Notes - store as general project notes in uwagi_note when uwagi is checked
        self.notes_edit = QTextEdit()
        self.notes_edit.setObjectName("notes_edit")
        self.notes_edit.setPlaceholderText(
            "Ogólne uwagi do projektu (będą zapisane w sekcji 'Uwagi dodatkowe')..."
        )
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setToolTip("Ogólne uwagi do projektu")
        form_layout.addRow(self.tr("Uwagi:"), self.notes_edit)

        return project_group

    def _build_client_section(self):
        """Build the client information section"""
        client_group = QGroupBox(self.tr("Dane klienta"))
        client_group.setObjectName("clientGroup")
        form_layout = QFormLayout(client_group)

        # Client name
        self.client_name_edit = QLineEdit()
        self.client_name_edit.setObjectName("client_name_edit")
        self.client_name_edit.setPlaceholderText("Nazwa firmy lub imię i nazwisko...")
        self.client_name_edit.setToolTip("Nazwa klienta")
        form_layout.addRow(self.tr("Nazwa klienta:"), self.client_name_edit)

        # Phone with validator
        self.client_phone_edit = QLineEdit()
        self.client_phone_edit.setObjectName("client_phone_edit")
        self.client_phone_edit.setPlaceholderText("+48 600 000 000")
        self.client_phone_edit.setToolTip(
            "Numer telefonu (dozwolone cyfry, spacje, +, -, ())"
        )
        form_layout.addRow(self.tr("Telefon:"), self.client_phone_edit)

        # Email with validator
        self.client_email_edit = QLineEdit()
        self.client_email_edit.setObjectName("client_email_edit")
        self.client_email_edit.setPlaceholderText("email@example.com")
        self.client_email_edit.setToolTip("Adres e-mail")

        # Simple email validation
        email_regex = QRegularExpression(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        email_validator = QRegularExpressionValidator(email_regex)
        self.client_email_edit.setValidator(email_validator)

        form_layout.addRow(self.tr("Email:"), self.client_email_edit)

        # Address
        self.client_address_edit = QLineEdit()
        self.client_address_edit.setObjectName("client_address_edit")
        self.client_address_edit.setPlaceholderText(
            "Ulica, numer, kod pocztowy, miasto..."
        )
        self.client_address_edit.setToolTip("Adres klienta")
        form_layout.addRow(self.tr("Adres:"), self.client_address_edit)

        return client_group

    def _build_flags_section(self):
        """Build the flags and notes section"""
        flags_group = QGroupBox(self.tr("Flagi i notatki"))
        flags_group.setObjectName("flagsGroup")
        flags_layout = QVBoxLayout(flags_group)

        # Blaty
        self.blaty_check = QCheckBox(self.tr("Blaty"))
        self.blaty_check.setObjectName("blatyCheck")
        self.blaty_check.toggled.connect(self.toggle_blaty_note)
        flags_layout.addWidget(self.blaty_check)

        self.blaty_note_edit = QTextEdit()
        self.blaty_note_edit.setObjectName("blaty_note_edit")
        self.blaty_note_edit.setPlaceholderText("Szczegóły dotyczące blatów...")
        self.blaty_note_edit.setMaximumHeight(60)
        self.blaty_note_edit.setVisible(False)
        flags_layout.addWidget(self.blaty_note_edit)

        # Cokoły
        self.cokoly_check = QCheckBox(self.tr("Cokoły"))
        self.cokoly_check.setObjectName("cokolyCheck")
        self.cokoly_check.toggled.connect(self.toggle_cokoly_note)
        flags_layout.addWidget(self.cokoly_check)

        self.cokoly_note_edit = QTextEdit()
        self.cokoly_note_edit.setObjectName("cokoly_note_edit")
        self.cokoly_note_edit.setPlaceholderText("Szczegóły dotyczące cokołów...")
        self.cokoly_note_edit.setMaximumHeight(60)
        self.cokoly_note_edit.setVisible(False)
        flags_layout.addWidget(self.cokoly_note_edit)

        # Uwagi dodatkowe
        self.uwagi_check = QCheckBox(self.tr("Uwagi dodatkowe"))
        self.uwagi_check.setObjectName("uwagiCheck")
        self.uwagi_check.toggled.connect(self.toggle_uwagi_note)
        flags_layout.addWidget(self.uwagi_check)

        self.uwagi_note_edit = QTextEdit()
        self.uwagi_note_edit.setObjectName("uwagi_note_edit")
        self.uwagi_note_edit.setPlaceholderText("Dodatkowe uwagi...")
        self.uwagi_note_edit.setMaximumHeight(60)
        self.uwagi_note_edit.setVisible(False)
        flags_layout.addWidget(self.uwagi_note_edit)

        return flags_group

    def _build_footer(self):
        """Build the footer with action buttons"""
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.setObjectName("buttonBox")

        # Set button tooltips
        save_btn = self.button_box.button(QDialogButtonBox.Save)
        save_btn.setText(self.tr("Zapisz"))
        save_btn.setToolTip("Zapisz projekt (Ctrl+S, Ctrl+Enter)")
        save_btn.setDefault(True)

        cancel_btn = self.button_box.button(QDialogButtonBox.Cancel)
        cancel_btn.setText(self.tr("Anuluj"))
        cancel_btn.setToolTip("Anuluj bez zapisywania (Esc)")

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        return self.button_box

    def _wire_shortcuts(self):
        """Wire keyboard shortcuts"""
        # Generate order number
        QShortcut(QKeySequence("Ctrl+G"), self, self.generate_order_number)

        # Save shortcuts
        QShortcut(QKeySequence("Ctrl+S"), self, self.accept)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.accept)

        # Cancel shortcut (Esc is default)
        QShortcut(QKeySequence("Escape"), self, self.reject)

    def _bind_dirty_tracking(self):
        """Bind dirty state tracking to form controls"""
        # Text fields - connect all at once to avoid repetition
        text_widgets = [
            self.order_number_edit,
            self.name_edit,
            self.notes_edit,
            self.client_name_edit,
            self.client_phone_edit,
            self.client_email_edit,
            self.client_address_edit,
            self.blaty_note_edit,
            self.cokoly_note_edit,
            self.uwagi_note_edit,
        ]
        for widget in text_widgets:
            widget.textChanged.connect(self._mark_dirty)

        # Checkboxes - connect all at once
        checkboxes = [
            self.blaty_check,
            self.cokoly_check,
            self.uwagi_check,
        ]
        for checkbox in checkboxes:
            checkbox.toggled.connect(self._mark_dirty)

        # Combo box
        self.kitchen_type_combo.currentTextChanged.connect(self._mark_dirty)

        # Update header when order number changes
        self.order_number_edit.textChanged.connect(self._update_header)

    def _mark_dirty(self):
        """Mark the dialog as having unsaved changes"""
        self._dirty = True

    def _update_header(self):
        """Update the header with current information"""
        if self.project:
            self.title_label.setText(f"Edytuj projekt: {self.project.name}")
            self.mode_label.setText("Edycja")
            self.mode_label.setProperty("mode", "edit")
        else:
            self.title_label.setText("Nowy projekt")
            self.mode_label.setText("Nowy")
            self.mode_label.setProperty("mode", "new")

        order_num = self.order_number_edit.text().strip()
        if order_num:
            self.subheader_label.setText(f"Nr zam.: {order_num}")
        else:
            self.subheader_label.setText("Nr zam.: (nie podano)")

        # Apply styles using CSS classes
        self._apply_header_styles()

    def _apply_header_styles(self):
        """Apply CSS styles to header elements"""
        # Set CSS styles using objectName selectors
        self.setStyleSheet("""
            QLabel#titleLabel {
                font-size: 18px; 
                font-weight: bold; 
                color: #2c3e50;
                margin-bottom: 5px;
            }
            
            QLabel#subheaderLabel {
                font-size: 12px; 
                color: #7f8c8d; 
                margin-bottom: 5px;
            }
            
            QLabel#modeLabel {
                color: white; 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 11px;
                font-weight: bold;
            }
            
            QLabel#modeLabel[mode="new"] {
                background-color: #27ae60;
            }
            
            QLabel#modeLabel[mode="edit"] {
                background-color: #f39c12;
            }
            
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
        """)

    def _set_error(self, widget, on: bool):
        """Set visual error state on a widget"""
        if on:
            widget.setStyleSheet(
                "border: 2px solid #e74c3c; background-color: #fdf2f2;"
            )
        else:
            widget.setStyleSheet("")

    def _is_valid_email(self, text: str) -> bool:
        """Check if email format is valid"""
        if not text.strip():
            return True  # Empty is valid
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, text.strip()))

    def _is_valid_phone(self, text: str) -> bool:
        """Check if phone number format is valid (loose validation)"""
        if not text.strip():
            return True  # Empty is valid

        # Allow digits, spaces, +, -, (, ), and basic formatting
        # Must contain at least 7 digits for a valid phone number
        pattern = r"^[\d\s\+\-\(\)]+$"
        digit_count = len(re.sub(r"[^\d]", "", text.strip()))

        return bool(re.match(pattern, text.strip())) and digit_count >= 7

    def _validate_form(self) -> tuple[bool, str, object]:
        """
        Validate all form fields

        Returns:
            tuple: (is_valid, error_message, widget_to_focus)
        """
        # Clear previous error states
        self._set_error(self.name_edit, False)
        self._set_error(self.order_number_edit, False)
        self._set_error(self.client_email_edit, False)
        self._set_error(self.client_phone_edit, False)

        # Validate required fields
        if not self.name_edit.text().strip():
            self._set_error(self.name_edit, True)
            return False, self.tr("Nazwa projektu jest wymagana."), self.name_edit

        if not self.order_number_edit.text().strip():
            self._set_error(self.order_number_edit, True)
            return (
                False,
                self.tr("Numer zamówienia jest wymagany."),
                self.order_number_edit,
            )

        # Validate email if provided
        email_text = self.client_email_edit.text().strip()
        if email_text and not self._is_valid_email(email_text):
            self._set_error(self.client_email_edit, True)
            return (
                False,
                self.tr("Podany adres email ma nieprawidłowy format."),
                self.client_email_edit,
            )

        # Validate phone if provided
        phone_text = self.client_phone_edit.text().strip()
        if phone_text and not self._is_valid_phone(phone_text):
            self._set_error(self.client_phone_edit, True)
            return (
                False,
                self.tr(
                    "Podany numer telefonu ma nieprawidłowy format. Dozwolone są cyfry, spacje, +, -, ()."
                ),
                self.client_phone_edit,
            )

        return True, "", None

    def _collect_payload(self) -> dict:
        """Collect form data into a dictionary"""
        return {
            "order_number": self.order_number_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "kitchen_type": self.kitchen_type_combo.currentText(),
            "client_name": self.client_name_edit.text().strip() or None,
            "client_address": self.client_address_edit.text().strip() or None,
            "client_phone": self.client_phone_edit.text().strip() or None,
            "client_email": self.client_email_edit.text().strip() or None,
            "blaty": self.blaty_check.isChecked(),
            "blaty_note": self.blaty_note_edit.toPlainText().strip()
            if self.blaty_check.isChecked()
            else None,
            "cokoly": self.cokoly_check.isChecked(),
            "cokoly_note": self.cokoly_note_edit.toPlainText().strip()
            if self.cokoly_check.isChecked()
            else None,
            **self._merge_notes_data(),
        }

    def _merge_notes_data(self) -> dict:
        """
        Merge general notes with uwagi notes using a clear, documented strategy.

        Strategy:
        1. General notes (from notes_edit) are treated as primary project notes
        2. Uwagi notes (from uwagi_note_edit) are treated as additional/specific notes
        3. If both exist, general notes come first, followed by uwagi notes
        4. They are separated by double newlines for readability
        5. If either has content, the uwagi flag is automatically set to True

        Returns:
            dict: Contains 'uwagi' flag and 'uwagi_note' content
        """
        general_notes = self.notes_edit.toPlainText().strip()
        uwagi_specific_notes = self.uwagi_note_edit.toPlainText().strip()

        # Build the combined notes with clear precedence
        combined_parts = []

        # Primary: General project notes (if any)
        if general_notes:
            combined_parts.append(general_notes)

        # Secondary: Specific uwagi notes (if any)
        if uwagi_specific_notes:
            combined_parts.append(uwagi_specific_notes)

        # Combine with clear separation
        combined_uwagi_note = "\n\n".join(combined_parts) if combined_parts else ""

        # Determine if uwagi flag should be set
        # Logic: uwagi is enabled if:
        # 1. User explicitly checked the uwagi checkbox, OR
        # 2. There are any notes (general or specific) to save
        has_uwagi = self.uwagi_check.isChecked() or bool(combined_uwagi_note)

        return {
            "uwagi": has_uwagi,
            "uwagi_note": combined_uwagi_note if has_uwagi else None,
        }

    def generate_order_number(self):
        """Generate a new order number based on current date"""
        today = datetime.now()
        order_number = f"{today.year}{today.month:02d}{today.day:02d}-{today.hour:02d}{today.minute:02d}"
        self.order_number_edit.setText(order_number)
        self._mark_dirty()

    def toggle_blaty_note(self, checked):
        """Show/hide blaty note field based on checkbox state"""
        self.blaty_note_edit.setVisible(checked)
        if checked:
            self.blaty_note_edit.setFocus()

    def toggle_cokoly_note(self, checked):
        """Show/hide cokoly note field based on checkbox state"""
        self.cokoly_note_edit.setVisible(checked)
        if checked:
            self.cokoly_note_edit.setFocus()

    def toggle_uwagi_note(self, checked):
        """Show/hide uwagi note field based on checkbox state"""
        self.uwagi_note_edit.setVisible(checked)
        if checked:
            self.uwagi_note_edit.setFocus()

    def load_project_data(self):
        """Load project data into the form"""
        if not self.project:
            return

        # Basic info
        self.order_number_edit.setText(self.project.order_number or "")
        self.name_edit.setText(self.project.name or "")

        # Notes field - keep for UI but don't load from project as it's not supported
        # The notes field can be used for temporary notes during editing

        # Kitchen type
        if self.project.kitchen_type:
            index = self.kitchen_type_combo.findText(self.project.kitchen_type)
            if index >= 0:
                self.kitchen_type_combo.setCurrentIndex(index)

        # Flags and notes
        self.blaty_check.setChecked(bool(self.project.blaty))
        if self.project.blaty_note:
            self.blaty_note_edit.setText(self.project.blaty_note)

        self.cokoly_check.setChecked(bool(self.project.cokoly))
        if self.project.cokoly_note:
            self.cokoly_note_edit.setText(self.project.cokoly_note)

        self.uwagi_check.setChecked(bool(self.project.uwagi))
        if self.project.uwagi_note:
            # Try to separate general notes from specific uwagi notes
            # For now, just put everything in the uwagi_note field
            # In the future, we could try to parse and separate them
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

        # Clear dirty state after loading
        self._dirty = False
        self._update_header()

    def _confirm_discard_changes(self) -> str:
        """
        Show confirmation dialog for unsaved changes.

        Returns:
            str: User's choice - "save", "discard", or "cancel"
        """
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle(self.tr("Niezapisane zmiany"))
        msgbox.setText(self.tr("Masz niezapisane zmiany. Czy chcesz je zapisać?"))
        msgbox.setIcon(QMessageBox.Question)

        save_button = msgbox.addButton(self.tr("Tak"), QMessageBox.YesRole)
        discard_button = msgbox.addButton(self.tr("Nie"), QMessageBox.NoRole)
        msgbox.addButton(self.tr("Anuluj"), QMessageBox.RejectRole)
        msgbox.setDefaultButton(save_button)

        msgbox.exec()
        clicked_button = msgbox.clickedButton()

        if clicked_button == save_button:
            return "save"
        elif clicked_button == discard_button:
            return "discard"
        else:  # cancel_button or closed
            return "cancel"

    def closeEvent(self, event):
        """Handle close event with dirty state check"""
        if self._dirty:
            choice = self._confirm_discard_changes()

            if choice == "save":
                self.accept()
                return
            elif choice == "cancel":
                event.ignore()
                return
            # choice == "discard" - continue with closing

        event.accept()

    def reject(self):
        """Handle dialog rejection with dirty state check"""
        if self._dirty:
            choice = self._confirm_discard_changes()

            if choice == "save":
                self.accept()
                return
            elif choice == "cancel":
                return
            # choice == "discard" - continue with rejection

        super().reject()

    def accept(self):
        """Handle dialog acceptance (Save button)"""
        try:
            # Skip DB operations if no changes were made to existing project
            if self.project and not self._dirty:
                super().accept()
                return

            # Validate form
            is_valid, error_message, widget_to_focus = self._validate_form()
            if not is_valid:
                QMessageBox.warning(
                    self,
                    self.tr("Brak danych")
                    if "wymagana" in error_message
                    else self.tr("Nieprawidłowe dane"),
                    error_message,
                )
                if widget_to_focus:
                    widget_to_focus.setFocus()
                return

            # TODO: Check for duplicate order numbers if ProjectService supports it
            # if hasattr(self.project_service, 'get_project_by_order_number'):
            #     existing = self.project_service.get_project_by_order_number(self.order_number_edit.text().strip())
            #     if existing and (not self.project or existing.id != self.project.id):
            #         QMessageBox.warning(self, "Duplikat", "Projekt z tym numerem zamówienia już istnieje.")
            #         return

            # Collect and save data
            project_data = self._collect_payload()

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

            self._dirty = False
            super().accept()

        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")
            QMessageBox.critical(
                self,
                self.tr("Błąd zapisu"),
                self.tr(f"Wystąpił błąd podczas zapisywania projektu: {str(e)}"),
            )
