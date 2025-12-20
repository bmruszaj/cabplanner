"""
Dialog for editing an accessory.

Provides a unified interface for adding and editing accessories
across different parts of the application.

Features:
- ComboBox with autocomplete for selecting from accessory catalog
- Automatic unit selection when choosing from catalog
- New accessories are automatically added to catalog on save
"""

from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QDialogButtonBox,
    QButtonGroup,
    QRadioButton,
    QLabel,
    QCompleter,
)
from PySide6.QtCore import Qt


class AccessoryEditDialog(QDialog):
    """Dialog for editing an accessory with catalog support.
    
    Supports two modes:
    - Selection from catalog: Shows ComboBox with existing accessories
    - New accessory: User types a new name, which is added to catalog on save
    """

    def __init__(
        self,
        accessory=None,
        existing_names=None,
        accessory_service=None,
        parent=None,
    ):
        """
        Initialize the accessory edit dialog.
        
        Args:
            accessory: Dict with accessory data for edit mode (name, unit, count)
            existing_names: List of names already in current cabinet (for validation)
            accessory_service: Optional AccessoryService for catalog integration
            parent: Parent widget
        """
        super().__init__(parent)
        self.accessory = accessory
        self.accessory_service = accessory_service
        self.is_edit_mode = accessory is not None
        
        # Store existing names for uniqueness validation (excluding current name in edit mode)
        self.existing_names = set(n.lower() for n in (existing_names or []))
        if self.is_edit_mode and accessory:
            # Exclude current accessory name from uniqueness check
            current_name = accessory.get("name", "").lower()
            self.existing_names.discard(current_name)
        
        # Load catalog accessories
        self.catalog_accessories = self._load_catalog_accessories()

        self.setWindowTitle(
            "Edytuj akcesorium" if self.is_edit_mode else "Nowe akcesorium"
        )
        self.resize(450, 320)

        self._setup_ui()
        self._setup_connections()

        if self.is_edit_mode:
            self._load_accessory_data()

    def _load_catalog_accessories(self) -> List[dict]:
        """Load accessories from catalog via service."""
        if not self.accessory_service:
            return []
        try:
            accessories = self.accessory_service.list_accessories()
            return [
                {"name": acc.name, "unit": acc.unit}
                for acc in accessories
            ]
        except Exception:
            return []

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Accessory information group
        accessory_group = QGroupBox("Informacje o akcesorium")
        accessory_layout = QFormLayout(accessory_group)
        accessory_layout.setSpacing(12)

        # Accessory name - ComboBox with autocomplete
        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)
        self.name_combo.setInsertPolicy(QComboBox.NoInsert)
        self.name_combo.lineEdit().setPlaceholderText(
            "Wybierz z listy lub wpisz nową nazwę..."
        )
        
        # Add catalog items to combo
        self.name_combo.addItem("")  # Empty option for new entry
        for acc in self.catalog_accessories:
            self.name_combo.addItem(acc["name"])
        
        # Setup completer for autocomplete
        completer = QCompleter([acc["name"] for acc in self.catalog_accessories], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.name_combo.setCompleter(completer)
        
        accessory_layout.addRow("Nazwa akcesorium*:", self.name_combo)

        # Hint label
        if self.catalog_accessories:
            hint_label = QLabel(
                f"💡 {len(self.catalog_accessories)} akcesoriów w katalogu. "
                "Nowe nazwy zostaną dodane automatycznie."
            )
            hint_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            hint_label.setWordWrap(True)
            accessory_layout.addRow("", hint_label)

        # Unit (radio buttons)
        unit_layout = QHBoxLayout()
        self.unit_group = QButtonGroup(self)
        self.szt_radio = QRadioButton("szt.")
        self.kpl_radio = QRadioButton("kpl.")
        self.unit_group.addButton(self.szt_radio)
        self.unit_group.addButton(self.kpl_radio)
        self.szt_radio.setChecked(True)  # Default
        unit_layout.addWidget(self.szt_radio)
        unit_layout.addWidget(self.kpl_radio)
        unit_layout.addStretch()
        accessory_layout.addRow("Jednostka:", unit_layout)

        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        accessory_layout.addRow("Ilość:", self.quantity_spinbox)

        layout.addWidget(accessory_group)

        # Button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _setup_connections(self):
        """Setup signal connections."""
        # When user selects from catalog, set the default unit
        self.name_combo.currentTextChanged.connect(self._on_name_changed)

    def _on_name_changed(self, name: str):
        """Handle name selection/change - set default unit from catalog."""
        name = name.strip()
        if not name:
            return
        
        # Find accessory in catalog
        for acc in self.catalog_accessories:
            if acc["name"].lower() == name.lower():
                # Set unit from catalog
                if acc["unit"] == "kpl":
                    self.kpl_radio.setChecked(True)
                else:
                    self.szt_radio.setChecked(True)
                break

    def _load_accessory_data(self):
        """Load accessory data into the form."""
        if not self.accessory:
            return

        name = self.accessory.get("name", "")
        self.name_combo.setCurrentText(name)
        
        unit = self.accessory.get("unit", "szt")
        if unit == "kpl":
            self.kpl_radio.setChecked(True)
        else:
            self.szt_radio.setChecked(True)
        self.quantity_spinbox.setValue(self.accessory.get("count", 1))

    def _is_new_catalog_entry(self, name: str) -> bool:
        """Check if name is not in catalog (new entry)."""
        name_lower = name.lower()
        return not any(
            acc["name"].lower() == name_lower 
            for acc in self.catalog_accessories
        )

    def accept(self):
        """Handle dialog acceptance."""
        name = self.name_combo.currentText().strip()

        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa akcesorium jest wymagana.")
            self.name_combo.setFocus()
            return

        # Check for duplicate name in current cabinet
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

        unit = "kpl" if self.kpl_radio.isChecked() else "szt"
        
        # Add to catalog if new and service is available
        if self.accessory_service and self._is_new_catalog_entry(name):
            try:
                self.accessory_service.get_or_create(name=name, unit=unit)
            except Exception:
                # Silently fail - catalog entry is optional
                pass

        # Create accessory data
        self.accessory_data = {
            "name": name,
            "unit": unit,
            "count": self.quantity_spinbox.value(),
        }

        super().accept()
