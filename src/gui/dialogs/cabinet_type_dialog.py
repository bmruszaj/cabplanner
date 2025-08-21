"""Dialog for creating or editing cabinet types."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.orm import Session

from src.services.cabinet_type_service import CabinetTypeService

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PartDefaults:
    """Default dimensions for cabinet parts."""
    last_w: int = 600
    last_h: int = 720


class CollapsiblePartGroup(QGroupBox):
    """A collapsible group box with summary display when collapsed."""

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._on_toggle)

        # Main layout
        self._main_layout = QVBoxLayout(self)

        # Summary label (shown when collapsed)
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: gray; font-style: italic;")
        self._summary_label.hide()
        self._main_layout.addWidget(self._summary_label)

        # Content widget (shown when expanded)
        self._content_widget = QWidget()
        self._content_layout = QFormLayout(self._content_widget)
        self._main_layout.addWidget(self._content_widget)

        # Controls
        self.count_spin = QSpinBox()
        self.count_spin.setRange(0, 10)
        self.count_spin.setToolTip("Wprowadź liczbę elementów")

        self.w_spin = QDoubleSpinBox()
        self.h_spin = QDoubleSpinBox()

        for spin in (self.w_spin, self.h_spin):
            spin.setRange(0, 5000)
            spin.setDecimals(0)
            spin.setSingleStep(1)
            spin.setSuffix(" mm")
            spin.setToolTip("Wprowadź w milimetrach")

        # Error labels
        self.w_error_label = QLabel("")
        self.w_error_label.setStyleSheet("color: red; font-size: 11px;")
        self.w_error_label.hide()

        self.h_error_label = QLabel("")
        self.h_error_label.setStyleSheet("color: red; font-size: 11px;")
        self.h_error_label.hide()

        # Presets dropdown
        self.presets_combo = QComboBox()
        self.presets_combo.addItem("Preset...")

        # Layout controls
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        preset_layout.addWidget(self.presets_combo)
        preset_layout.addStretch()

        self._content_layout.addRow(preset_layout)
        self._content_layout.addRow("Ilość:", self.count_spin)
        self._content_layout.addRow("Szerokość (mm):", self.w_spin)
        self._content_layout.addWidget(self.w_error_label)
        self._content_layout.addRow("Wysokość (mm):", self.h_spin)
        self._content_layout.addWidget(self.h_error_label)

        # Connect signals
        self.count_spin.valueChanged.connect(self._on_count_changed)
        self.w_spin.valueChanged.connect(self._update_summary)
        self.h_spin.valueChanged.connect(self._update_summary)
        self.presets_combo.currentTextChanged.connect(self._on_preset_selected)

        self._update_summary()

    def _on_toggle(self, checked: bool) -> None:
        """Handle group box toggle."""
        self._content_widget.setVisible(checked)
        self._summary_label.setVisible(not checked)
        if not checked:
            self._update_summary()

    def _on_count_changed(self, count: int) -> None:
        """Handle count change."""
        enabled = count > 0
        self.w_spin.setEnabled(enabled)
        self.h_spin.setEnabled(enabled)
        if not enabled:
            self.w_spin.setValue(0)
            self.h_spin.setValue(0)
        self._update_summary()

    def _update_summary(self) -> None:
        """Update summary display."""
        count = self.count_spin.value()
        if count == 0:
            summary = "0 elementów"
        else:
            w = int(self.w_spin.value())
            h = int(self.h_spin.value())
            summary = f"{count}× • {w}×{h} mm"
        self._summary_label.setText(summary)

    def _on_preset_selected(self, preset: str) -> None:
        """Handle preset selection."""
        if preset == "Preset...":
            return

        presets = {
            "Standard 720": (2, 600, 720),
            "Niska 600": (2, 600, 600),
            "Wysoka 900": (2, 600, 900),
            "Mała 400": (2, 400, 720),
            "Szeroka 800": (2, 800, 720),
        }

        if preset in presets:
            count, w, h = presets[preset]
            self.count_spin.setValue(count)
            self.w_spin.setValue(w)
            self.h_spin.setValue(h)

        # Reset combo to default
        self.presets_combo.setCurrentIndex(0)

    def set_presets(self, presets: List[str]) -> None:
        """Set available presets."""
        self.presets_combo.clear()
        self.presets_combo.addItem("Preset...")
        self.presets_combo.addItems(presets)

    def set_validation_error(self, field: str, error: str) -> None:
        """Set validation error for a field."""
        if field == "w":
            self.w_error_label.setText(error)
            self.w_error_label.setVisible(bool(error))
            self.w_spin.setStyleSheet("border: 1px solid red;" if error else "")
        elif field == "h":
            self.h_error_label.setText(error)
            self.h_error_label.setVisible(bool(error))
            self.h_spin.setStyleSheet("border: 1px solid red;" if error else "")

    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.set_validation_error("w", "")
        self.set_validation_error("h", "")


def is_part_valid(count: int, w: float, h: float) -> bool:
    """Check if part configuration is valid."""
    if count == 0:
        return True
    return w > 0 and h > 0


def form_errors(parts_data: Dict[str, tuple[int, float, float]]) -> List[str]:
    """Get form validation errors."""
    errors = []
    for part_name, (count, w, h) in parts_data.items():
        if count > 0 and (w <= 0 or h <= 0):
            errors.append(f"{part_name}: Wymagane wymiary gdy ilość > 0")
    return errors


class CabinetTypeDialog(QDialog):
    """Dialog for creating or editing a cabinet type"""

    def __init__(
        self,
        db_session: Session,
        cabinet_type_id: Optional[int] = None,
        parent: Optional[QWidget] = None,
        prefill_cabinet: Optional[Any] = None,
    ) -> None:
        super().__init__(parent)

        self.session: Session = db_session
        self.cabinet_type_service = CabinetTypeService(self.session)

        self.cabinet_type_id: Optional[int] = cabinet_type_id
        self.cabinet_type: Optional[Any] = None

        # State tracking
        self._is_dirty = False
        self._original_data: Dict[str, Any] = {}
        self._part_defaults: Dict[str, PartDefaults] = {
            "listwa": PartDefaults(),
            "wieniec": PartDefaults(),
            "bok": PartDefaults(),
            "front": PartDefaults(),
            "polka": PartDefaults(),
        }

        if cabinet_type_id:
            self.cabinet_type = self.cabinet_type_service.get_cabinet_type(cabinet_type_id)

        self._build_ui()

        if self.cabinet_type:
            self.setWindowTitle("Edytuj typ szafki")
            self._load_cabinet_type_data(self.cabinet_type)
        elif prefill_cabinet is not None:
            self.setWindowTitle(f"Nowy typ szafki (na podstawie: {prefill_cabinet.nazwa})")
            self._load_cabinet_type_data(prefill_cabinet, is_prefill=True)
        else:
            self.setWindowTitle("Nowy typ szafki")

        # Store original data for dirty checking
        self._store_original_data()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Initial validation
        self._validate_form()

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Ctrl+Enter and Ctrl+S to save
        shortcut1 = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut1.activated.connect(self._try_accept)

        shortcut2 = QShortcut(QKeySequence("Ctrl+Enter"), self)
        shortcut2.activated.connect(self._try_accept)

        shortcut3 = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut3.activated.connect(self._try_accept)

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        self.resize(700, 800)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Build tabs
        self._build_basic_tab()
        self._build_components_tab()

        # Error banner
        self.error_banner = QLabel("")
        self.error_banner.setStyleSheet("""
            QLabel {
                background-color: #ffe6e6;
                border: 1px solid #ff9999;
                border-radius: 4px;
                padding: 8px;
                color: #cc0000;
                font-weight: bold;
            }
        """)
        self.error_banner.hide()
        main_layout.addWidget(self.error_banner)

        # Summary bar
        self._build_summary_bar()
        main_layout.addWidget(self.summary_frame)

        # Buttons
        self._build_buttons()
        main_layout.addWidget(self.button_layout_widget)

        # Connect change signals for dirty tracking
        self._connect_change_signals()

    def _build_basic_tab(self) -> None:
        """Build the basic information tab."""
        basic_tab = QWidget()
        self.tab_widget.addTab(basic_tab, "Podstawowe")

        layout = QVBoxLayout(basic_tab)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Use VBox layout instead of FormLayout for the main content
        content_layout = QVBoxLayout(content)

        # Basic info group
        basic_group = QGroupBox("Informacje podstawowe")
        basic_form = QFormLayout(basic_group)

        self.nazwa_edit = QLineEdit()
        self.nazwa_edit.setPlaceholderText("Szafka dolna 60")
        self.nazwa_edit.setAccessibleName("Nazwa szafki")
        basic_form.addRow("Nazwa:", self.nazwa_edit)

        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.setAccessibleName("Typ kuchni")
        basic_form.addRow("Typ kuchni:", self.kitchen_type_combo)

        # HDF backs with help icon
        hdf_layout = QHBoxLayout()
        self.hdf_plecy_check = QCheckBox()
        self.hdf_plecy_check.setAccessibleName("Plecy HDF")
        help_button = QToolButton()
        help_button.setText("?")
        help_button.setFixedSize(20, 20)
        help_button.setToolTip("Plecy HDF - określa czy szafka ma tylną ścianę z płyty HDF")

        hdf_layout.addWidget(self.hdf_plecy_check)
        hdf_layout.addWidget(help_button)
        hdf_layout.addStretch()

        basic_form.addRow("Plecy HDF:", hdf_layout)

        content_layout.addWidget(basic_group)
        content_layout.addStretch()

    def _build_components_tab(self) -> None:
        """Build the components tab."""
        components_tab = QWidget()
        self.tab_widget.addTab(components_tab, "Komponenty")

        layout = QVBoxLayout(components_tab)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        form_layout = QVBoxLayout(content)
        form_layout.setSpacing(12)

        # Create collapsible part groups
        self.listwa_group = CollapsiblePartGroup("Listwy")
        self.listwa_group.set_presets(["Standard 720", "Niska 600", "Wysoka 900"])
        form_layout.addWidget(self.listwa_group)

        self.wieniec_group = CollapsiblePartGroup("Wieńce")
        self.wieniec_group.set_presets(["Standard 720", "Niska 600", "Wysoka 900"])
        form_layout.addWidget(self.wieniec_group)

        self.bok_group = CollapsiblePartGroup("Boki")
        self.bok_group.set_presets(["Standard 720", "Niska 600", "Wysoka 900"])
        form_layout.addWidget(self.bok_group)

        self.front_group = CollapsiblePartGroup("Fronty")
        self.front_group.set_presets(["Standard 720", "Mała 400", "Szeroka 800"])
        form_layout.addWidget(self.front_group)

        self.polka_group = CollapsiblePartGroup("Półki")
        self.polka_group.set_presets(["Standard 720", "Mała 400", "Szeroka 800"])
        form_layout.addWidget(self.polka_group)

        form_layout.addStretch()

        # Connect count changes to prefill logic
        for group, part_name in [
            (self.listwa_group, "listwa"),
            (self.wieniec_group, "wieniec"),
            (self.bok_group, "bok"),
            (self.front_group, "front"),
            (self.polka_group, "polka"),
        ]:
            group.count_spin.valueChanged.connect(
                lambda count, g=group, p=part_name: self._on_count_changed(g, p, count)
            )

    def _build_summary_bar(self) -> None:
        """Build the sticky summary bar."""
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self.summary_frame)

        self.summary_count_label = QLabel("")
        self.summary_parts_label = QLabel("")
        self.summary_area_label = QLabel("")

        layout.addWidget(self.summary_count_label)
        layout.addWidget(self.summary_parts_label)
        layout.addWidget(self.summary_area_label)

    def _build_buttons(self) -> None:
        """Build the button area."""
        self.button_layout_widget = QWidget()
        button_layout = QHBoxLayout(self.button_layout_widget)

        # Save and Add Another button
        self.save_and_add_button = QPushButton("Zapisz i dodaj kolejny")
        self.save_and_add_button.clicked.connect(self._save_and_add_another)
        button_layout.addWidget(self.save_and_add_button)

        button_layout.addStretch()

        # Standard buttons
        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setDefault(True)
        self.button_box.accepted.connect(self._try_accept)
        self.button_box.rejected.connect(self._try_reject)
        button_layout.addWidget(self.button_box)

    def _connect_change_signals(self) -> None:
        """Connect signals for change tracking and validation."""
        # Basic fields
        self.nazwa_edit.textChanged.connect(self._on_field_changed)
        self.kitchen_type_combo.currentTextChanged.connect(self._on_field_changed)
        self.hdf_plecy_check.toggled.connect(self._on_field_changed)

        # Part groups
        for group in [self.listwa_group, self.wieniec_group, self.bok_group,
                     self.front_group, self.polka_group]:
            group.count_spin.valueChanged.connect(self._on_field_changed)
            group.w_spin.valueChanged.connect(self._on_field_changed)
            group.h_spin.valueChanged.connect(self._on_field_changed)

    def _on_field_changed(self) -> None:
        """Handle field change."""
        self._is_dirty = True
        self._validate_form()
        self._update_summary()

    def _on_count_changed(self, group: CollapsiblePartGroup, part_name: str, count: int) -> None:
        """Handle count change with smart prefill."""
        if count > 0:
            defaults = self._part_defaults[part_name]
            if group.w_spin.value() == 0:
                group.w_spin.setValue(defaults.last_w)
            if group.h_spin.value() == 0:
                group.h_spin.setValue(defaults.last_h)

        # Store last used values
        if count > 0 and group.w_spin.value() > 0 and group.h_spin.value() > 0:
            defaults = self._part_defaults[part_name]
            defaults.last_w = int(group.w_spin.value())
            defaults.last_h = int(group.h_spin.value())

    def _validate_form(self) -> bool:
        """Validate the form and update UI state."""
        errors = []

        # Clear previous errors
        for group in [self.listwa_group, self.wieniec_group, self.bok_group,
                     self.front_group, self.polka_group]:
            group.clear_validation_errors()

        # Check name
        if not self.nazwa_edit.text().strip():
            errors.append("Nazwa jest wymagana")

        # Check parts
        parts_data = {
            "Listwy": (self.listwa_group.count_spin.value(),
                      self.listwa_group.w_spin.value(),
                      self.listwa_group.h_spin.value()),
            "Wieńce": (self.wieniec_group.count_spin.value(),
                      self.wieniec_group.w_spin.value(),
                      self.wieniec_group.h_spin.value()),
            "Boki": (self.bok_group.count_spin.value(),
                    self.bok_group.w_spin.value(),
                    self.bok_group.h_spin.value()),
            "Fronty": (self.front_group.count_spin.value(),
                      self.front_group.w_spin.value(),
                      self.front_group.h_spin.value()),
            "Półki": (self.polka_group.count_spin.value(),
                     self.polka_group.w_spin.value(),
                     self.polka_group.h_spin.value()),
        }

        groups = [self.listwa_group, self.wieniec_group, self.bok_group,
                 self.front_group, self.polka_group]

        for (part_name, (count, w, h)), group in zip(parts_data.items(), groups):
            if count > 0:
                if w <= 0:
                    group.set_validation_error("w", "Wymagane, gdy ilość > 0")
                    errors.append(f"{part_name}: Szerokość wymagana")
                if h <= 0:
                    group.set_validation_error("h", "Wymagane, gdy ilość > 0")
                    errors.append(f"{part_name}: Wysokość wymagana")

        # Update error banner
        if errors:
            self.error_banner.setText("Uzupełnij wymagane wymiary")
            self.error_banner.show()
        else:
            self.error_banner.hide()

        # Update save button state
        is_valid = len(errors) == 0
        self.save_button.setEnabled(is_valid)
        self.save_and_add_button.setEnabled(is_valid)

        return is_valid

    def _update_summary(self) -> None:
        """Update the summary bar."""
        total_count = (
            self.listwa_group.count_spin.value() +
            self.wieniec_group.count_spin.value() +
            self.bok_group.count_spin.value() +
            self.front_group.count_spin.value() +
            self.polka_group.count_spin.value()
        )

        # Per-type counts
        parts = []
        for name, group in [
            ("Boki", self.bok_group),
            ("Wieńce", self.wieniec_group),
            ("Półki", self.polka_group),
            ("Fronty", self.front_group),
            ("Listwy", self.listwa_group),
        ]:
            count = group.count_spin.value()
            if count > 0:
                parts.append(f"{name} x{count}")

        # Total area calculation (mm² → m²)
        total_area_mm2 = 0
        for group in [self.listwa_group, self.wieniec_group, self.bok_group,
                     self.front_group, self.polka_group]:
            count = group.count_spin.value()
            if count > 0:
                w = group.w_spin.value()
                h = group.h_spin.value()
                total_area_mm2 += count * w * h

        total_area_m2 = total_area_mm2 / 1_000_000  # Convert mm² to m²

        # Update labels
        self.summary_count_label.setText(f"<b>Łączna liczba elementów: {total_count}</b>")

        if parts:
            self.summary_parts_label.setText(f"Szczegóły: {', '.join(parts)}")
        else:
            self.summary_parts_label.setText("Szczegóły: brak elementów")

        self.summary_area_label.setText(f"Łączna powierzchnia: {total_area_m2:.2f} m²")

    def _store_original_data(self) -> None:
        """Store original data for dirty checking."""
        self._original_data = {
            "nazwa": self.nazwa_edit.text(),
            "kitchen_type": self.kitchen_type_combo.currentText(),
            "hdf_plecy": self.hdf_plecy_check.isChecked(),
            "listwa_count": self.listwa_group.count_spin.value(),
            "listwa_w": self.listwa_group.w_spin.value(),
            "listwa_h": self.listwa_group.h_spin.value(),
            "wieniec_count": self.wieniec_group.count_spin.value(),
            "wieniec_w": self.wieniec_group.w_spin.value(),
            "wieniec_h": self.wieniec_group.h_spin.value(),
            "bok_count": self.bok_group.count_spin.value(),
            "bok_w": self.bok_group.w_spin.value(),
            "bok_h": self.bok_group.h_spin.value(),
            "front_count": self.front_group.count_spin.value(),
            "front_w": self.front_group.w_spin.value(),
            "front_h": self.front_group.h_spin.value(),
            "polka_count": self.polka_group.count_spin.value(),
            "polka_w": self.polka_group.w_spin.value(),
            "polka_h": self.polka_group.h_spin.value(),
        }
        self._is_dirty = False

    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        if not self._is_dirty:
            return False

        current_data = {
            "nazwa": self.nazwa_edit.text(),
            "kitchen_type": self.kitchen_type_combo.currentText(),
            "hdf_plecy": self.hdf_plecy_check.isChecked(),
            "listwa_count": self.listwa_group.count_spin.value(),
            "listwa_w": self.listwa_group.w_spin.value(),
            "listwa_h": self.listwa_group.h_spin.value(),
            "wieniec_count": self.wieniec_group.count_spin.value(),
            "wieniec_w": self.wieniec_group.w_spin.value(),
            "wieniec_h": self.wieniec_group.h_spin.value(),
            "bok_count": self.bok_group.count_spin.value(),
            "bok_w": self.bok_group.w_spin.value(),
            "bok_h": self.bok_group.h_spin.value(),
            "front_count": self.front_group.count_spin.value(),
            "front_w": self.front_group.w_spin.value(),
            "front_h": self.front_group.h_spin.value(),
            "polka_count": self.polka_group.count_spin.value(),
            "polka_w": self.polka_group.w_spin.value(),
            "polka_h": self.polka_group.h_spin.value(),
        }

        return current_data != self._original_data

    def inject_kitchen_types(self, types: List[str]) -> None:
        """Inject available kitchen types into the combo box."""
        current_text = self.kitchen_type_combo.currentText()
        self.kitchen_type_combo.clear()
        self.kitchen_type_combo.addItems(types)

        # Restore selection if possible
        idx = self.kitchen_type_combo.findText(current_text)
        if idx >= 0:
            self.kitchen_type_combo.setCurrentIndex(idx)

    def _load_cabinet_type_data(self, source: Any, is_prefill: bool = False) -> None:
        """Load cabinet type data into the form fields."""
        self.nazwa_edit.setText("" if is_prefill else str(source.nazwa))

        idx = self.kitchen_type_combo.findText(str(source.kitchen_type))
        if idx >= 0:
            self.kitchen_type_combo.setCurrentIndex(idx)

        self.hdf_plecy_check.setChecked(bool(source.hdf_plecy))

        # Load part data
        parts_data = [
            (self.listwa_group, source.listwa_count, source.listwa_w_mm, source.listwa_h_mm),
            (self.wieniec_group, source.wieniec_count, source.wieniec_w_mm, source.wieniec_h_mm),
            (self.bok_group, source.bok_count, source.bok_w_mm, source.bok_h_mm),
            (self.front_group, source.front_count, source.front_w_mm, source.front_h_mm),
            (self.polka_group, source.polka_count, source.polka_w_mm, source.polka_h_mm),
        ]

        for group, count, w_mm, h_mm in parts_data:
            group.count_spin.setValue(int(count))
            if w_mm:
                group.w_spin.setValue(float(w_mm))
            if h_mm:
                group.h_spin.setValue(float(h_mm))

    def _reset_form(self) -> None:
        """Reset form to pristine state while preserving session data."""
        # Keep kitchen type and part defaults
        current_kitchen_type = self.kitchen_type_combo.currentText()

        # Reset basic fields
        self.nazwa_edit.clear()
        self.hdf_plecy_check.setChecked(False)

        # Reset part counts but keep dimensions as defaults
        for group in [self.listwa_group, self.wieniec_group, self.bok_group,
                     self.front_group, self.polka_group]:
            group.count_spin.setValue(0)
            group.w_spin.setValue(0)
            group.h_spin.setValue(0)

        # Restore kitchen type
        idx = self.kitchen_type_combo.findText(current_kitchen_type)
        if idx >= 0:
            self.kitchen_type_combo.setCurrentIndex(idx)

        # Reset state
        self._store_original_data()
        self._validate_form()
        self._update_summary()

        # Focus on name field
        self.nazwa_edit.setFocus()

    def _try_accept(self) -> None:
        """Try to save (with validation)."""
        if self._validate_form():
            self.accept()

    def _try_reject(self) -> None:
        """Try to cancel (with dirty state check)."""
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Niezapisane zmiany",
                "Masz niezapisane zmiany. Zamknąć okno?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.reject()
        else:
            self.reject()

    def _save_and_add_another(self) -> None:
        """Save current item and reset for next."""
        if not self._validate_form():
            return

        try:
            cabinet_data = self._build_cabinet_data()

            if self.cabinet_type_id:
                self.cabinet_type_service.update_cabinet_type(self.cabinet_type_id, **cabinet_data)
                logger.info(f"Updated cabinet type ID: {self.cabinet_type_id}")
            else:
                new_cabinet = self.cabinet_type_service.create_cabinet_type(**cabinet_data)
                logger.info(f"Created new cabinet type ID: {new_cabinet.id}")

            # Reset form for next item
            self.cabinet_type_id = None
            self.cabinet_type = None
            self.setWindowTitle("Nowy typ szafki")
            self._reset_form()

        except Exception as e:
            logger.error(f"Error saving cabinet type: {e}")
            msg = QMessageBox(QMessageBox.Icon.Critical, "Błąd",
                            "Nie udało się zapisać typu szafki.", QMessageBox.StandardButton.Ok, self)
            msg.setDetailedText(str(e))
            msg.exec()

    def _build_cabinet_data(self) -> Dict[str, Any]:
        """Build cabinet data dictionary for service call."""
        nazwa = self.nazwa_edit.text().strip()
        kitchen_type = self.kitchen_type_combo.currentText()
        hdf_plecy = self.hdf_plecy_check.isChecked()

        def mm_or_none(count: int, w: float, h: float) -> tuple[Optional[float], Optional[float]]:
            return (w if count > 0 else None, h if count > 0 else None)

        # Part data
        listwa_count = self.listwa_group.count_spin.value()
        listwa_w_mm, listwa_h_mm = mm_or_none(listwa_count,
                                              self.listwa_group.w_spin.value(),
                                              self.listwa_group.h_spin.value())

        wieniec_count = self.wieniec_group.count_spin.value()
        wieniec_w_mm, wieniec_h_mm = mm_or_none(wieniec_count,
                                                self.wieniec_group.w_spin.value(),
                                                self.wieniec_group.h_spin.value())

        bok_count = self.bok_group.count_spin.value()
        bok_w_mm, bok_h_mm = mm_or_none(bok_count,
                                        self.bok_group.w_spin.value(),
                                        self.bok_group.h_spin.value())

        front_count = self.front_group.count_spin.value()
        front_w_mm, front_h_mm = mm_or_none(front_count,
                                            self.front_group.w_spin.value(),
                                            self.front_group.h_spin.value())

        polka_count = self.polka_group.count_spin.value()
        polka_w_mm, polka_h_mm = mm_or_none(polka_count,
                                            self.polka_group.w_spin.value(),
                                            self.polka_group.h_spin.value())

        return {
            "nazwa": nazwa,
            "kitchen_type": kitchen_type,
            "hdf_plecy": hdf_plecy,
            "listwa_count": listwa_count,
            "listwa_w_mm": listwa_w_mm,
            "listwa_h_mm": listwa_h_mm,
            "wieniec_count": wieniec_count,
            "wieniec_w_mm": wieniec_w_mm,
            "wieniec_h_mm": wieniec_h_mm,
            "bok_count": bok_count,
            "bok_w_mm": bok_w_mm,
            "bok_h_mm": bok_h_mm,
            "front_count": front_count,
            "front_w_mm": front_w_mm,
            "front_h_mm": front_h_mm,
            "polka_count": polka_count,
            "polka_w_mm": polka_w_mm,
            "polka_h_mm": polka_h_mm,
        }

    def closeEvent(self, event) -> None:
        """Handle close event with dirty state check."""
        if self._has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Niezapisane zmiany",
                "Masz niezapisane zmiany. Zamknąć okno?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def accept(self) -> None:  # type: ignore[override]
        """Validate and save the cabinet type."""
        if not self._validate_form():
            return

        try:
            cabinet_data = self._build_cabinet_data()

            if self.cabinet_type_id:
                self.cabinet_type_service.update_cabinet_type(self.cabinet_type_id, **cabinet_data)
                logger.info(f"Updated cabinet type ID: {self.cabinet_type_id}")
            else:
                new_cabinet = self.cabinet_type_service.create_cabinet_type(**cabinet_data)
                logger.info(f"Created new cabinet type ID: {new_cabinet.id}")

            super().accept()

        except Exception as e:
            logger.error(f"Error saving cabinet type: {e}")
            msg = QMessageBox(QMessageBox.Icon.Critical, "Błąd",
                            "Nie udało się zapisać typu szafki.", QMessageBox.StandardButton.Ok, self)
            msg.setDetailedText(str(e))
            msg.exec()
