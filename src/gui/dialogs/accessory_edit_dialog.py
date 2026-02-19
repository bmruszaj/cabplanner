"""
Dialog for editing an accessory.

Provides a unified interface for adding and editing accessories
across different parts of the application.

Features:
- ComboBox with autocomplete for selecting from accessory catalog
- New accessories are automatically added to catalog on save
"""

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
)

from src.gui.resources.styles import PRIMARY


class AccessoryEditDialog(QDialog):
    """Dialog for editing an accessory with catalog support."""

    DIALOG_WIDTH = 450
    DIALOG_HEIGHT = 280

    def __init__(
        self,
        accessory=None,
        existing_names=None,
        accessory_service=None,
        parent=None,
    ):
        """Initialize the accessory edit dialog."""
        super().__init__(parent)
        self.accessory = accessory
        self.accessory_service = accessory_service
        self.is_edit_mode = accessory is not None

        # Store existing names for uniqueness validation (excluding current name in edit mode)
        self.existing_names = set(n.lower() for n in (existing_names or []))
        if self.is_edit_mode and accessory:
            current_name = accessory.get("name", "").lower()
            self.existing_names.discard(current_name)

        self.catalog_accessories = self._load_catalog_accessories()

        self.setWindowTitle(
            "Edytuj akcesorium" if self.is_edit_mode else "Nowe akcesorium"
        )
        self.setFixedWidth(self.DIALOG_WIDTH)
        self.setMinimumHeight(self.DIALOG_HEIGHT)

        self._setup_ui()
        self._apply_styles()

        if self.is_edit_mode:
            self._load_accessory_data()

    def _load_catalog_accessories(self) -> List[dict]:
        """Load accessories from catalog via service."""
        if not self.accessory_service:
            return []
        try:
            accessories = self.accessory_service.list_accessories()
            return [{"name": acc.name} for acc in accessories]
        except Exception:
            return []

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        accessory_group = QGroupBox("Informacje o akcesorium")
        accessory_layout = QFormLayout(accessory_group)
        accessory_layout.setSpacing(12)

        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)
        self.name_combo.setInsertPolicy(QComboBox.NoInsert)
        self.name_combo.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon
        )
        self.name_combo.setMinimumContentsLength(24)
        self.name_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.name_combo.lineEdit().setPlaceholderText(
            "Wybierz z listy lub wpisz nową nazwę..."
        )

        self.name_combo.addItem("")
        for acc in self.catalog_accessories:
            self.name_combo.addItem(acc["name"])

        completer = QCompleter([acc["name"] for acc in self.catalog_accessories], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.name_combo.setCompleter(completer)

        accessory_layout.addRow("Nazwa akcesorium*:", self.name_combo)

        if self.catalog_accessories:
            hint_label = QLabel(
                f"W katalogu: {len(self.catalog_accessories)} akcesoriów. "
                "Nowe nazwy zostaną dodane automatycznie."
            )
            hint_label.setStyleSheet(
                "color: #666; font-size: 10px; font-style: italic;"
            )
            hint_label.setWordWrap(True)
            accessory_layout.addRow("", hint_label)

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        accessory_layout.addRow("Ilość:", self.quantity_spinbox)

        layout.addWidget(accessory_group)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        save_button = self.button_box.button(QDialogButtonBox.Save)
        if save_button is not None:
            save_button.setText("Zapisz")
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        if cancel_button is not None:
            cancel_button.setText("Anuluj")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _load_accessory_data(self):
        """Load accessory data into the form."""
        if not self.accessory:
            return

        self.name_combo.setCurrentText(self.accessory.get("name", ""))
        self.quantity_spinbox.setValue(self.accessory.get("count", 1))

    def _is_new_catalog_entry(self, name: str) -> bool:
        """Check if name is not in catalog (new entry)."""
        name_lower = name.lower()
        return not any(
            acc["name"].lower() == name_lower for acc in self.catalog_accessories
        )

    def accept(self):
        """Handle dialog acceptance."""
        name = self.name_combo.currentText().strip()

        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa akcesorium jest wymagana.")
            self.name_combo.setFocus()
            return

        if name.lower() in self.existing_names:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Akcesorium o nazwie '{name}' już istnieje w tej szafce.\n"
                "Proszę wybrać inną nazwę.",
            )
            self.name_combo.setFocus()
            self.name_combo.lineEdit().selectAll()
            return

        if self.accessory_service and self._is_new_catalog_entry(name):
            try:
                self.accessory_service.get_or_create(name=name)
            except Exception:
                # Catalog entry creation is optional for the dialog flow.
                pass

        self.accessory_data = {
            "name": name,
            "count": self.quantity_spinbox.value(),
        }

        super().accept()

    def _apply_styles(self):
        """Apply visual styling to match other dialogs."""
        self.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: white;
            }}
            QLineEdit, QSpinBox, QComboBox {{
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {PRIMARY};
            }}
            QDialogButtonBox QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 9pt;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: #085f56;
            }}
            QDialogButtonBox QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """
        )
