"""
Modern settings dialog for the Cabplanner application.
"""

import logging
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
    QSpinBox,
    QDoubleSpinBox,
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
        self.appearance_tab = self.create_appearance_tab()
        self.company_tab = self.create_company_tab()
        self.advanced_tab = self.create_advanced_tab()

        # Add tabs to widget
        self.tab_widget.addTab(self.general_tab, "Ogólne")
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
            ["Codziennie", "Co tydzień", "Co miesiąc", "Nigdy"]
        )
        db_layout.addRow("Częstotliwość sprawdzania:", self.autoupdate_freq)

        # Add version information
        from src.version import get_version_string, BUILD_DATE

        version_label = QLabel(f"Wersja programu: {get_version_string()}")
        version_label.setAlignment(Qt.AlignRight)
        db_layout.addRow("", version_label)

        # Add build date information
        build_date_label = QLabel(f"Data kompilacji: {BUILD_DATE}")
        build_date_label.setAlignment(Qt.AlignRight)
        db_layout.addRow("", build_date_label)

        layout.addWidget(db_group)

        # Projects settings group
        projects_group = QGroupBox("Projekty")
        projects_layout = QFormLayout(projects_group)

        self.auto_numbering_check = QCheckBox("Automatyczne numerowanie projektów")
        projects_layout.addRow(self.auto_numbering_check)

        self.default_kitchen_type = QComboBox()
        self.default_kitchen_type.addItems(["LOFT", "PARIS", "WINO"])
        projects_layout.addRow("Domyślny typ kuchni:", self.default_kitchen_type)

        layout.addWidget(projects_group)

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

        # Color scheme
        color_layout = QFormLayout()
        self.theme_color = QComboBox()
        self.theme_color.addItems(
            ["Niebieski", "Zielony", "Czerwony", "Pomarańczowy", "Fioletowy"]
        )
        color_layout.addRow("Główny kolor:", self.theme_color)
        theme_layout.addLayout(color_layout)

        # Font size
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 16)
        self.font_size.setSingleStep(1)
        color_layout.addRow("Rozmiar czcionki:", self.font_size)

        layout.addWidget(theme_group)

        # Table settings
        table_group = QGroupBox("Tabele")
        table_layout = QVBoxLayout(table_group)

        self.alternate_row_colors = QCheckBox("Naprzemienne kolory wierszy")
        table_layout.addWidget(self.alternate_row_colors)

        self.grid_lines = QCheckBox("Pokaż linie siatki")
        table_layout.addWidget(self.grid_lines)

        layout.addWidget(table_group)

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

        # Formula settings
        formula_group = QGroupBox("Wzory i obliczenia")
        formula_layout = QFormLayout(formula_group)

        self.base_offset = QDoubleSpinBox()
        self.base_offset.setRange(0, 100)
        self.base_offset.setSingleStep(0.1)
        self.base_offset.setSuffix(" mm")
        formula_layout.addRow("Domyślne przesunięcie:", self.base_offset)

        layout.addWidget(formula_group)

        # Developer settings
        dev_group = QGroupBox("Opcje deweloperskie")
        dev_layout = QVBoxLayout(dev_group)

        self.enable_logging = QCheckBox("Włącz szczegółowe logowanie")
        dev_layout.addWidget(self.enable_logging)

        self.debug_mode = QCheckBox("Tryb debugowania")
        dev_layout.addWidget(self.debug_mode)

        layout.addWidget(dev_group)

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

            autoupdate_freq = self.settings_service.get_setting_value(
                "auto_update_frequency", "Co tydzień"
            )
            index = self.autoupdate_freq.findText(autoupdate_freq)
            if index >= 0:
                self.autoupdate_freq.setCurrentIndex(index)

            # Project settings
            self.auto_numbering_check.setChecked(
                self.settings_service.get_setting_value("auto_numbering", True)
            )

            default_kitchen = self.settings_service.get_setting_value(
                "default_kitchen_type", "LOFT"
            )
            index = self.default_kitchen_type.findText(default_kitchen)
            if index >= 0:
                self.default_kitchen_type.setCurrentIndex(index)

            # Appearance settings
            self.dark_mode_check.setChecked(
                self.settings_service.get_setting_value("dark_mode", False)
            )

            theme_color = self.settings_service.get_setting_value(
                "theme_color", "Niebieski"
            )
            index = self.theme_color.findText(theme_color)
            if index >= 0:
                self.theme_color.setCurrentIndex(index)

            self.font_size.setValue(
                self.settings_service.get_setting_value("font_size", 10)
            )

            self.alternate_row_colors.setChecked(
                self.settings_service.get_setting_value("alternate_row_colors", True)
            )

            self.grid_lines.setChecked(
                self.settings_service.get_setting_value("grid_lines", True)
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

            # Advanced settings
            self.base_offset.setValue(
                self.settings_service.get_setting_value("base_formula_offset_mm", 20.0)
            )

            self.enable_logging.setChecked(
                self.settings_service.get_setting_value("enable_logging", False)
            )

            self.debug_mode.setChecked(
                self.settings_service.get_setting_value("debug_mode", False)
            )

        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            QMessageBox.warning(
                self, "Błąd", f"Wystąpił błąd podczas wczytywania ustawień: {str(e)}"
            )

    def save_settings(self):
        """Save settings to the database"""
        try:
            # Database settings
            self.settings_service.set_setting("db_path", self.db_path_edit.text())

            # Auto-update settings
            self.settings_service.set_setting(
                "auto_update_enabled", self.autoupdate_check.isChecked()
            )

            self.settings_service.set_setting(
                "auto_update_frequency", self.autoupdate_freq.currentText()
            )

            # Project settings
            self.settings_service.set_setting(
                "auto_numbering", self.auto_numbering_check.isChecked()
            )

            self.settings_service.set_setting(
                "default_kitchen_type", self.default_kitchen_type.currentText()
            )

            # Appearance settings
            self.settings_service.set_setting(
                "dark_mode", self.dark_mode_check.isChecked()
            )

            self.settings_service.set_setting(
                "theme_color", self.theme_color.currentText()
            )

            self.settings_service.set_setting(
                "font_size", self.font_size.value(), "int"
            )

            self.settings_service.set_setting(
                "alternate_row_colors", self.alternate_row_colors.isChecked()
            )

            self.settings_service.set_setting("grid_lines", self.grid_lines.isChecked())

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

            # Advanced settings
            self.settings_service.set_setting(
                "base_formula_offset_mm", self.base_offset.value(), "float"
            )

            self.settings_service.set_setting(
                "enable_logging", self.enable_logging.isChecked()
            )

            self.settings_service.set_setting("debug_mode", self.debug_mode.isChecked())

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

    def clear_company_logo(self):
        """Clear the company logo"""
        self.logo_preview.setText("Brak logo")
        self.logo_preview.setPixmap(QPixmap())
        self.settings_service.set_setting("company_logo_path", "")

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
                "auto_update_frequency": "Co tydzień",
                "auto_numbering": True,
                "default_kitchen_type": "LOFT",
                "dark_mode": False,
                "theme_color": "Niebieski",
                "font_size": 10,
                "alternate_row_colors": True,
                "grid_lines": True,
                "base_formula_offset_mm": 20.0,
                "enable_logging": False,
                "debug_mode": False,
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
