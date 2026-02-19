"""
Dialog for editing a cabinet part.

Provides a unified interface for adding and editing parts
across different parts of the application.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QDialogButtonBox,
    QTextEdit,
)


class PartEditDialog(QDialog):
    """Dialog for editing a cabinet part"""

    def __init__(self, part=None, parent=None):
        super().__init__(parent)
        self.part = part
        self.is_edit_mode = part is not None

        self.setWindowTitle("Edytuj część" if self.is_edit_mode else "Nowa część")
        self.resize(400, 500)

        self._setup_ui()
        self._setup_connections()

        if self.is_edit_mode:
            self._load_part_data()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Basic information group
        basic_group = QGroupBox("Podstawowe informacje")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(12)

        # Part name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. bok lewy, front, półka...")
        basic_layout.addRow("Nazwa części*:", self.name_edit)

        # Dimensions
        dimensions_layout = QHBoxLayout()

        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 5000)
        self.width_spinbox.setSuffix(" mm")
        self.width_spinbox.setValue(600)
        dimensions_layout.addWidget(QLabel("Szerokość:"))
        dimensions_layout.addWidget(self.width_spinbox)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(1, 5000)
        self.height_spinbox.setSuffix(" mm")
        self.height_spinbox.setValue(720)
        dimensions_layout.addWidget(QLabel("Wysokość:"))
        dimensions_layout.addWidget(self.height_spinbox)

        basic_layout.addRow("Wymiary:", dimensions_layout)

        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 100)
        self.quantity_spinbox.setValue(1)
        basic_layout.addRow("Ilość:", self.quantity_spinbox)

        layout.addWidget(basic_group)

        # Material information group
        material_group = QGroupBox("Informacje o materiale")
        material_layout = QFormLayout(material_group)
        material_layout.setSpacing(12)

        # Material type
        self.material_combo = QComboBox()
        self.material_combo.addItems(
            [
                "PLYTA 18",
                "PLYTA 16",
                "PLYTA 12",
                "HDF",
                "FRONT",
                "WITRYNA",
                "PÓŁKA SZKLANA",
                "INNE",
            ]
        )
        self.material_combo.setEditable(True)
        material_layout.addRow("Materiał:", self.material_combo)

        # Wrapping
        self.wrapping_edit = QLineEdit()
        self.wrapping_edit.setPlaceholderText("np. D, K, DDKK...")
        material_layout.addRow("Okleina:", self.wrapping_edit)

        layout.addWidget(material_group)

        # Comments group
        comments_group = QGroupBox("Uwagi")
        comments_layout = QVBoxLayout(comments_group)

        self.comments_edit = QTextEdit()
        self.comments_edit.setMaximumHeight(80)
        self.comments_edit.setPlaceholderText("Dodatkowe uwagi dotyczące części...")
        comments_layout.addWidget(self.comments_edit)

        layout.addWidget(comments_group)

        # Button box
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

    def _setup_connections(self):
        """Setup signal connections."""
        pass

    def _get_part_value(self, key, default=None):
        """Get value from part, supporting both dict and object attributes."""
        if self.part is None:
            return default
        if isinstance(self.part, dict):
            return self.part.get(key, default)
        return getattr(self.part, key, default)

    def _load_part_data(self):
        """Load part data into the form."""
        if not self.part:
            return

        self.name_edit.setText(self._get_part_value("part_name", "") or "")
        self.width_spinbox.setValue(self._get_part_value("width_mm", 0) or 0)
        self.height_spinbox.setValue(self._get_part_value("height_mm", 0) or 0)
        self.quantity_spinbox.setValue(self._get_part_value("pieces", 1) or 1)

        material = self._get_part_value("material", "")
        if material:
            index = self.material_combo.findText(material)
            if index >= 0:
                self.material_combo.setCurrentIndex(index)
            else:
                self.material_combo.setCurrentText(material)

        self.wrapping_edit.setText(self._get_part_value("wrapping", "") or "")
        self.comments_edit.setPlainText(self._get_part_value("comments", "") or "")

    def accept(self):
        """Handle dialog acceptance."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Nazwa części jest wymagana.")
            self.name_edit.setFocus()
            return

        # Create part data
        self.part_data = {
            "part_name": name,
            "width_mm": self.width_spinbox.value(),
            "height_mm": self.height_spinbox.value(),
            "pieces": self.quantity_spinbox.value(),
            "material": self.material_combo.currentText() or None,
            "wrapping": self.wrapping_edit.text().strip() or None,
            "comments": self.comments_edit.toPlainText().strip() or None,
        }

        super().accept()
