"""
Dialog for editing an accessory.

Provides a unified interface for adding and editing accessories
across different parts of the application.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QDialogButtonBox,
    QButtonGroup,
    QRadioButton,
)


class AccessoryEditDialog(QDialog):
    """Dialog for editing an accessory"""

    def __init__(self, accessory=None, existing_names=None, parent=None):
        super().__init__(parent)
        self.accessory = accessory
        self.is_edit_mode = accessory is not None
        # Store existing names for uniqueness validation (excluding current name in edit mode)
        self.existing_names = set(n.lower() for n in (existing_names or []))
        if self.is_edit_mode and accessory:
            # Exclude current accessory name from uniqueness check
            current_name = accessory.get("name", "").lower()
            self.existing_names.discard(current_name)

        self.setWindowTitle(
            "Edytuj akcesorium" if self.is_edit_mode else "Nowe akcesorium"
        )
        self.resize(400, 300)

        self._setup_ui()
        self._setup_connections()

        if self.is_edit_mode:
            self._load_accessory_data()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Accessory information group
        accessory_group = QGroupBox("Informacje o akcesorium")
        accessory_layout = QFormLayout(accessory_group)
        accessory_layout.setSpacing(12)

        # Accessory name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. Uchwyt standardowy...")
        accessory_layout.addRow("Nazwa akcesorium*:", self.name_edit)

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
        pass

    def _load_accessory_data(self):
        """Load accessory data into the form."""
        if not self.accessory:
            return

        self.name_edit.setText(self.accessory.get("name", ""))
        unit = self.accessory.get("unit", "szt")
        if unit == "kpl":
            self.kpl_radio.setChecked(True)
        else:
            self.szt_radio.setChecked(True)
        self.quantity_spinbox.setValue(self.accessory.get("count", 1))

    def accept(self):
        """Handle dialog acceptance."""
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa akcesorium jest wymagana.")
            self.name_edit.setFocus()
            return

        # Check for duplicate name
        if name.lower() in self.existing_names:
            QMessageBox.warning(
                self,
                "Błąd",
                f"Akcesorium o nazwie '{name}' już istnieje.\n"
                "Proszę wybrać inną nazwę.",
            )
            self.name_edit.setFocus()
            self.name_edit.selectAll()
            return

        # Create accessory data
        self.accessory_data = {
            "name": name,
            "unit": "kpl" if self.kpl_radio.isChecked() else "szt",
            "count": self.quantity_spinbox.value(),
        }

        super().accept()
