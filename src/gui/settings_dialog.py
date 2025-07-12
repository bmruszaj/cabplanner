from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QTextEdit,
    QDialogButtonBox,
    QLabel,
    QFileDialog,
    QPushButton,
    QColorDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap

from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import os
import logging

from src.services.settings_service import SettingsService

# Configure logging
logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Dialog for managing global application settings.

    This dialog handles UI for setting configuration and delegates
    all data operations to SettingsService.
    """

    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        logger.debug("Initializing SettingsDialog")

        # Store session and create service
        self.session = db_session
        self.settings_service = SettingsService(self.session)

        # Initialize paths and settings
        self.initialize_settings_and_paths()

        # Create UI components
        self.init_ui()
        self.load_settings()

        logger.debug("SettingsDialog initialization complete")

    def initialize_settings_and_paths(self):
        """Initialize settings from service and file paths"""
        try:
            # Load settings from database
            logger.debug("Loading settings from database")
            self.settings = self.settings_service.get_settings()

            # Setup logo paths
            self.app_dir = Path(__file__).resolve().parent.parent.parent
            self.program_logo_path = self.app_dir / "program_logo.png"
            self.company_logo_path = self.app_dir / "company_logo.png"

            logger.debug(f"Program logo path: {self.program_logo_path}")
            logger.debug(f"Company logo path: {self.company_logo_path}")

            # Parse theme color if available
            self.selected_theme_color = self.parse_theme_color()
        except Exception as e:
            logger.error(f"Error initializing settings: {str(e)}")
            QMessageBox.critical(
                self,
                "Błąd inicjalizacji",
                f"Wystąpił błąd podczas inicjalizacji ustawień: {str(e)}"
            )

    def parse_theme_color(self) -> QColor:
        """Parse theme color from settings string, return None if invalid"""
        if not self.settings.theme_accent_rgb:
            return None

        try:
            r, g, b = map(int, self.settings.theme_accent_rgb.split(","))
            logger.debug(f"Parsed theme color: RGB({r},{g},{b})")
            return QColor(r, g, b)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid theme color format: {e}")
            return None

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Ustawienia globalne")
        self.resize(500, 500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Form layout for settings
        form_layout = QFormLayout()

        # Formula offset
        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setMinimum(-10.0)
        self.offset_spin.setMaximum(10.0)
        self.offset_spin.setSingleStep(0.1)
        self.offset_spin.setDecimals(1)
        self.offset_spin.setSuffix(" mm")
        form_layout.addRow("Domyślne przesunięcie formuły:", self.offset_spin)

        # Auto-update interval
        self.update_combo = QComboBox()
        self.update_combo.addItems(["on_start", "daily", "weekly"])
        form_layout.addRow("Częstotliwość aktualizacji:", self.update_combo)

        # Theme color
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setStyleSheet("background-color: #cccccc; border: 1px solid black;")

        self.color_button = QPushButton("Wybierz kolor")
        self.color_button.clicked.connect(self.choose_color)

        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()

        form_layout.addRow("Kolor motywu:", color_layout)

        # Advanced script
        form_layout.addRow(QLabel("Zaawansowany skrypt:"))
        self.script_edit = QTextEdit()
        self.script_edit.setMinimumHeight(100)
        form_layout.addRow(self.script_edit)

        main_layout.addLayout(form_layout)

        # Logo section
        main_layout.addWidget(QLabel("Loga:"))

        # Program logo
        logo_layout = QHBoxLayout()

        self.program_logo_label = QLabel()
        self.program_logo_label.setFixedSize(150, 75)
        self.program_logo_label.setStyleSheet("border: 1px solid #cccccc;")
        self.program_logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(self.program_logo_label)

        logo_btn_layout = QVBoxLayout()
        self.program_logo_btn = QPushButton("Wczytaj logo programu")
        self.program_logo_btn.clicked.connect(lambda: self.load_logo("program"))
        logo_btn_layout.addWidget(self.program_logo_btn)
        logo_btn_layout.addStretch()
        logo_layout.addLayout(logo_btn_layout)

        main_layout.addLayout(logo_layout)

        # Company logo
        company_logo_layout = QHBoxLayout()

        self.company_logo_label = QLabel()
        self.company_logo_label.setFixedSize(150, 75)
        self.company_logo_label.setStyleSheet("border: 1px solid #cccccc;")
        self.company_logo_label.setAlignment(Qt.AlignCenter)
        company_logo_layout.addWidget(self.company_logo_label)

        company_btn_layout = QVBoxLayout()
        self.company_logo_btn = QPushButton("Wczytaj logo firmy")
        self.company_logo_btn.clicked.connect(lambda: self.load_logo("company"))
        company_btn_layout.addWidget(self.company_logo_btn)
        company_btn_layout.addStretch()
        company_logo_layout.addLayout(company_btn_layout)

        main_layout.addLayout(company_logo_layout)

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Display existing logos if they exist
        self.display_logo("program")
        self.display_logo("company")

    def load_settings(self):
        """Load settings from database into form"""
        try:
            # Set formula offset
            logger.debug(f"Setting formula offset: {self.settings.base_formula_offset_mm}")
            self.offset_spin.setValue(self.settings.base_formula_offset_mm)

            # Set auto-update interval
            index = self.update_combo.findText(self.settings.autoupdate_interval)
            if index >= 0:
                logger.debug(f"Setting update interval: {self.settings.autoupdate_interval}")
                self.update_combo.setCurrentIndex(index)
            else:
                logger.warning(f"Unknown update interval: {self.settings.autoupdate_interval}")

            # Set theme color
            if self.selected_theme_color:
                logger.debug(f"Setting theme color: {self.selected_theme_color.name()}")
                self.update_color_preview(self.selected_theme_color)

            # Set advanced script
            if self.settings.advanced_script:
                logger.debug("Setting advanced script")
                self.script_edit.setPlainText(self.settings.advanced_script)

        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            QMessageBox.warning(self, "Błąd", f"Nie udało się wczytać wszystkich ustawień: {str(e)}")

    def choose_color(self):
        """Open color dialog to choose theme color"""
        try:
            initial_color = self.selected_theme_color or QColor("#cccccc")
            color = QColorDialog.getColor(initial_color, self, "Wybierz kolor motywu")

            if color.isValid():
                logger.debug(f"New color selected: {color.name()}")
                self.selected_theme_color = color
                self.update_color_preview(color)
            else:
                logger.debug("Color selection canceled")
        except Exception as e:
            logger.error(f"Error selecting color: {str(e)}")
            QMessageBox.warning(self, "Błąd", f"Problem z wyborem koloru: {str(e)}")

    def update_color_preview(self, color):
        """Update color preview label with selected color"""
        try:
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
        except Exception as e:
            logger.error(f"Error updating color preview: {str(e)}")

    def load_logo(self, logo_type):
        """Open file dialog to select a logo image"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Wybierz plik logo", "", "Obrazy (*.png *.jpg *.jpeg)"
            )

            if not file_path:
                logger.debug("Logo file selection canceled")
                return

            logger.debug(f"Selected logo file: {file_path}")

            # Determine target path
            target_path = self.program_logo_path if logo_type == "program" else self.company_logo_path

            # Copy the selected file
            shutil.copy(file_path, target_path)
            logger.info(f"Copied logo from {file_path} to {target_path}")

            # Display the new logo
            self.display_logo(logo_type)
        except Exception as e:
            logger.error(f"Error loading logo: {str(e)}")
            QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać pliku logo: {str(e)}")

    def display_logo(self, logo_type):
        """Display the selected logo in the preview label"""
        logo_path = self.program_logo_path if logo_type == "program" else self.company_logo_path
        label = self.program_logo_label if logo_type == "program" else self.company_logo_label

        try:
            if logo_path.exists():
                logger.debug(f"Displaying logo: {logo_path}")
                pixmap = QPixmap(str(logo_path))
                pixmap = pixmap.scaled(150, 75, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(pixmap)
            else:
                logger.debug(f"Logo does not exist: {logo_path}")
                label.setText("Brak logo")
        except Exception as e:
            logger.error(f"Error displaying logo: {str(e)}")
            label.setText("Błąd wczytania")

    def collect_settings_data(self) -> dict:
        """Collect settings from UI into a dictionary"""
        # Prepare RGB string if color is selected
        theme_accent_rgb = None
        if self.selected_theme_color:
            r, g, b = self.selected_theme_color.red(), self.selected_theme_color.green(), self.selected_theme_color.blue()
            theme_accent_rgb = f"{r},{g},{b}"

        return {
            "base_formula_offset_mm": self.offset_spin.value(),
            "autoupdate_interval": self.update_combo.currentText(),
            "theme_accent_rgb": theme_accent_rgb,
            "advanced_script": self.script_edit.toPlainText() or None
        }

    def accept(self):
        """Save settings on dialog accept"""
        try:
            logger.info("Saving settings")

            # Collect settings data
            settings_data = self.collect_settings_data()
            logger.debug(f"Collected settings data: {settings_data}")

            # Update settings using service
            self.settings_service.update_settings(**settings_data)
            logger.info("Settings updated successfully")

            # Close dialog
            super().accept()

        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            QMessageBox.critical(self, "Błąd zapisu", f"Wystąpił błąd podczas zapisywania ustawień: {str(e)}")
