"""
Type form for editing catalog cabinet types.

Handles type-level fields like name, SKU, dimensions, defaults, etc.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QDoubleSpinBox,
    QScrollArea,
)
from PySide6.QtCore import Signal, Qt

from src.gui.resources.styles import get_theme, PRIMARY
from .validators import (
    is_nonempty,
)


class TypeForm(QWidget):
    """Form for editing catalog cabinet type."""

    sig_dirty_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cabinet_type = None
        self._is_dirty = False
        self._setup_ui()
        self._setup_connections()
        self._apply_styles()

    def _setup_ui(self):
        """Setup the user interface."""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create scrollable content widget
        self.content_widget = QWidget()
        layout = QVBoxLayout(self.content_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Set the content widget as the scroll area's widget
        scroll_area.setWidget(self.content_widget)

        # Main layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

        # Basic information group
        basic_group = QGroupBox("Podstawowe informacje")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(16)

        # Name (required)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Wprowadź nazwę typu szafki...")
        basic_layout.addRow("Nazwa*:", self.name_edit)

        # Name validation label
        self.name_validation = QLabel("")
        self.name_validation.setStyleSheet("color: #d32f2f; font-size: 9pt;")
        self.name_validation.hide()
        basic_layout.addRow("", self.name_validation)

        # SKU (optional)
        self.sku_edit = QLineEdit()
        self.sku_edit.setPlaceholderText("Opcjonalny kod SKU...")
        basic_layout.addRow("SKU:", self.sku_edit)

        # Kitchen type
        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.addItems(["LOFT", "PARIS", "WINO"])
        basic_layout.addRow("Typ kuchni:", self.kitchen_type_combo)

        layout.addWidget(basic_group)

        # Dimensions group
        dimensions_group = QGroupBox("Wymiary")
        dimensions_layout = QFormLayout(dimensions_group)
        dimensions_layout.setSpacing(16)

        # Width (read-only, calculated from parts)
        self.width_spinbox = QDoubleSpinBox()
        self.width_spinbox.setRange(0, 5000)
        self.width_spinbox.setSuffix(" mm")
        self.width_spinbox.setValue(600)
        self.width_spinbox.setReadOnly(True)
        self.width_spinbox.setToolTip(
            "Wymiary są obliczane automatycznie na podstawie części szafki"
        )
        dimensions_layout.addRow("Szerokość:", self.width_spinbox)

        # Height (read-only, calculated from parts)
        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(0, 5000)
        self.height_spinbox.setSuffix(" mm")
        self.height_spinbox.setValue(720)
        self.height_spinbox.setReadOnly(True)
        self.height_spinbox.setToolTip(
            "Wymiary są obliczane automatycznie na podstawie części szafki"
        )
        dimensions_layout.addRow("Wysokość:", self.height_spinbox)

        # Depth (read-only, based on kitchen type)
        self.depth_spinbox = QDoubleSpinBox()
        self.depth_spinbox.setRange(0, 2000)
        self.depth_spinbox.setSuffix(" mm")
        self.depth_spinbox.setValue(560)
        self.depth_spinbox.setReadOnly(True)
        self.depth_spinbox.setToolTip(
            "Głębokość jest określana na podstawie typu kuchni"
        )
        dimensions_layout.addRow("Głębokość:", self.depth_spinbox)

        # Dimensions validation
        self.dimensions_validation = QLabel("")
        self.dimensions_validation.setStyleSheet("color: #ff9800; font-size: 9pt;")
        self.dimensions_validation.hide()
        dimensions_layout.addRow("", self.dimensions_validation)

        layout.addWidget(dimensions_group)

        # Default colors group
        defaults_group = QGroupBox("Domyślne kolory")
        defaults_layout = QFormLayout(defaults_group)
        defaults_layout.setSpacing(16)

        # Default body color
        self.default_body_combo = QComboBox()
        self.default_body_combo.setEditable(True)
        self.default_body_combo.addItems(
            ["#ffffff", "#000000", "#808080", "#8B4513", "#A0522D"]
        )
        self.default_body_combo.setCurrentText("#ffffff")
        defaults_layout.addRow("Domyślny korpus:", self.default_body_combo)

        # Default front color
        self.default_front_combo = QComboBox()
        self.default_front_combo.setEditable(True)
        self.default_front_combo.addItems(
            ["#ffffff", "#000000", "#808080", "#8B4513", "#A0522D", "#4169E1"]
        )
        self.default_front_combo.setCurrentText("#ffffff")
        defaults_layout.addRow("Domyślny front:", self.default_front_combo)

        # Default handle
        self.default_handle_combo = QComboBox()
        self.default_handle_combo.setEditable(True)
        self.default_handle_combo.addItems(
            [
                "Standardowy",
                "Nowoczesny",
                "Klasyczny",
                "Bez uchwytów",
                "Uchwyt aluminiowy",
                "Uchwyt drewniany",
            ]
        )
        self.default_handle_combo.setCurrentText("Standardowy")
        defaults_layout.addRow("Domyślny uchwyt:", self.default_handle_combo)

        # Default hinges
        self.default_hinges_combo = QComboBox()
        self.default_hinges_combo.setEditable(True)
        self.default_hinges_combo.addItems(
            [
                "Zawias standardowy",
                "Zawias automatyczny",
                "Zawias meblowy",
                "Zawias ukryty",
                "Zawias piankowy",
            ]
        )
        self.default_hinges_combo.setCurrentText("Zawias standardowy")
        defaults_layout.addRow("Domyślne zawiasy:", self.default_hinges_combo)

        layout.addWidget(defaults_group)

        # Additional settings group
        additional_group = QGroupBox("Dodatkowe ustawienia")
        additional_layout = QVBoxLayout(additional_group)
        additional_layout.setSpacing(16)

        # Tags
        tags_layout = QFormLayout()
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Tagi oddzielone przecinkami...")
        tags_layout.addRow("Tagi:", self.tags_edit)
        additional_layout.addLayout(tags_layout)

        layout.addWidget(additional_group)

        # Spacer
        layout.addStretch()

    def _setup_connections(self):
        """Setup signal connections."""
        # Connect all form controls to dirty tracking
        self.name_edit.textChanged.connect(self._on_name_changed)
        self.sku_edit.textChanged.connect(self._mark_dirty)
        self.kitchen_type_combo.currentTextChanged.connect(self._mark_dirty)
        # Dimension fields are read-only, so no change connections needed
        self.default_body_combo.currentTextChanged.connect(self._mark_dirty)
        self.default_front_combo.currentTextChanged.connect(self._mark_dirty)
        self.default_handle_combo.currentTextChanged.connect(self._mark_dirty)
        self.default_hinges_combo.currentTextChanged.connect(self._mark_dirty)
        self.tags_edit.textChanged.connect(self._mark_dirty)

    def _apply_styles(self):
        """Apply visual styling."""
        get_theme()

        self.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #a0a0a0;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QGroupBox {{
                font-weight: bold;
                font-size: 10pt;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px 0 6px;
                background-color: white;
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                padding: 8px;
                min-height: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {PRIMARY};
            }}
            QLineEdit[invalid="true"] {{
                border-color: #d32f2f;
                background-color: #fff5f5;
            }}
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
                opacity: 0.9;
            }}
        """)

    def _block_dirty_signals(self, block: bool):
        """Block or unblock dirty tracking signals during data loading."""
        self.name_edit.blockSignals(block)
        self.sku_edit.blockSignals(block)
        self.kitchen_type_combo.blockSignals(block)
        self.width_spinbox.blockSignals(block)
        self.height_spinbox.blockSignals(block)
        self.depth_spinbox.blockSignals(block)
        self.default_body_combo.blockSignals(block)
        self.default_front_combo.blockSignals(block)
        self.default_handle_combo.blockSignals(block)
        self.default_hinges_combo.blockSignals(block)
        self.tags_edit.blockSignals(block)

    def _mark_dirty(self):
        """Mark form as dirty and emit signal."""
        if not self._is_dirty:
            self._is_dirty = True
            self.sig_dirty_changed.emit(True)

    def _on_name_changed(self):
        """Handle name field changes with validation."""
        name = self.name_edit.text().strip()

        if not name:
            self.name_validation.setText("Nazwa jest wymagana")
            self.name_validation.show()
            self.name_edit.setProperty("invalid", True)
        else:
            self.name_validation.hide()
            self.name_edit.setProperty("invalid", False)

        # Refresh styling
        self.name_edit.style().unpolish(self.name_edit)
        self.name_edit.style().polish(self.name_edit)

        self._mark_dirty()

    def _on_dimension_changed(self):
        """Handle dimension changes with validation."""
        # Dimensions are read-only and calculated from parts, so no validation needed
        pass

    def load(self, cabinet_type):
        """Load cabinet type data."""
        self.cabinet_type = cabinet_type

        if not cabinet_type:
            self.setEnabled(False)
            return

        self.setEnabled(True)

        # Block signals during data loading to prevent false dirty state
        self._block_dirty_signals(True)

        try:
            # Load basic info
            self.name_edit.setText(cabinet_type.name or "")
            self.sku_edit.setText(getattr(cabinet_type, "sku", "") or "")

            # Load kitchen type
            kitchen_type = getattr(cabinet_type, "kitchen_type", "LOFT") or "LOFT"
            index = self.kitchen_type_combo.findText(kitchen_type)
            if index >= 0:
                self.kitchen_type_combo.setCurrentIndex(index)

            # Load dimensions - calculate from parts if available
            width = height = depth = None

            if hasattr(cabinet_type, "parts") and cabinet_type.parts:
                # Calculate max dimensions from parts
                max_w = None
                max_h = None
                for part in cabinet_type.parts:
                    if part.width_mm is not None:
                        max_w = (
                            int(part.width_mm)
                            if max_w is None
                            else max(max_w, int(part.width_mm))
                        )
                    if part.height_mm is not None:
                        max_h = (
                            int(part.height_mm)
                            if max_h is None
                            else max(max_h, int(part.height_mm))
                        )
                width = max_w
                height = max_h
            else:
                # No parts available, use default dimensions
                width = 600
                height = 720

            # Set depth based on kitchen type
            depth = (
                560.0
                if cabinet_type.kitchen_type in ["LOFT", "PARIS", "WINO"]
                else 320.0
            )

            self.width_spinbox.setValue(float(width) if width else 600.0)
            self.height_spinbox.setValue(float(height) if height else 720.0)
            self.depth_spinbox.setValue(depth)

            # Set default colors (these don't exist in schema, so use defaults)
            self.default_body_combo.setCurrentText("#ffffff")
            self.default_front_combo.setCurrentText("#ffffff")
            self.default_handle_combo.setCurrentText("Standardowy")
            self.default_hinges_combo.setCurrentText("Zawias standardowy")

            # Set tags (don't exist in schema, so empty)
            self.tags_edit.setText("")
        finally:
            # Re-enable signals after loading
            self._block_dirty_signals(False)

        # Run initial validation (but don't let it mark as dirty)
        name = self.name_edit.text().strip()
        if not name:
            self.name_validation.setText("Nazwa jest wymagana")
            self.name_validation.show()
            self.name_edit.setProperty("invalid", True)
        else:
            self.name_validation.hide()
            self.name_edit.setProperty("invalid", False)

        # Refresh styling
        self.name_edit.style().unpolish(self.name_edit)
        self.name_edit.style().polish(self.name_edit)

        # Reset dirty flag AFTER validation
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

    def is_dirty(self) -> bool:
        """Check if form has unsaved changes."""
        return self._is_dirty

    def is_valid(self) -> bool:
        """Check if form data is valid."""
        return is_nonempty(self.name_edit.text())

    def values(self) -> dict:
        """Get form values for saving."""
        # Only return fields that exist in the new CabinetTemplate schema
        return {
            "name": self.name_edit.text().strip(),  # Maps to 'nazwa' in service
            "kitchen_type": self.kitchen_type_combo.currentText(),
            "default_body_color": self.default_body_combo.currentText(),
            "default_front_color": self.default_front_combo.currentText(),
            "default_handle": self.default_handle_combo.currentText(),
            "default_hinges": self.default_hinges_combo.currentText(),
            "tags": self.tags_edit.text().strip(),
        }

    def reset_dirty(self):
        """Reset dirty flag after saving."""
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)
