"""
Modern settings dialog for the Cabplanner application.
"""

import logging
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QDialogButtonBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from sqlalchemy.orm import Session

from src.services.settings_service import SettingsService
from src.services.updater_service import UpdaterService
from src.gui.update_dialog import UpdateDialog
from src.version import VERSION

# Configure logging
logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Modern settings dialog for configuring application preferences."""

    settingsChanged = Signal()  # Signal emitted when settings are saved

    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.session = db_session
        self.settings_service = SettingsService(self.session)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Ustawienia")
        self.resize(600, 500)

        # Main layout
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.general_tab = self.create_general_tab()
        self.projects_tab = self.create_projects_tab()
        self.appearance_tab = self.create_appearance_tab()
        self.company_tab = self.create_company_tab()
        self.advanced_tab = self.create_advanced_tab()

        # Add tabs to widget
        self.tab_widget.addTab(self.general_tab, "Ogólne")
        self.tab_widget.addTab(self.projects_tab, "Projekty")
        self.tab_widget.addTab(self.appearance_tab, "Wygląd")
        self.tab_widget.addTab(self.company_tab, "Dane firmy")
        self.tab_widget.addTab(self.advanced_tab, "Zaawansowane")

        layout.addWidget(self.tab_widget)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def create_general_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Database settings group
        db_group = QGroupBox("Baza danych")
        db_layout = QFormLayout(db_group)

        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)

        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)

        browse_btn = QPushButton("Przeglądaj...")
        browse_btn.clicked.connect(self.browse_db_path)
        browse_btn.setProperty("class", "secondary")
        db_path_layout.addWidget(browse_btn)

        db_layout.addRow("Ścieżka do bazy danych:", db_path_layout)

        # Auto-update settings
        self.autoupdate_check = QCheckBox("Automatycznie sprawdzaj aktualizacje")
        db_layout.addRow(self.autoupdate_check)

        self.autoupdate_freq = QComboBox()
        self.autoupdate_freq.addItems(
            ["Przy uruchomieniu", "Codziennie", "Co tydzień", "Co miesiąc", "Nigdy"]
        )
        db_layout.addRow("Częstotliwość sprawdzania:", self.autoupdate_freq)

        # Shortcut creation setting
        self.create_shortcut_check = QCheckBox(
            "Twórz skrót przy uruchomieniu aplikacji"
        )
        db_layout.addRow(self.create_shortcut_check)

        # Add version information
        from src.version import get_version_string, BUILD_DATE

        version_label = QLabel(f"Wersja programu: {get_version_string()}")
        version_label.setAlignment(Qt.AlignRight)
        db_layout.addRow("", version_label)

        # Add build date information
        build_date_label = QLabel(f"Data kompilacji: {BUILD_DATE}")
        build_date_label.setAlignment(Qt.AlignRight)
        db_layout.addRow("", build_date_label)

        # Add check for updates button
        update_btn = QPushButton("Sprawdź aktualizacje")
        update_btn.clicked.connect(self.check_for_updates)
        update_btn.setProperty("class", "primary")
        db_layout.addRow("", update_btn)

        layout.addWidget(db_group)

        layout.addStretch()
        return tab

    def create_projects_tab(self):
        """Create the projects settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Project defaults group
        defaults_group = QGroupBox("Domyślne ustawienia projektów")
        defaults_layout = QFormLayout(defaults_group)

        # Default kitchen type
        self.default_kitchen_type = QComboBox()
        self.default_kitchen_type.addItems(["LOFT", "PARIS", "WINO"])
        defaults_layout.addRow("Domyślny typ kuchni:", self.default_kitchen_type)

        # Default project path
        self.default_project_path = QLineEdit()
        project_path_layout = QHBoxLayout()
        project_path_layout.addWidget(self.default_project_path)

        browse_project_btn = QPushButton("Przeglądaj...")
        browse_project_btn.clicked.connect(self.browse_project_path)
        browse_project_btn.setProperty("class", "secondary")
        project_path_layout.addWidget(browse_project_btn)

        defaults_layout.addRow("Domyślna ścieżka projektów:", project_path_layout)

        layout.addWidget(defaults_group)

        # Report settings group
        report_group = QGroupBox("Ustawienia raportów")
        report_layout = QFormLayout(report_group)

        # Report parts sorting
        self.report_sort_by = QComboBox()
        self.report_sort_by.addItems(["Kolor", "LP (numer szafki)"])
        report_layout.addRow("Sortowanie elementów w raporcie:", self.report_sort_by)

        layout.addWidget(report_group)

        layout.addStretch()
        return tab

    def create_appearance_tab(self):
        """Create the appearance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Theme settings
        theme_group = QGroupBox("Motyw")
        theme_layout = QVBoxLayout(theme_group)

        self.dark_mode_check = QCheckBox("Tryb ciemny")
        theme_layout.addWidget(self.dark_mode_check)

        layout.addWidget(theme_group)

        layout.addStretch()
        return tab

    def create_company_tab(self):
        """Create the company data settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Company info group
        company_group = QGroupBox("Dane firmy")
        company_layout = QFormLayout(company_group)

        self.company_name = QLineEdit()
        company_layout.addRow("Nazwa firmy:", self.company_name)

        self.company_address = QLineEdit()
        company_layout.addRow("Adres:", self.company_address)

        self.company_phone = QLineEdit()
        company_layout.addRow("Telefon:", self.company_phone)

        self.company_email = QLineEdit()
        company_layout.addRow("Email:", self.company_email)

        self.company_website = QLineEdit()
        company_layout.addRow("Strona WWW:", self.company_website)

        self.company_tax_id = QLineEdit()
        company_layout.addRow("NIP:", self.company_tax_id)

        layout.addWidget(company_group)

        # Logo group
        logo_group = QGroupBox("Logo firmy")
        logo_layout = QVBoxLayout(logo_group)

        self.logo_preview = QLabel("Brak logo")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setMinimumHeight(100)
        logo_layout.addWidget(self.logo_preview)

        logo_btn_layout = QHBoxLayout()

        self.select_logo_btn = QPushButton("Wybierz logo")
        self.select_logo_btn.clicked.connect(self.browse_company_logo)
        logo_btn_layout.addWidget(self.select_logo_btn)

        self.clear_logo_btn = QPushButton("Usuń logo")
        self.clear_logo_btn.clicked.connect(self.clear_company_logo)
        self.clear_logo_btn.setProperty("class", "secondary")
        logo_btn_layout.addWidget(self.clear_logo_btn)

        logo_layout.addLayout(logo_btn_layout)

        layout.addWidget(logo_group)

        layout.addStretch()
        return tab

    def create_advanced_tab(self):
        """Create the advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Reset settings button
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()

        self.reset_btn = QPushButton("Przywróć ustawienia domyślne")
        self.reset_btn.clicked.connect(self.confirm_reset)
        self.reset_btn.setProperty("class", "danger")
        reset_layout.addWidget(self.reset_btn)

        layout.addLayout(reset_layout)
        layout.addStretch()
        return tab

    def load_settings(self):
        """Load settings from the database into the UI"""
        try:
            # Database settings
            db_path = self.settings_service.get_setting_value("db_path", "")
            if db_path:
                self.db_path_edit.setText(db_path)
            else:
                default_db_path = str(
                    Path(__file__).resolve().parent.parent.parent / "cabplanner.db"
                )
                self.db_path_edit.setText(default_db_path)

            # Auto-update settings
            self.autoupdate_check.setChecked(
                self.settings_service.get_setting_value("auto_update_enabled", True)
            )

            # Make sure dropdown is properly populated first
            self.autoupdate_freq.clear()
            self.autoupdate_freq.addItems(
                ["Przy uruchomieniu", "Codziennie", "Co tydzień", "Co miesiąc", "Nigdy"]
            )

            # Then set the current value
            autoupdate_freq = self.settings_service.get_setting_value(
                "auto_update_frequency", "Co tydzień"
            )
            logger.debug("Loading auto_update_frequency setting: %s", autoupdate_freq)

            index = self.autoupdate_freq.findText(autoupdate_freq)
            logger.debug("Found index for frequency %s: %s", autoupdate_freq, index)

            if index >= 0:
                self.autoupdate_freq.setCurrentIndex(index)
            else:
                # Default to weekly if the saved value isn't found
                default_index = self.autoupdate_freq.findText("Co tydzień")
                self.autoupdate_freq.setCurrentIndex(default_index)
                logger.warning(
                    "Invalid auto_update_frequency: %s, defaulting to weekly",
                    autoupdate_freq,
                )

            # Shortcut creation setting
            self.create_shortcut_check.setChecked(
                self.settings_service.get_setting_value(
                    "create_shortcut_on_start", True
                )
            )

            default_kitchen = self.settings_service.get_setting_value(
                "default_kitchen_type", "LOFT"
            )
            index = self.default_kitchen_type.findText(default_kitchen)
            if index >= 0:
                self.default_kitchen_type.setCurrentIndex(index)

            # Default project path
            self.default_project_path.setText(
                self.settings_service.get_setting_value("default_project_path", "")
            )

            # Report settings
            report_sort = self.settings_service.get_setting_value(
                "report_sort_by", "Kolor"
            )
            index = self.report_sort_by.findText(report_sort)
            if index >= 0:
                self.report_sort_by.setCurrentIndex(index)

            # Appearance settings
            self.dark_mode_check.setChecked(
                self.settings_service.get_setting_value("dark_mode", False)
            )

            # Company settings
            self.company_name.setText(
                self.settings_service.get_setting_value("company_name", "")
            )

            self.company_address.setText(
                self.settings_service.get_setting_value("company_address", "")
            )

            self.company_phone.setText(
                self.settings_service.get_setting_value("company_phone", "")
            )

            self.company_email.setText(
                self.settings_service.get_setting_value("company_email", "")
            )

            self.company_website.setText(
                self.settings_service.get_setting_value("company_website", "")
            )

            self.company_tax_id.setText(
                self.settings_service.get_setting_value("company_tax_id", "")
            )

            # Load company logo if exists
            company_logo_path = self.settings_service.get_setting_value(
                "company_logo_path", ""
            )
            if company_logo_path and Path(company_logo_path).exists():
                pixmap = QPixmap(company_logo_path)
                self.logo_preview.setPixmap(
                    pixmap.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.logo_preview.setText("Brak logo")
                self.logo_preview.setPixmap(QPixmap())

        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            QMessageBox.warning(
                self, "Błąd", f"Wystąpił błąd podczas wczytywania ustawień: {str(e)}"
            )

    def save_settings(self):
        """Save settings to the database"""
        try:
            # Validate settings first
            if not self.validate_settings():
                return

            # Database settings
            self.settings_service.set_setting("db_path", self.db_path_edit.text())

            # Auto-update settings
            self.settings_service.set_setting(
                "auto_update_enabled", self.autoupdate_check.isChecked()
            )

            self.settings_service.set_setting(
                "auto_update_frequency", self.autoupdate_freq.currentText()
            )

            # Shortcut creation setting
            self.settings_service.set_setting(
                "create_shortcut_on_start", self.create_shortcut_check.isChecked()
            )

            self.settings_service.set_setting(
                "default_kitchen_type", self.default_kitchen_type.currentText()
            )

            self.settings_service.set_setting(
                "default_project_path", self.default_project_path.text()
            )

            # Report settings
            self.settings_service.set_setting(
                "report_sort_by", self.report_sort_by.currentText()
            )

            # Appearance settings
            self.settings_service.set_setting(
                "dark_mode", self.dark_mode_check.isChecked()
            )

            # Company settings
            self.settings_service.set_setting("company_name", self.company_name.text())

            self.settings_service.set_setting(
                "company_address", self.company_address.text()
            )

            self.settings_service.set_setting(
                "company_phone", self.company_phone.text()
            )

            self.settings_service.set_setting(
                "company_email", self.company_email.text()
            )

            self.settings_service.set_setting(
                "company_website", self.company_website.text()
            )

            self.settings_service.set_setting(
                "company_tax_id", self.company_tax_id.text()
            )

            # Emit signal that settings have changed
            self.settingsChanged.emit()

            # Close dialog
            self.accept()

        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            QMessageBox.critical(
                self, "Błąd", f"Wystąpił błąd podczas zapisywania ustawień: {str(e)}"
            )

    def browse_db_path(self):
        """Browse for database file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik bazy danych",
            "",
            "Pliki SQLite (*.db *.sqlite);;Wszystkie pliki (*)",
        )

        if file_path:
            self.db_path_edit.setText(file_path)

    def browse_company_logo(self):
        """Browse for company logo file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz logo firmy",
            "",
            "Pliki obrazów (*.png *.jpg *.jpeg);;Wszystkie pliki (*)",
        )

        if file_path:
            try:
                pixmap = QPixmap(file_path)
                if pixmap.isNull():
                    QMessageBox.warning(
                        self,
                        "Nieprawidłowy plik",
                        "Wybrany plik nie jest prawidłowym obrazem.",
                    )
                    return

                # Display logo preview
                self.logo_preview.setPixmap(
                    pixmap.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

                # Save logo path
                self.settings_service.set_setting("company_logo_path", file_path)

            except Exception as e:
                logger.error(f"Error loading company logo: {str(e)}")
                QMessageBox.warning(
                    self, "Błąd", f"Nie udało się wczytać logo: {str(e)}"
                )

    def browse_project_path(self):
        """Browse for default project directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Wybierz domyślny folder dla projektów",
            self.default_project_path.text() or "",
        )

        if directory:
            self.default_project_path.setText(directory)

    def clear_company_logo(self):
        """Clear the company logo"""
        self.logo_preview.setText("Brak logo")
        self.logo_preview.setPixmap(QPixmap())
        self.settings_service.set_setting("company_logo_path", "")

    def validate_settings(self):
        """Validate all settings before saving"""
        # Validate database path
        db_path = self.db_path_edit.text().strip()
        if not db_path:
            QMessageBox.warning(
                self, "Błąd walidacji", "Ścieżka do bazy danych nie może być pusta."
            )
            return False

        # Validate project path if provided
        project_path = self.default_project_path.text().strip()
        if project_path and not os.path.exists(project_path):
            reply = QMessageBox.question(
                self,
                "Nieprawidłowa ścieżka",
                f"Ścieżka '{project_path}' nie istnieje. Czy chcesz kontynuować?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return False

        # Validate company email if provided
        company_email = self.company_email.text().strip()
        if company_email and not self.is_valid_email(company_email):
            QMessageBox.warning(
                self, "Błąd walidacji", "Wprowadź prawidłowy adres e-mail firmy."
            )
            return False

        # Validate company phone if provided
        company_phone = self.company_phone.text().strip()
        if company_phone and not self.is_valid_phone(company_phone):
            QMessageBox.warning(
                self, "Błąd walidacji", "Wprowadź prawidłowy numer telefonu."
            )
            return False

        return True

    def is_valid_email(self, email):
        """Simple email validation"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def is_valid_phone(self, phone):
        """Simple phone validation - allows digits, spaces, hyphens, parentheses, plus"""
        import re

        # Remove common separators and check if remaining are digits (with optional + at start)
        cleaned = re.sub(r"[\s\-\(\)]+", "", phone)
        pattern = r"^\+?[0-9]{7,15}$"
        return re.match(pattern, cleaned) is not None

    def confirm_reset(self):
        """Confirm and reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Potwierdzenie",
            "Czy na pewno chcesz przywrócić wszystkie ustawienia do wartości domyślnych?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.reset_settings()

    def reset_settings(self):
        """Reset all settings to defaults"""
        try:
            # Set default values for core settings
            default_settings = {
                "auto_update_enabled": True,
                "auto_update_frequency": "Przy uruchomieniu",
                "create_shortcut_on_start": True,
                "default_kitchen_type": "LOFT",
                "default_project_path": os.path.join(
                    os.path.expanduser("~"), "Documents", "CabPlanner"
                ),
                "dark_mode": False,
                "company_logo_path": "",
            }

            # Apply defaults
            for key, value in default_settings.items():
                value_type = (
                    "bool"
                    if isinstance(value, bool)
                    else "int"
                    if isinstance(value, int)
                    else "float"
                    if isinstance(value, float)
                    else "str"
                )
                self.settings_service.set_setting(key, value, value_type)

            # Clear company info
            for key in [
                "company_name",
                "company_address",
                "company_phone",
                "company_email",
                "company_website",
                "company_tax_id",
            ]:
                self.settings_service.set_setting(key, "")

            # Reload settings into UI
            self.load_settings()

            QMessageBox.information(
                self,
                "Ustawienia zresetowane",
                "Wszystkie ustawienia zostały przywrócone do wartości domyślnych.",
            )

        except Exception as e:
            logger.error(f"Error resetting settings: {str(e)}")
            QMessageBox.critical(
                self, "Błąd", f"Wystąpił błąd podczas resetowania ustawień: {str(e)}"
            )

    def check_for_updates(self):
        """Open update dialog and automatically trigger update check."""
        try:
            updater = UpdaterService(self)
            dialog = UpdateDialog(VERSION, parent=self)

            # Connect signals with new exception-based error system
            dialog.check_for_updates.connect(updater.check_for_updates)
            dialog.perform_update.connect(lambda: dialog.on_update_started())
            dialog.perform_update.connect(updater.perform_update)
            dialog.cancel_update.connect(updater.cancel_update)

            # Handle update check results
            updater.update_check_complete.connect(
                lambda avail, cur, lat: (
                    dialog.update_available(cur, lat)
                    if avail
                    else dialog.no_update_available()
                )
            )

            # Handle update check failures with new exception-based system
            updater.update_check_failed.connect(dialog.update_check_failed)

            # Handle update progress and completion with correct signal names
            updater.update_progress.connect(dialog.on_update_progress)
            updater.update_complete.connect(dialog.on_update_complete)
            updater.update_failed.connect(dialog.on_update_failed)

            # Handle cancellation
            dialog.cancel_update.connect(dialog.reject)

            # Show dialog and immediately trigger update check
            dialog.show()
            updater.check_for_updates()

        except Exception as e:
            logger.exception("Error in update process: %s", e)
            QMessageBox.critical(
                self, self.tr("Błąd aktualizacji"), self.tr(f"Wystąpił błąd: {e}")
            )

    def _direct_handle_update_result(
        self, dialog, update_available, current_version, latest_version
    ):
        """Directly handle update check result and update dialog UI"""
        print(
            f"DEBUG: Direct update check result handler called: available={update_available}, current={current_version}, latest={latest_version}"
        )

        if update_available:
            dialog.update_available(current_version, latest_version)
        else:
            dialog.no_update_available()

    def _perform_update(self, updater_service, dialog):
        """Perform the update process"""
        try:
            dialog.update_started()
            updater_service.perform_update()
        except Exception as e:
            logger.exception(f"Error during update: {e}")
            dialog.update_failed(str(e))
