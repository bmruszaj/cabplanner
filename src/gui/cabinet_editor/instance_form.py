"""
Instance form for editing project cabinet instances.

Handles instance-specific fields like quantity, sequence, colors, etc.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QSpinBox,
    QComboBox,
    QPlainTextEdit,
    QPushButton,
    QFrame,
    QGroupBox,
)
from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QFont

from src.gui.resources.resources import get_icon
from src.gui.resources.styles import get_theme, PRIMARY


class InstanceForm(QWidget):
    """Form for editing project cabinet instance."""

    sig_dirty_changed = Signal(bool)
    sig_edit_type = Signal()  # Request to switch to type tab

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_cabinet = None
        self.cabinet_type = None
        self._is_dirty = False
        self._setup_ui()
        self._setup_connections()
        self._apply_styles()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Type info section (read-only)
        type_frame = QFrame()
        type_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        type_layout = QVBoxLayout(type_frame)
        type_layout.setContentsMargins(12, 12, 12, 12)

        type_header = QHBoxLayout()
        type_title = QLabel("Typ szafki")
        type_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        type_header.addWidget(type_title)

        type_header.addStretch()

        self.edit_type_button = QPushButton("Edytuj typ")
        self.edit_type_button.setIcon(get_icon("edit"))
        icon_size = int(self.edit_type_button.fontMetrics().height() * 0.8)
        self.edit_type_button.setIconSize(QSize(icon_size, icon_size))
        self.edit_type_button.clicked.connect(self.sig_edit_type.emit)
        type_header.addWidget(self.edit_type_button)

        type_layout.addLayout(type_header)

        self.type_info_label = QLabel("—")
        self.type_info_label.setWordWrap(True)
        self.type_info_label.setStyleSheet("color: #666; margin-top: 4px;")
        type_layout.addWidget(self.type_info_label)

        layout.addWidget(type_frame)

        # Basic settings group
        basic_group = QGroupBox("Podstawowe ustawienia")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(12)

        # Quantity
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setRange(1, 999)
        self.quantity_spinbox.setValue(1)
        self.quantity_spinbox.setSuffix(" szt")
        self.quantity_spinbox.setMinimumHeight(
            34
        )  # Make spinbox taller for better usability
        self.quantity_spinbox.setButtonSymbols(
            QSpinBox.ButtonSymbols.UpDownArrows
        )  # Ensure arrows are visible
        basic_layout.addRow("Ilość:", self.quantity_spinbox)

        # Sequence number - removed to prevent editing conflicts

        layout.addWidget(basic_group)

        # Colors and options group
        options_group = QGroupBox("Kolory i opcje")
        options_layout = QFormLayout(options_group)
        options_layout.setSpacing(12)

        # Body color with preview
        body_color_layout = QHBoxLayout()
        self.body_color_combo = QComboBox()
        self.body_color_combo.setEditable(True)
        # Import popular colors from central location
        from ..constants.colors import POPULAR_COLORS

        self.body_color_combo.addItems(POPULAR_COLORS)
        self.body_color_combo.setCurrentText("Biały")
        body_color_layout.addWidget(self.body_color_combo)

        # Add color preview chip for body color
        from ..project_details.widgets.color_chip import ColorChip

        self.body_color_preview = ColorChip("Biały", "Korpus", parent=self)
        self.body_color_preview.setToolTip("Podgląd koloru korpusu")
        body_color_layout.addWidget(self.body_color_preview)

        options_layout.addRow("Korpus:", body_color_layout)

        # Front color with preview
        front_color_layout = QHBoxLayout()
        self.front_color_combo = QComboBox()
        self.front_color_combo.setEditable(True)
        self.front_color_combo.addItems(POPULAR_COLORS)
        self.front_color_combo.setCurrentText("Biały")
        front_color_layout.addWidget(self.front_color_combo)

        # Add color preview chip for front color
        self.front_color_preview = ColorChip("Biały", "Front", parent=self)
        self.front_color_preview.setToolTip("Podgląd koloru frontu")
        front_color_layout.addWidget(self.front_color_preview)

        options_layout.addRow("Front:", front_color_layout)

        # Handle type
        self.handle_combo = QComboBox()
        self.handle_combo.addItems(
            ["Standardowy", "Nowoczesny", "Klasyczny", "Bez uchwytów"]
        )
        options_layout.addRow("Uchwyt:", self.handle_combo)

        # Hinges (optional)
        self.hinges_combo = QComboBox()
        self.hinges_combo.addItems(["Automatyczne", "Lewy", "Prawy"])
        options_layout.addRow("Zawiasy:", self.hinges_combo)

        layout.addWidget(options_group)

        # Notes section
        notes_group = QGroupBox("Uwagi")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Dodatkowe uwagi dotyczące tej szafki...")
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(notes_group)

        # Spacer
        layout.addStretch()

    def _setup_connections(self):
        """Setup signal connections."""
        # Connect all form controls to dirty tracking
        self.quantity_spinbox.valueChanged.connect(self._mark_dirty)
        # sequence_spinbox removed
        self.body_color_combo.currentTextChanged.connect(self._mark_dirty)
        self.front_color_combo.currentTextChanged.connect(self._mark_dirty)
        self.handle_combo.currentTextChanged.connect(self._mark_dirty)
        self.hinges_combo.currentTextChanged.connect(self._mark_dirty)
        self.notes_edit.textChanged.connect(self._mark_dirty)

        # Connect color combos to preview updates
        self.body_color_combo.currentTextChanged.connect(
            self._update_body_color_preview
        )
        self.front_color_combo.currentTextChanged.connect(
            self._update_front_color_preview
        )

    def _apply_styles(self):
        """Apply visual styling."""
        get_theme()

        self.setStyleSheet(f"""
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
            QFrame {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
            QSpinBox, QComboBox, QPlainTextEdit {{
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }}
            QSpinBox {{
                padding-right: 32px; /* Make room for larger buttons */
                min-height: 28px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 28px;
                height: 16px;
                border: 1px solid #ccc;
                background-color: #f8f9fa;
                border-radius: 2px;
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                margin-right: 1px;
                margin-top: 1px;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                margin-right: 1px;
                margin-bottom: 1px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {PRIMARY};
            }}
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
                background-color: #0066cc;
            }}
            QSpinBox::up-arrow {{
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 8px solid #666;
                width: 0px;
                height: 0px;
            }}
            QSpinBox::down-arrow {{
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                width: 0px;
                height: 0px;
            }}
            QSpinBox::up-button:hover QSpinBox::up-arrow {{
                border-bottom-color: white;
            }}
            QSpinBox::down-button:hover QSpinBox::down-arrow {{
                border-top-color: white;
            }}


            QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{
                border-color: {PRIMARY};
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
        self.quantity_spinbox.blockSignals(block)
        self.body_color_combo.blockSignals(block)
        self.front_color_combo.blockSignals(block)
        self.handle_combo.blockSignals(block)
        self.hinges_combo.blockSignals(block)
        self.notes_edit.blockSignals(block)

    def _mark_dirty(self):
        """Mark form as dirty and emit signal."""
        if not self._is_dirty:
            self._is_dirty = True
            self.sig_dirty_changed.emit(True)

    def load(self, project_cabinet, cabinet_type=None):
        """Load project cabinet instance data."""
        self.project_cabinet = project_cabinet
        self.cabinet_type = cabinet_type

        if not project_cabinet:
            self.setEnabled(False)
            self.type_info_label.setText("Nie wybrano szafki do edycji")
            return

        self.setEnabled(True)

        # Block signals during data loading to prevent false dirty state
        self._block_dirty_signals(True)

        try:
            # Load instance data
            self.quantity_spinbox.setValue(project_cabinet.quantity or 1)
            # sequence_number editing removed

            # Load colors
            body_color = project_cabinet.body_color or "Biały"
            front_color = project_cabinet.front_color or "Biały"

            self.body_color_combo.setCurrentText(body_color)
            self.front_color_combo.setCurrentText(front_color)

            # Update color previews
            if hasattr(self, "body_color_preview"):
                self.body_color_preview.set_color(body_color)
            if hasattr(self, "front_color_preview"):
                self.front_color_preview.set_color(front_color)

            # Load handle and hinges
            handle_type = getattr(project_cabinet, "handle_type", None) or "Standardowy"
            self.handle_combo.setCurrentText(handle_type)

            hinges = getattr(project_cabinet, "hinges", None) or "Automatyczne"
            self.hinges_combo.setCurrentText(hinges)

            # Load notes
            notes = getattr(project_cabinet, "notes", None) or ""
            self.notes_edit.setPlainText(notes)
        finally:
            # Re-enable signals after loading
            self._block_dirty_signals(False)

        # Update type info
        if cabinet_type:
            type_info = f"{cabinet_type.nazwa}"
            if hasattr(cabinet_type, "sku") and cabinet_type.sku:
                type_info += f" (SKU: {cabinet_type.sku})"
            self.type_info_label.setText(type_info)
            self.edit_type_button.setEnabled(True)
        elif hasattr(project_cabinet, "type_id") and project_cabinet.type_id:
            self.type_info_label.setText("Ładowanie informacji o typie...")
            self.edit_type_button.setEnabled(True)
        else:
            self.type_info_label.setText(
                "To jest szafka niestandardowa (bez powiązanego typu katalogowego)."
            )
            self.edit_type_button.setEnabled(False)

        # Reset dirty flag
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

    def is_dirty(self) -> bool:
        """Check if form has unsaved changes."""
        return self._is_dirty

    def is_valid(self) -> bool:
        """Check if form data is valid."""
        # Instance forms are generally always valid since quantity > 0 is enforced by spinbox
        return self.quantity_spinbox.value() > 0

    def values(self) -> dict:
        """Get form values for saving."""
        return {
            "quantity": self.quantity_spinbox.value(),
            # sequence_number editing removed to prevent conflicts
            "body_color": self.body_color_combo.currentText(),
            "front_color": self.front_color_combo.currentText(),
            "handle_type": self.handle_combo.currentText(),
            "hinges": self.hinges_combo.currentText(),
            "notes": self.notes_edit.toPlainText().strip() or None,
        }

    def reset_dirty(self):
        """Reset dirty flag after saving."""
        self._is_dirty = False
        self.sig_dirty_changed.emit(False)

    def _update_body_color_preview(self, color_name: str):
        """Update body color preview chip when combo box changes."""
        if hasattr(self, "body_color_preview"):
            self.body_color_preview.set_color(color_name)

    def _update_front_color_preview(self, color_name: str):
        """Update front color preview chip when combo box changes."""
        if hasattr(self, "front_color_preview"):
            self.front_color_preview.set_color(color_name)
