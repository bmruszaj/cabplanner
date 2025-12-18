"""Dialog for creating or editing cabinet types."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

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
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.orm import Session

from src.services.template_service import TemplateService
from src.gui.resources.styles import PRIMARY, BORDER_MEDIUM

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PartDefaults:
    """Default dimensions for cabinet parts."""

    last_w: int = 600
    last_h: int = 720


@dataclass
class PresetDefinition:
    """Definition of a preset with count and dimensions."""

    count: int
    width: int
    height: int


class PartStatusChip(QLabel):
    """A chip widget showing part status with color coding."""

    def __init__(self, part_name: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.part_name = part_name
        self.setProperty("chip", True)  # Mark as chip for QSS styling
        self.update_status(False, False, 0, 0, 0)  # Initial gray state

    def update_status(
        self, is_checked: bool, is_valid: bool, count: int, w: int, h: int
    ) -> None:
        """Update the chip appearance based on status."""
        if not is_checked:
            # Gray - unchecked
            self.setProperty("state", "off")
            self.setText(self.part_name)
        elif is_valid and count > 0:
            # Primary filled - valid and complete
            self.setProperty("state", "ok")
            self.setText(f"{self.part_name} x{count} ({w}×{h})")
        else:
            # Primary outline - checked but invalid
            self.setProperty("state", "warn")
            self.setText(self.part_name)

        # Repolish to apply new property state
        self.style().unpolish(self)
        self.style().polish(self)


class CollapsiblePartGroup(QGroupBox):
    """A collapsible group box with summary display when collapsed."""

    def __init__(
        self, title: str, part_key: str, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(title, parent)
        self.part_key = part_key
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._on_toggle)

        # Property for error state styling
        self.setProperty("invalid", False)

        # Set size policy for responsive layout
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

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

        # Szablon dropdown (Polish for "Template/Preset")
        self.presets_combo: QComboBox = QComboBox()
        self.presets_combo.addItem("Szablon...")
        self.presets_combo.setAccessibleName(f"Szablon dla {title}")

        preset_layout = QHBoxLayout()
        preset_label = QLabel("&Szablon:")
        preset_label.setBuddy(self.presets_combo)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.presets_combo)
        preset_layout.addStretch()

        self._content_layout.addRow(preset_layout)

        # Controls
        self.count_spin: QSpinBox = QSpinBox()
        self.count_spin.setRange(0, 10)
        self.count_spin.setToolTip("Wprowadź liczbę elementów")
        self.count_spin.setAccessibleName(f"Ilość dla {title}")

        count_label = QLabel("&Ilość:")
        count_label.setBuddy(self.count_spin)
        self._content_layout.addRow(count_label, self.count_spin)

        self.w_spin: QDoubleSpinBox = QDoubleSpinBox()
        self.h_spin: QDoubleSpinBox = QDoubleSpinBox()

        for spin in (self.w_spin, self.h_spin):
            spin.setRange(1, 5000)
            spin.setDecimals(0)
            spin.setSingleStep(10)  # Faster entry with 10mm steps
            spin.setSuffix(" mm")
            spin.setToolTip("Wprowadź w milimetrach")

        self.w_spin.setAccessibleName(f"Szerokość dla {title}")
        self.h_spin.setAccessibleName(f"Wysokość dla {title}")

        # Width field with error label
        w_label = QLabel("&Szerokość (mm):")
        w_label.setBuddy(self.w_spin)
        self._content_layout.addRow(w_label, self.w_spin)

        self.w_error_label: QLabel = QLabel("")
        self.w_error_label.setStyleSheet(f"color: {PRIMARY}; font-size: 11px;")
        self.w_error_label.hide()
        self._content_layout.addRow("", self.w_error_label)  # Proper alignment

        # Height field with error label
        h_label = QLabel("&Wysokość (mm):")
        h_label.setBuddy(self.h_spin)
        self._content_layout.addRow(h_label, self.h_spin)

        self.h_error_label: QLabel = QLabel("")
        self.h_error_label.setStyleSheet(f"color: {PRIMARY}; font-size: 11px;")
        self.h_error_label.hide()
        self._content_layout.addRow("", self.h_error_label)  # Proper alignment

        # Preset mapping
        self._presets: Dict[str, PresetDefinition] = {}

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
            # Unchecking a group should clear its data (delete parts semantics)
            self.count_spin.setValue(
                0
            )  # this will cascade and zero w/h via _on_count_changed
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
        is_invalid = self.property("invalid") and self.isChecked()

        if count == 0:
            summary = "0 elementów"
        else:
            w = int(self.w_spin.value())
            h = int(self.h_spin.value())
            summary = f"{count}× • {w}×{h} mm"

        # Add error indicator to collapsed summary only if checked and invalid
        if is_invalid and not self.isChecked():
            summary += f" <span style='color: {PRIMARY}; font-weight: bold;'>•</span>"

        self._summary_label.setText(summary)

    def _on_preset_selected(self, preset: str) -> None:
        """Handle preset selection."""
        if preset == "Szablon..." or preset not in self._presets:
            return

        preset_def = self._presets[preset]
        self.count_spin.setValue(preset_def.count)
        self.w_spin.setValue(preset_def.width)
        self.h_spin.setValue(preset_def.height)

        # Reset combo to default
        self.presets_combo.setCurrentIndex(0)

    def set_presets(self, presets: Dict[str, PresetDefinition]) -> None:
        """Set available presets with structured data."""
        self._presets = presets
        self.presets_combo.clear()
        self.presets_combo.addItem("Szablon...")
        self.presets_combo.addItems(list(presets.keys()))

    def set_validation_error(self, field: str, error: str) -> None:
        """Set validation error for a field."""
        if field == "w":
            self.w_error_label.setText(error)
            self.w_error_label.setVisible(bool(error))
            self.w_spin.setProperty("error", bool(error))
        elif field == "h":
            self.h_error_label.setText(error)
            self.h_error_label.setVisible(bool(error))
            self.h_spin.setProperty("error", bool(error))

        # Update widget style
        self.w_spin.style().unpolish(self.w_spin)
        self.w_spin.style().polish(self.w_spin)
        self.h_spin.style().unpolish(self.h_spin)
        self.h_spin.style().polish(self.h_spin)

    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.set_validation_error("w", "")
        self.set_validation_error("h", "")
        self.setProperty("invalid", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self._update_summary()

    def set_invalid(self, invalid: bool) -> None:
        """Set the invalid state for the group."""
        self.setProperty("invalid", invalid)
        self.style().unpolish(self)
        self.style().polish(self)
        self._update_summary()


def is_part_valid(count: int, w: float, h: float) -> bool:
    """Check if part configuration is valid."""
    if count == 0:
        return True
    return w > 0 and h > 0


def validate_form_data(
    nazwa: str, parts_data: Dict[str, Tuple[int, float, float, bool]]
) -> List[str]:
    """Get comprehensive form validation errors - only for checked groups. Name validation removed."""
    errors = []

    # Name validation removed - handled separately in dialog

    # Check parts using the helper - only for checked groups
    for part_name, (count, w, h, is_checked) in parts_data.items():
        if is_checked:
            if count <= 0:
                errors.append(f"{part_name}: Ilość wymagana")
            if w <= 0:
                errors.append(f"{part_name}: Szerokość wymagana")
            if h <= 0:
                errors.append(f"{part_name}: Wysokość wymagana")

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
        self.cabinet_type_service = TemplateService(self.session)

        self.cabinet_type_id: Optional[int] = cabinet_type_id
        self.cabinet_type: Optional[Any] = None

        # Typed widget attributes
        self.nazwa_edit: QLineEdit
        self.kitchen_type_combo: QComboBox
        self.hdf_plecy_check: QCheckBox
        self.error_banner: QFrame
        self.error_label: QLabel
        self.error_dismiss_btn: QToolButton
        self.header_frame: QFrame
        self.content_scroll: QScrollArea
        self.content_widget: QWidget
        self.content_layout: QVBoxLayout
        self.parts_grid: QGridLayout
        self.footer_frame: QFrame
        self.save_and_add_button: QPushButton
        self.button_box: QDialogButtonBox
        self.save_button: QPushButton

        # Parts registry for DRY operations
        self._parts: List[Tuple[str, CollapsiblePartGroup, str]] = []

        # Status chips for summary
        self._status_chips: Dict[str, PartStatusChip] = {}

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

        # Responsive layout tracking
        self._current_cols = 1
        self._min_card_width = 380

        # Submit attempt flag - show validation UI only after first save attempt
        self._show_errors = False

        if cabinet_type_id:
            self.cabinet_type = self.cabinet_type_service.get_template(cabinet_type_id)

        # Window configuration for minimize/maximize/resize support
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setSizeGripEnabled(True)

        self._build_ui()
        self._setup_styling()

        if self.cabinet_type:
            self.setWindowTitle("Edytuj typ szafki")
            self._load_cabinet_type_data(self.cabinet_type)
        elif prefill_cabinet is not None:
            self.setWindowTitle(
                f"Nowy typ szafki (na podstawie: {prefill_cabinet.name})"
            )
            self._load_cabinet_type_data(prefill_cabinet, is_prefill=True)
        else:
            self.setWindowTitle("Nowy typ szafki")

        # Store original data for dirty checking
        self._store_original_data()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Initial validation and focus
        self._validate_form()
        self.nazwa_edit.setFocus()

        # Start maximized for full-window editor card
        self.setWindowState(Qt.WindowState.WindowMaximized)

    def _setup_styling(self) -> None:
        """Setup stylesheet for error states using theme constants."""
        self.setStyleSheet(f"""
            /* Chips */
            QLabel[chip="true"][state="off"] {{
                background: #E0E0E0;
                color: #616161;
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 11px; 
                font-weight: 600;
            }}
            QLabel[chip="true"][state="ok"] {{
                background: {PRIMARY};
                color: white;
                padding: 4px 8px; 
                border-radius: 12px; 
                font-size: 11px; 
                font-weight: 600;
            }}
            QLabel[chip="true"][state="warn"] {{
                background: transparent;
                color: {PRIMARY};
                border: 1px solid {PRIMARY};
                padding: 3px 7px; 
                border-radius: 11px; 
                font-size: 11px; 
                font-weight: 600;
            }}

            /* Field error (minimal, primary) */
            QSpinBox[error="true"], QDoubleSpinBox[error="true"] {{
                border: 2px solid {PRIMARY};
                border-radius: 4px;
            }}

            /* Group invalid (minimal, primary accent) */
            QGroupBox[invalid="true"] {{
                border-left: 3px solid {PRIMARY};
            }}
            QGroupBox[invalid="true"]::title {{
                color: {PRIMARY};
                font-weight: 600;
            }}

            /* Error banner – neutral gray + primary text */
            #errBanner {{
                background: #F5F5F5;
                border: 1px solid {BORDER_MEDIUM};
                border-radius: 6px;
                padding: 8px;
            }}
            #errLabel {{ 
                color: {PRIMARY}; 
                font-weight: 600; 
            }}
            #errClose {{ 
                color: {PRIMARY}; 
            }}

            /* Header and Footer frames */
            #headerFrame, #footerFrame {{
                background: #FAFAFA;
                border-bottom: 1px solid {BORDER_MEDIUM};
                border-top: 1px solid {BORDER_MEDIUM};
            }}
        """)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Ctrl+Enter and Ctrl+S to save
        self.shortcut_save1 = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_save1.activated.connect(self._try_accept)

        self.shortcut_save2 = QShortcut(QKeySequence("Ctrl+Enter"), self)
        self.shortcut_save2.activated.connect(self._try_accept)

        self.shortcut_save3 = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save3.activated.connect(self._try_accept)

    def _build_ui(self) -> None:
        """Build the single full-window editor card UI."""
        # Set size policy to expand
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header (sticky)
        self._build_header()
        main_layout.addWidget(self.header_frame)

        # Error banner (between header and content)
        self._build_error_banner()
        main_layout.addWidget(self.error_banner)

        # Content (scrollable)
        self._build_body()
        main_layout.addWidget(self.content_scroll, 1)  # Stretch to fill

        # Footer (sticky)
        self._build_footer()
        main_layout.addWidget(self.footer_frame)

        # Connect change signals for dirty tracking
        self._connect_change_signals()

    def _build_header(self) -> None:
        """Build the sticky header with title and controls."""
        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        self.header_frame.setFixedHeight(80)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Left side: Title and chips
        left_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Nowy typ szafki")
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin-bottom: 4px;"
        )
        left_layout.addWidget(title_label)

        # Status chips row
        chips_layout = QHBoxLayout()
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(8)

        # Create status chips for each part (in specific order)
        chip_names = ["Boki", "Wieńce", "Półki", "Fronty", "Listwy"]
        for chip_name in chip_names:
            chip = PartStatusChip(chip_name)
            self._status_chips[chip_name] = chip
            chips_layout.addWidget(chip)

        chips_layout.addStretch()
        left_layout.addLayout(chips_layout)

        header_layout.addLayout(left_layout)
        header_layout.addStretch()

        # Right side: Controls
        right_layout = QHBoxLayout()
        right_layout.setSpacing(12)

        # Kitchen type combo
        kitchen_label = QLabel("Typ kuchni:")
        kitchen_label.setStyleSheet("font-weight: 600;")
        right_layout.addWidget(kitchen_label)

        self.kitchen_type_combo = QComboBox()
        self.kitchen_type_combo.setAccessibleName("Typ kuchni")
        self.kitchen_type_combo.setMinimumWidth(150)
        right_layout.addWidget(self.kitchen_type_combo)

        # HDF checkbox
        self.hdf_plecy_check = QCheckBox("Plecy HDF")
        self.hdf_plecy_check.setAccessibleName("Plecy HDF")
        self.hdf_plecy_check.setToolTip(
            "Plecy HDF - określa czy szafka ma tylną ścianę z płyty HDF"
        )
        right_layout.addWidget(self.hdf_plecy_check)

        header_layout.addLayout(right_layout)

    def _build_body(self) -> None:
        """Build the scrollable content area with single-column responsive layout."""
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.content_widget = QWidget()
        self.content_scroll.setWidget(self.content_widget)

        # Single column vertical layout
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(16)

        # Basic Information group (full width)
        basic_group = QGroupBox("Informacje podstawowe")
        basic_form = QFormLayout(basic_group)

        self.nazwa_edit = QLineEdit()
        self.nazwa_edit.setPlaceholderText("Szafka dolna 60")
        self.nazwa_edit.setAccessibleName("Nazwa szafki")
        nazwa_label = QLabel("&Nazwa:")
        nazwa_label.setBuddy(self.nazwa_edit)
        basic_form.addRow(nazwa_label, self.nazwa_edit)

        self.content_layout.addWidget(basic_group)

        # Create parts container widget
        parts_container = QWidget()
        self.parts_grid = QGridLayout(parts_container)
        self.parts_grid.setSpacing(12)

        # Define presets at dialog level
        standard_presets = {
            "Standard 720": PresetDefinition(2, 600, 720),
            "Niska 600": PresetDefinition(2, 600, 600),
            "Wysoka 900": PresetDefinition(2, 600, 900),
        }

        custom_presets = {
            "Standard 720": PresetDefinition(2, 600, 720),
            "Mała 400": PresetDefinition(2, 400, 720),
            "Szeroka 800": PresetDefinition(2, 800, 720),
        }

        # Create collapsible part groups and populate registry
        part_groups = [
            ("listwa", "Listwy", standard_presets),
            ("wieniec", "Wieńce", standard_presets),
            ("bok", "Boki", standard_presets),
            ("front", "Fronty", custom_presets),
            ("polka", "Półki", custom_presets),
        ]

        for i, (part_key, display_name, presets) in enumerate(part_groups):
            group = CollapsiblePartGroup(display_name, part_key)
            group.set_presets(presets)
            self._parts.append((part_key, group, display_name))

            # Connect count changes to prefill logic
            group.count_spin.valueChanged.connect(
                lambda count, g=group, p=part_key: self._on_count_changed(g, p, count)
            )

        # Initial layout of parts
        self._relayout_parts()

        self.content_layout.addWidget(parts_container)
        self.content_layout.addStretch()

    def _relayout_parts(self) -> None:
        """Relayout parts in responsive grid based on current width."""
        # Calculate number of columns based on available width
        if hasattr(self, "content_scroll") and self.content_scroll.isVisible():
            viewport_width = (
                self.content_scroll.viewport().width() - 32
            )  # Account for margins
        else:
            viewport_width = 800  # Default fallback

        cols = max(1, min(3, viewport_width // self._min_card_width))

        # Only relayout if column count changed
        if cols != self._current_cols:
            self._current_cols = cols

            # Clear existing layout
            for i in reversed(range(self.parts_grid.count())):
                self.parts_grid.itemAt(i).widget().setParent(None)

            # Add parts back in new grid arrangement
            for i, (_, group, _) in enumerate(self._parts):
                row, col = divmod(i, cols)
                self.parts_grid.addWidget(group, row, col)

    def resizeEvent(self, event) -> None:
        """Handle resize events for responsive layout."""
        super().resizeEvent(event)
        if hasattr(self, "_parts") and self._parts:
            self._relayout_parts()

    def _build_footer(self) -> None:
        """Build the sticky footer with actions."""
        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("footerFrame")
        self.footer_frame.setFixedHeight(60)

        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(16, 12, 16, 12)

        # Left: Info text
        info_label = QLabel("Ctrl+S – Zapisz; Esc – Zamknij")
        info_label.setStyleSheet("color: #757575; font-size: 11px;")
        footer_layout.addWidget(info_label)

        footer_layout.addStretch()

        # Right: Buttons
        # Save and Add Another button (ghost style)
        self.save_and_add_button = QPushButton("Zapisz i dodaj kolejny")
        self.save_and_add_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {PRIMARY};
                border: 1px solid {PRIMARY};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {PRIMARY};
                color: white;
            }}
            QPushButton:disabled {{
                color: #BDBDBD;
                border-color: #BDBDBD;
                background: transparent;
            }}
        """)
        self.save_and_add_button.clicked.connect(self._save_and_add_another)
        footer_layout.addWidget(self.save_and_add_button)

        # Standard buttons
        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setText("Zapi&sz")  # Alt+S mnemonic
        self.save_button.setDefault(True)
        self.button_box.accepted.connect(self._try_accept)
        self.button_box.rejected.connect(self._try_reject)
        footer_layout.addWidget(self.button_box)

    def _build_error_banner(self) -> None:
        """Build dismissible error banner."""
        self.error_banner = QFrame()
        self.error_banner.setObjectName("errBanner")

        banner_layout = QHBoxLayout(self.error_banner)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errLabel")
        self.error_label.setWordWrap(True)
        banner_layout.addWidget(self.error_label)

        self.error_dismiss_btn = QToolButton()
        self.error_dismiss_btn.setText("×")
        self.error_dismiss_btn.setObjectName("errClose")
        # Fix the RGBA color format for hover effect
        primary_rgb = PRIMARY.replace("#", "")
        r, g, b = (
            int(primary_rgb[0:2], 16),
            int(primary_rgb[2:4], 16),
            int(primary_rgb[4:6], 16),
        )
        self.error_dismiss_btn.setStyleSheet(f"""
            QToolButton {{
                background: none;
                border: none;
                font-weight: bold;
                font-size: 16px;
                width: 20px;
                height: 20px;
            }}
            QToolButton:hover {{
                background-color: rgba({r}, {g}, {b}, 0.1);
            }}
        """)
        self.error_dismiss_btn.clicked.connect(lambda: self.error_banner.hide())
        banner_layout.addWidget(self.error_dismiss_btn)

        self.error_banner.hide()

    def _connect_change_signals(self) -> None:
        """Connect signals for change tracking and validation."""
        # Basic fields
        self.nazwa_edit.textChanged.connect(self._on_field_changed)
        self.kitchen_type_combo.currentTextChanged.connect(self._on_field_changed)
        self.hdf_plecy_check.toggled.connect(self._on_field_changed)

        # Part groups - connect all relevant signals including check state
        for _, group, _ in self._parts:
            group.count_spin.valueChanged.connect(self._on_field_changed)
            group.w_spin.valueChanged.connect(self._on_field_changed)
            group.h_spin.valueChanged.connect(self._on_field_changed)
            group.presets_combo.currentTextChanged.connect(self._on_field_changed)
            group.toggled.connect(self._on_field_changed)  # Group check state

    def _on_field_changed(self) -> None:
        """Handle field change."""
        self._is_dirty = True
        self._validate_form(
            show_errors=self._show_errors
        )  # only paint errors after first save attempt
        self._update_summary()

    def _on_count_changed(
        self, group: CollapsiblePartGroup, part_name: str, count: int
    ) -> None:
        """Handle count change with smart prefill."""
        if count > 0 and group.isChecked():
            defaults = self._part_defaults[part_name]
            # Prefill with defaults if current values are zero
            if group.w_spin.value() == 0:
                # Use stored defaults, or fallback to 600 if never set
                prefill_w = defaults.last_w if defaults.last_w > 0 else 600
                group.w_spin.setValue(prefill_w)
            if group.h_spin.value() == 0:
                prefill_h = defaults.last_h if defaults.last_h > 0 else 720
                group.h_spin.setValue(prefill_h)

        # Update defaults when user changes dimensions after setting count
        if count > 0 and group.w_spin.value() > 0 and group.h_spin.value() > 0:
            defaults = self._part_defaults[part_name]
            defaults.last_w = int(group.w_spin.value())
            defaults.last_h = int(group.h_spin.value())

    def _validate_form(self, show_errors: bool = False) -> bool:
        """Validate the form and update UI state with optional error display."""
        # Clear previous visual errors always
        for _, group, _ in self._parts:
            group.clear_validation_errors()
            if not show_errors:
                group.set_invalid(False)

        # Gather validation data - include check state
        nazwa = self.nazwa_edit.text().strip()
        parts_data = {}
        for part_key, group, display_name in self._parts:
            parts_data[display_name] = (
                group.count_spin.value(),
                group.w_spin.value(),
                group.h_spin.value(),
                group.isChecked(),  # Include check state
            )

        # Build errors ONLY for checked groups
        part_errors = []
        for display_name, (count, w, h, is_checked) in parts_data.items():
            if is_checked:
                if count <= 0:
                    part_errors.append(f"{display_name}: Ilość wymagana")
                if w <= 0:
                    part_errors.append(f"{display_name}: Szerokość wymagana")
                if h <= 0:
                    part_errors.append(f"{display_name}: Wysokość wymagana")

        # Name + kitchen checks are evaluated for can_save
        name_ok = bool(nazwa)
        kitchen_ok = self.kitchen_type_combo.count() > 0
        parts_ok = len(part_errors) == 0

        can_save = name_ok and kitchen_ok and parts_ok

        # Only after first save attempt (show_errors=True) paint visuals + banner
        if show_errors:
            # group-level invalid + inline hints
            for _, g, display_name in self._parts:
                count, w, h, is_checked = parts_data[display_name]
                invalid = False
                if is_checked:
                    if count <= 0:
                        invalid = True
                        g.set_validation_error("w", "")
                        g.set_validation_error("h", "")
                    if count > 0 and w <= 0:
                        invalid = True
                        g.set_validation_error("w", "Wymagane, gdy ilość > 0")
                    if count > 0 and h <= 0:
                        invalid = True
                        g.set_validation_error("h", "Wymagane, gdy ilość > 0")
                g.set_invalid(invalid)

            # Build banner ONLY now; include name & kitchen messages here
            banner_msgs = []
            if not name_ok:
                banner_msgs.append("Nazwa: Wymagana")
            if not kitchen_ok:
                banner_msgs.append("Typ kuchni: Wybierz typ kuchni")
            banner_msgs.extend(part_errors)

            if banner_msgs:
                error_html = (
                    "<ul style='margin: 0; padding-left: 20px;'>"
                    + "".join(f"<li>{m}</li>" for m in banner_msgs)
                    + "</ul>"
                )
                self.error_label.setText(error_html)
                self.error_banner.show()
            else:
                self.error_banner.hide()
        else:
            # before any save attempt, keep banner hidden and no red outlines
            self.error_banner.hide()

        return can_save

    def _update_summary(self) -> None:
        """Update the status chips in header."""
        # Update status chips
        for part_key, group, display_name in self._parts:
            if display_name in self._status_chips:
                chip = self._status_chips[display_name]
                count = group.count_spin.value()
                w = int(group.w_spin.value())
                h = int(group.h_spin.value())
                is_checked = group.isChecked()
                is_valid = is_part_valid(count, w, h) if is_checked else True

                chip.update_status(is_checked, is_valid, count, w, h)

    def _store_original_data(self) -> None:
        """Store original data for dirty checking."""
        self._original_data = {
            "nazwa": self.nazwa_edit.text(),
            "kitchen_type": self.kitchen_type_combo.currentText(),
            "hdf_plecy": self.hdf_plecy_check.isChecked(),
        }

        # Add all parts data including check state
        for part_key, group, _ in self._parts:
            self._original_data.update(
                {
                    f"{part_key}_count": group.count_spin.value(),
                    f"{part_key}_w": group.w_spin.value(),
                    f"{part_key}_h": group.h_spin.value(),
                    f"{part_key}_checked": group.isChecked(),
                }
            )

        self._is_dirty = False

    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        if not self._is_dirty:
            return False

        current_data = {
            "nazwa": self.nazwa_edit.text(),
            "kitchen_type": self.kitchen_type_combo.currentText(),
            "hdf_plecy": self.hdf_plecy_check.isChecked(),
        }

        # Add current parts data including check state
        for part_key, group, _ in self._parts:
            current_data.update(
                {
                    f"{part_key}_count": group.count_spin.value(),
                    f"{part_key}_w": group.w_spin.value(),
                    f"{part_key}_h": group.h_spin.value(),
                    f"{part_key}_checked": group.isChecked(),
                }
            )

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

        # Trigger validation after injection
        self._validate_form()

    def _load_cabinet_type_data(self, source: Any, is_prefill: bool = False) -> None:
        """Load cabinet type data into the form fields."""
        self.nazwa_edit.setText("" if is_prefill else str(source.name))

        idx = self.kitchen_type_combo.findText(str(source.kitchen_type))
        if idx >= 0:
            self.kitchen_type_combo.setCurrentIndex(idx)

        self.hdf_plecy_check.setChecked(bool(source.hdf_plecy))

        # Load part data using registry
        for part_key, group, _ in self._parts:
            count = getattr(source, f"{part_key}_count", 0)
            w_mm = getattr(source, f"{part_key}_w_mm", None)
            h_mm = getattr(source, f"{part_key}_h_mm", None)

            # Set group as checked if it has data
            group.setChecked(count > 0)
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

        # Reset part counts but keep defaults and check state
        for _, group, _ in self._parts:
            group.setChecked(True)  # Default to checked
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
            # Create custom message box with Polish buttons
            msg = QMessageBox(self)
            msg.setWindowTitle("Niezapisane zmiany")
            msg.setText("Masz niezapisane zmiany. Zamknąć okno?")
            msg.setIcon(QMessageBox.Icon.Question)

            # Custom Polish buttons
            tak_btn = msg.addButton("Tak", QMessageBox.ButtonRole.YesRole)
            nie_btn = msg.addButton("Nie", QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(nie_btn)

            msg.exec()

            if msg.clickedButton() == tak_btn:
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
                self.cabinet_type_service.update_cabinet_type(
                    self.cabinet_type_id, **cabinet_data
                )
                logger.info(f"Updated cabinet type ID: {self.cabinet_type_id}")
            else:
                new_cabinet = self.cabinet_type_service.create_cabinet_type(
                    **cabinet_data
                )
                logger.info(f"Created new cabinet type ID: {new_cabinet.id}")

            # Reset form for next item
            self.cabinet_type_id = None
            self.cabinet_type = None
            self.setWindowTitle("Nowy typ szafki")
            self._reset_form()

        except Exception as e:
            logger.error(f"Error saving cabinet type: {e}")
            msg = QMessageBox(
                QMessageBox.Icon.Critical,
                "Błąd",
                "Nie udało się zapisać typu szafki.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.setDetailedText(str(e))
            msg.exec()

    def _build_cabinet_data(self) -> Dict[str, Any]:
        """Build cabinet data dictionary for service call - honors group check-state."""
        nazwa = self.nazwa_edit.text().strip()
        kitchen_type = self.kitchen_type_combo.currentText()
        hdf_plecy = self.hdf_plecy_check.isChecked()

        def mm_or_none(
            count: int, w: float, h: float, is_checked: bool
        ) -> Tuple[Optional[float], Optional[float]]:
            # If group is unchecked, force None regardless of values
            if not is_checked:
                return (None, None)
            return (w if count > 0 else None, h if count > 0 else None)

        # Build data using registry
        cabinet_data: Dict[str, Any] = {
            "nazwa": nazwa,
            "kitchen_type": kitchen_type,
            "hdf_plecy": hdf_plecy,
        }

        for part_key, group, _ in self._parts:
            count = group.count_spin.value() if group.isChecked() else 0
            w_mm, h_mm = mm_or_none(
                count, group.w_spin.value(), group.h_spin.value(), group.isChecked()
            )

            cabinet_data[f"{part_key}_count"] = count
            cabinet_data[f"{part_key}_w_mm"] = w_mm
            cabinet_data[f"{part_key}_h_mm"] = h_mm

        return cabinet_data

    def closeEvent(self, event) -> None:
        """Handle close event with dirty state check."""
        if self._has_unsaved_changes():
            # Create custom message box with Polish buttons
            msg = QMessageBox(self)
            msg.setWindowTitle("Niezapisane zmiany")
            msg.setText("Masz niezapisane zmiany. Zamknąć okno?")
            msg.setIcon(QMessageBox.Icon.Question)

            # Custom Polish buttons
            tak_btn = msg.addButton("Tak", QMessageBox.ButtonRole.YesRole)
            nie_btn = msg.addButton("Nie", QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(nie_btn)

            msg.exec()

            if msg.clickedButton() == tak_btn:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def get_cabinet_data(self) -> Dict[str, Any]:
        """Get the cabinet data for external use."""
        return self._build_cabinet_data()
