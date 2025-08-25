"""
Project Details - Merged implementation.

This module contains the complete project details functionality merged from the
original project_details package. Provides both view and controller in one place.
"""

from __future__ import annotations

import logging
import os
import platform
from typing import Any, Dict, List, TYPE_CHECKING

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QSettings,
    QSize,
    QSortFilterProxyModel,
    QTimer,
    Signal,
    QEvent,
    QRect,
    QPoint,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QToolButton,
    QTableView,
    QStackedWidget,
    QScrollArea,
    QFrame,
    QSpinBox,
    QLineEdit,
    QDialogButtonBox,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QLayout,
)

from sqlalchemy.orm import Session

# Import existing services and resources
from src.db_schema.orm_models import Project, ProjectCabinet
from src.gui.add_cabinet_dialog import AddCabinetDialog
from src.gui.adhoc_cabinet_dialog import AdhocCabinetDialog
from src.gui.resources.styles import get_theme
from src.gui.resources.resources import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Constants
ICON_SIZE = QSize(24, 24)
SMALL_ICON_SIZE = QSize(16, 16)
LARGE_ICON_SIZE = QSize(32, 32)
BANNER_ICON_SIZE = QSize(20, 20)
HEADER_HEIGHT = 60
TOOLBAR_HEIGHT = 40
CONTENT_MARGINS = (12, 12, 12, 12)
LAYOUT_SPACING = 8
SECTION_SPACING = 16
WIDGET_SPACING = 4
CARD_WIDTH = 320
CARD_MIN_W = 320
CARD_MIN_H = 200
CARD_RADIUS = 12
CARD_PADDING = 16
CARD_GRID_SPACING = 16  # Space between cards
VIEW_MODE_CARDS = "cards"
VIEW_MODE_TABLE = "table"
COLOR_CHIP_SIZE = 16
QUANTITY_STEPPER_BUTTON_SIZE = 24
QUANTITY_INPUT_WIDTH = 50
MIN_CABINET_QUANTITY = 1
MAX_CABINET_QUANTITY = 999


# Utility functions
def open_or_print(file_path: str, action: str = "open") -> bool:
    """Open or print a file using OS default application."""
    try:
        if action == "print" and platform.system() == "Windows":
            os.startfile(file_path, "print")
        else:
            os.startfile(file_path)
        return True
    except Exception as e:
        logger.error(f"Failed to {action} file {file_path}: {e}")
        return False


# Widget Components
class ColorChip(QWidget):
    """Small color chip widget for displaying cabinet colors."""

    def __init__(self, color: str, label: str = "", parent=None):
        super().__init__(parent)
        self.color = color
        self.label = label
        self.setFixedSize(COLOR_CHIP_SIZE, COLOR_CHIP_SIZE)
        self.setToolTip(f"{label}: {color}" if label else color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(self.color)))
        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.drawRoundedRect(0, 0, COLOR_CHIP_SIZE, COLOR_CHIP_SIZE, 4, 4)


class QuantityStepper(QWidget):
    """Inline quantity stepper widget."""

    value_changed = Signal(int)

    def __init__(self, initial_value: int = 1, parent=None):
        super().__init__(parent)
        self._value = max(
            MIN_CABINET_QUANTITY, min(MAX_CABINET_QUANTITY, initial_value)
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.decrease_btn = QPushButton("–")
        self.decrease_btn.setFixedSize(
            QUANTITY_STEPPER_BUTTON_SIZE, QUANTITY_STEPPER_BUTTON_SIZE
        )
        self.decrease_btn.clicked.connect(self._decrease_value)
        layout.addWidget(self.decrease_btn)

        self.spinbox = QSpinBox()
        self.spinbox.setRange(MIN_CABINET_QUANTITY, MAX_CABINET_QUANTITY)
        self.spinbox.setValue(self._value)
        self.spinbox.setFixedSize(QUANTITY_INPUT_WIDTH, QUANTITY_STEPPER_BUTTON_SIZE)
        self.spinbox.setButtonSymbols(QSpinBox.NoButtons)
        self.spinbox.setAlignment(Qt.AlignCenter)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        layout.addWidget(self.spinbox)

        self.increase_btn = QPushButton("+")
        self.increase_btn.setFixedSize(
            QUANTITY_STEPPER_BUTTON_SIZE, QUANTITY_STEPPER_BUTTON_SIZE
        )
        self.increase_btn.clicked.connect(self._increase_value)
        layout.addWidget(self.increase_btn)

    def _decrease_value(self):
        new_value = max(MIN_CABINET_QUANTITY, self._value - 1)
        if new_value != self._value:
            self.set_value(new_value)

    def _increase_value(self):
        new_value = min(MAX_CABINET_QUANTITY, self._value + 1)
        if new_value != self._value:
            self.set_value(new_value)

    def _on_spinbox_changed(self, value: int):
        if value != self._value:
            self.set_value(value)

    def set_value(self, value: int):
        old_value = self._value
        self._value = max(MIN_CABINET_QUANTITY, min(MAX_CABINET_QUANTITY, value))

        if self._value != old_value:
            if self.spinbox.value() != self._value:
                self.spinbox.blockSignals(True)
                self.spinbox.setValue(self._value)
                self.spinbox.blockSignals(False)

            self.value_changed.emit(self._value)

    def get_value(self) -> int:
        return self._value


class SequenceNumberInput(QWidget):
    """Editable sequence number widget with enhanced validation."""

    sequence_changed = Signal(int)

    def __init__(self, initial_value: int, parent=None):
        super().__init__(parent)
        self._value = initial_value
        self._editing = False
        self._validation_callback = None
        self._duplicate_check_callback = None
        self._min_value = 1
        self._max_value = 999
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Display label (shows when not editing)
        self.display_label = QLabel(f"#{self._value}")
        self.display_label.setProperty("class", "sequence-display")
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setMinimumWidth(40)
        self.display_label.setMaximumWidth(60)
        self.display_label.setStyleSheet("""
            QLabel[class="sequence-display"] {
                padding: 4px 6px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f8f9fa;
                color: #666;
                font-size: 12px;
                font-weight: bold;
            }
            QLabel[class="sequence-display"]:hover {
                border-color: #2196F3;
                background-color: #ffffff;
                color: #2196F3;
            }
        """)
        self.display_label.mousePressEvent = self._start_editing
        layout.addWidget(self.display_label)

        # Input field (shows when editing)
        self.input_field = QLineEdit(str(self._value))
        self.input_field.setProperty("class", "sequence-input")
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setMinimumWidth(40)
        self.input_field.setMaximumWidth(60)
        self.input_field.setMaxLength(3)  # Limit to 3 digits max
        self.input_field.setPlaceholderText("#")
        self.input_field.setStyleSheet("""
            QLineEdit[class="sequence-input"] {
                padding: 4px 6px;
                border: 2px solid #2196F3;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.input_field.hide()
        self.input_field.editingFinished.connect(self._finish_editing)
        self.input_field.textChanged.connect(self._validate_input_realtime)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field)

        # Set up number validation (1-999 range)
        from PySide6.QtGui import QIntValidator

        validator = QIntValidator(1, 999, self)
        self.input_field.setValidator(validator)

    def eventFilter(self, obj, event):
        """Handle key events for the input field with safety checks."""
        try:
            if obj == self.input_field and event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self._cancel_editing()
                    return True
                elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    self._finish_editing()
                    return True
        except RuntimeError:
            # Widget was deleted, ignore the event
            return False
        return super().eventFilter(obj, event)

    def _validate_input_realtime(self, text: str):
        """Real-time validation as user types."""
        try:
            if not text:
                self._set_input_style("normal")
                return

            value = int(text)

            # Check range
            if value < self._min_value or value > self._max_value:
                self._set_input_style("error")
                self.input_field.setToolTip(
                    f"Numer sekwencji musi być między {self._min_value} a {self._max_value}"
                )
                return

            # Check for duplicates if callback is set
            if self._duplicate_check_callback and value != self._value:
                if self._duplicate_check_callback(value):
                    self._set_input_style("warning")
                    self.input_field.setToolTip(f"Numer sekwencji {value} już istnieje")
                    return

            # Valid input
            self._set_input_style("valid")
            self.input_field.setToolTip("")

        except ValueError:
            self._set_input_style("error")
            self.input_field.setToolTip("Wprowadź poprawny numer")

    def _set_input_style(self, state: str):
        """Set input field style based on validation state."""
        styles = {
            "normal": "",
            "valid": "border: 2px solid #9e9e9e;",  # Grey for valid
            "warning": "border: 2px solid #757575; background-color: #f5f5f5;",  # Darker grey for warning
            "error": "border: 2px solid #616161; background-color: #eeeeee;",  # Dark grey for error
        }
        self.input_field.setStyleSheet(styles.get(state, ""))

    def _start_editing(self, event):
        if not self._editing:
            self._editing = True
            self.display_label.hide()
            self.input_field.setText(str(self._value))
            self.input_field.show()
            self.input_field.setFocus()
            self.input_field.selectAll()

    def _finish_editing(self):
        """Finish editing with safety checks for widget deletion."""
        if not self._editing:
            return

        try:
            text = self.input_field.text().strip()
            if not text:
                self._cancel_editing()
                return

            new_value = int(text)

            # Range validation
            if new_value < self._min_value or new_value > self._max_value:
                self._show_validation_error(
                    f"Numer sekwencji musi być między {self._min_value} a {self._max_value}"
                )
                return

            # Custom validation
            if self._validation_callback:
                is_valid, error_msg = self._validation_callback(new_value, self._value)
                if not is_valid:
                    self._show_validation_error(error_msg)
                    return

            # Duplicate check
            if self._duplicate_check_callback and new_value != self._value:
                if self._duplicate_check_callback(new_value):
                    self._show_validation_error(
                        f"Numer sekwencji {new_value} już istnieje"
                    )
                    return

            # Value is valid
            if new_value != self._value:
                self._value = new_value
                self.sequence_changed.emit(self._value)

            self._update_display()
        except (ValueError, RuntimeError):
            # ValueError for invalid input, RuntimeError for deleted widgets
            try:
                self._show_validation_error("Wprowadź poprawny numer")
            except RuntimeError:
                # Widget was deleted, just reset state
                self._editing = False

    def _show_validation_error(self, message: str):
        """Show validation error and keep editing mode."""
        self.input_field.setToolTip(message)
        self._set_input_style("error")
        self.input_field.selectAll()  # Select all text for easy correction

    def _cancel_editing(self):
        """Cancel editing with safety checks for widget deletion."""
        if self._editing:
            self._editing = False
            try:
                self.input_field.hide()
                self.display_label.show()
                self.input_field.setStyleSheet("")  # Reset style
                self.input_field.setToolTip("")
            except RuntimeError:
                # Widgets were deleted, just reset state
                pass

    def _update_display(self):
        """Update display with safety checks for widget deletion."""
        self._editing = False
        try:
            self.display_label.setText(f"#{self._value}")
            self.input_field.hide()
            self.display_label.show()
            self.input_field.setStyleSheet("")  # Reset style
            self.input_field.setToolTip("")
        except RuntimeError:
            # Widgets were deleted, just reset state
            pass

    def set_validation_callback(self, callback):
        self._validation_callback = callback

    def set_duplicate_check_callback(self, callback):
        """Set callback to check for duplicate sequence numbers."""
        self._duplicate_check_callback = callback

    def set_range(self, min_value: int, max_value: int):
        """Set valid range for sequence numbers."""
        self._min_value = min_value
        self._max_value = max_value

    def get_value(self) -> int:
        return self._value

    def set_value(self, value: int):
        """Set value programmatically."""
        self._value = value
        self.display_label.setText(f"#{self._value}")
        if self._editing:
            self.input_field.setText(str(value))


class CabinetCard(QWidget):
    """Cabinet card widget for displaying individual cabinets."""

    sig_qty_changed = Signal(int, int)
    sig_edit = Signal(int)
    sig_duplicate = Signal(int)
    sig_delete = Signal(int)
    sig_selected = Signal(int)
    sig_sequence_changed = Signal(int, int)

    def __init__(self, card_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.card_data = card_data
        self.cabinet_id = card_data.get("id", 0)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        # Use responsive sizing instead of fixed size
        self.setMinimumWidth(CARD_MIN_W)  # guard against too-narrow columns
        self.setMinimumHeight(CARD_MIN_H)  # keep your baseline height
        self.setSizePolicy(
            QSizePolicy.Preferred,  # width can adjust within row
            QSizePolicy.Minimum,
        )  # height grows with wrapped content
        # Remove inline styles and let the main theme handle styling
        self.setObjectName("cabinetCard")  # Set object name for CSS targeting

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING
        )
        main_layout.setSpacing(8)

        # Header with sequence and actions
        header_layout = QHBoxLayout()

        self.sequence_input = SequenceNumberInput(self.card_data.get("sequence", 1))
        self.sequence_input.sequence_changed.connect(self._on_sequence_changed)
        header_layout.addWidget(self.sequence_input)

        header_layout.addStretch()

        # Action menu
        self.menu_btn = QToolButton()
        self.menu_btn.setText("⋮")
        self.menu_btn.setPopupMode(QToolButton.InstantPopup)
        self._setup_menu()
        header_layout.addWidget(self.menu_btn)

        main_layout.addLayout(header_layout)

        # Cabinet name
        name = self.card_data.get("name", "Niestandardowy")
        self.name_label = QLabel(name)
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        self.name_label.setWordWrap(True)
        main_layout.addWidget(self.name_label)

        # Colors section
        colors_layout = QHBoxLayout()
        colors_layout.addWidget(QLabel("Korpus:"))
        self.body_color_chip = ColorChip(
            self.card_data.get("body_color", "#ffffff"), "Korpus"
        )
        colors_layout.addWidget(self.body_color_chip)

        colors_layout.addSpacing(10)
        colors_layout.addWidget(QLabel("Front:"))
        self.front_color_chip = ColorChip(
            self.card_data.get("front_color", "#ffffff"), "Front"
        )
        colors_layout.addWidget(self.front_color_chip)
        colors_layout.addStretch()

        main_layout.addLayout(colors_layout)

        # Quantity section
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Ilość:"))

        self.quantity_stepper = QuantityStepper(self.card_data.get("quantity", 1))
        self.quantity_stepper.value_changed.connect(self._on_quantity_changed)
        qty_layout.addWidget(self.quantity_stepper)
        qty_layout.addStretch()

        main_layout.addLayout(qty_layout)
        main_layout.addStretch()

    def _setup_menu(self):
        menu = QMenu(self)

        edit_action = QAction("Edytuj", self)
        edit_action.triggered.connect(lambda: self.sig_edit.emit(self.cabinet_id))
        menu.addAction(edit_action)

        duplicate_action = QAction("Duplikuj", self)
        duplicate_action.triggered.connect(
            lambda: self.sig_duplicate.emit(self.cabinet_id)
        )
        menu.addAction(duplicate_action)

        menu.addSeparator()

        delete_action = QAction("Usuń", self)
        delete_action.triggered.connect(lambda: self.sig_delete.emit(self.cabinet_id))
        menu.addAction(delete_action)

        self.menu_btn.setMenu(menu)

    def _connect_signals(self):
        pass

    def _on_quantity_changed(self, new_quantity: int):
        self.card_data["quantity"] = new_quantity
        self.sig_qty_changed.emit(self.cabinet_id, new_quantity)

    def _on_sequence_changed(self, new_sequence: int):
        self.card_data["sequence"] = new_sequence
        self.sig_sequence_changed.emit(self.cabinet_id, new_sequence)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.sig_selected.emit(self.cabinet_id)

    def sizeHint(self):
        """Provide target size hint for consistent appearance while allowing flexibility."""
        # Aim for CARD_WIDTH, but let layout compress/expand if needed
        if hasattr(self, "layout") and self.layout():
            h = self.layout().sizeHint().height() + 2 * CARD_PADDING
        else:
            h = CARD_MIN_H
        return QSize(CARD_WIDTH, max(CARD_MIN_H, h))

    def is_card_selected(self):
        """Safe stub for selection compatibility."""
        return False

    def set_selected(self, value: bool):
        """Safe stub for selection compatibility."""
        pass


class HeaderBar(QWidget):
    """
    Header bar widget displaying project information and actions.

    Layout:
    - Left: Project title (h2) + metadata row (Order, Typ, Created)
    - Right: Export and Print buttons with proper tooltips
    """

    sig_export = Signal()
    sig_print = Signal()
    sig_client = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_name = ""
        self.order_number = ""
        self.kitchen_type = ""
        self.created_date = ""
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Set up the header bar UI layout."""
        self.setFixedHeight(HEADER_HEIGHT)
        self.setProperty("class", "header-bar")

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # Left section: Project info
        self._create_info_section(layout)

        # Stretch to push buttons to right
        layout.addStretch()

        # Right section: Action buttons
        self._create_action_buttons(layout)

    def _create_info_section(self, parent_layout: QHBoxLayout):
        """Create the project information section."""
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        # Project title (h2 style)
        self.title_label = QLabel("Projekt")
        self.title_label.setProperty("class", "project-title")
        font = self.title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        info_layout.addWidget(self.title_label)

        # Metadata row
        metadata_layout = QHBoxLayout()
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(16)

        # Order number
        self.order_label = QLabel("Order: -")
        self.order_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.order_label)

        # Kitchen type
        self.type_label = QLabel("Typ: -")
        self.type_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.type_label)

        # Created date
        self.date_label = QLabel("Utworzono: -")
        self.date_label.setProperty("class", "metadata")
        metadata_layout.addWidget(self.date_label)

        # Add stretch to metadata
        metadata_layout.addStretch()

        info_layout.addLayout(metadata_layout)
        parent_layout.addLayout(info_layout)

    def _create_action_buttons(self, parent_layout: QHBoxLayout):
        """Create the action buttons section."""
        # Client button
        self.client_btn = QPushButton("Klient")
        self.client_btn.setIcon(get_icon("info"))
        self.client_btn.setIconSize(ICON_SIZE)
        self.client_btn.setProperty("class", "secondary")
        self.client_btn.setToolTip("Informacje o kliencie")
        self.client_btn.clicked.connect(self.sig_client.emit)
        parent_layout.addWidget(self.client_btn)

        # Export button
        self.export_btn = QPushButton("Eksport")
        self.export_btn.setIcon(get_icon("export"))
        self.export_btn.setIconSize(ICON_SIZE)
        self.export_btn.setProperty("class", "secondary")
        self.export_btn.setToolTip("Eksportuj projekt")
        self.export_btn.clicked.connect(self.sig_export.emit)
        parent_layout.addWidget(self.export_btn)

        # Print button
        self.print_btn = QPushButton("Drukuj")
        self.print_btn.setIcon(get_icon("print"))
        self.print_btn.setIconSize(ICON_SIZE)
        self.print_btn.setProperty("class", "secondary")
        self.print_btn.setToolTip("Drukuj projekt")
        self.print_btn.clicked.connect(self.sig_print.emit)
        parent_layout.addWidget(self.print_btn)

    def _apply_styling(self):
        """Apply styling to the header bar."""
        self.setStyleSheet("""
            HeaderBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
            }
            QLabel[class="project-title"] {
                color: #1a202c;
                font-weight: 600;
            }
            QLabel[class="metadata"] {
                color: #64748b;
                font-size: 12px;
            }
        """)

    def set_project_info(
        self,
        name: str,
        order_number: str = "",
        kitchen_type: str = "",
        created_date: str = "",
    ):
        """Update project information display."""
        self.project_name = name
        self.order_number = order_number
        self.kitchen_type = kitchen_type
        self.created_date = created_date

        # Update labels
        title = f"{name}"
        if order_number:
            title += f" - #{order_number}"
        self.title_label.setText(title)

        self.order_label.setText(f"Order: {order_number or '-'}")
        self.type_label.setText(f"Typ: {kitchen_type or '-'}")
        self.date_label.setText(f"Utworzono: {created_date or '-'}")


class Toolbar(QWidget):
    """
    Modern toolbar widget with view mode controls and actions.

    Layout:
    - Left: Add buttons ("Dodaj z listy", "Dodaj niestandardową")
    - Middle: Sort button
    - Right: View mode toggle chips ("Karty", "Tabela")
    """

    sig_add_from_catalog = Signal()
    sig_add_custom = Signal()
    sig_view_mode_changed = Signal(str)
    sig_sort_by_sequence = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_view_mode = VIEW_MODE_CARDS
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Set up the toolbar UI layout."""
        self.setFixedHeight(TOOLBAR_HEIGHT)
        self.setProperty("class", "toolbar")

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        # Left section: Add buttons
        self._create_add_buttons(layout)

        # Middle section: Sort button
        self._create_sort_button(layout)

        # Add stretch before view toggle to push it to the right
        layout.addStretch()

        # Right section: View mode toggle
        self._create_view_toggle(layout)

    def _create_add_buttons(self, parent_layout: QHBoxLayout):
        """Create the add buttons section."""
        # Add from catalog button
        self.add_catalog_btn = QPushButton("Katalog")
        self.add_catalog_btn.setIcon(get_icon("catalog"))
        self.add_catalog_btn.setIconSize(ICON_SIZE)
        self.add_catalog_btn.setProperty("class", "primary-btn")
        self.add_catalog_btn.setToolTip("Dodaj z katalogu")
        self.add_catalog_btn.clicked.connect(self.sig_add_from_catalog.emit)
        parent_layout.addWidget(self.add_catalog_btn)

        # Add custom button
        self.add_custom_btn = QPushButton("Niestandardowa")
        self.add_custom_btn.setIcon(get_icon("add"))
        self.add_custom_btn.setIconSize(ICON_SIZE)
        self.add_custom_btn.setProperty("class", "secondary")
        self.add_custom_btn.setToolTip("Dodaj niestandardową szafkę")
        self.add_custom_btn.clicked.connect(self.sig_add_custom.emit)
        parent_layout.addWidget(self.add_custom_btn)

    def _create_sort_button(self, parent_layout: QHBoxLayout):
        """Create the sort button."""
        self.sort_btn = QPushButton("Sortuj")
        self.sort_btn.setIcon(get_icon("filter"))  # Using filter icon for sort
        self.sort_btn.setIconSize(ICON_SIZE)
        self.sort_btn.setProperty("class", "secondary")
        self.sort_btn.setToolTip("Sortuj według sekwencji")
        self.sort_btn.clicked.connect(self.sig_sort_by_sequence.emit)
        parent_layout.addWidget(self.sort_btn)

    def _create_view_toggle(self, parent_layout: QHBoxLayout):
        """Create the view mode toggle buttons."""
        # Container for toggle buttons
        toggle_widget = QWidget()
        toggle_layout = QHBoxLayout(toggle_widget)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(2)

        # Cards view button
        self.cards_btn = QPushButton("Karty")
        self.cards_btn.setIcon(get_icon("dashboard"))
        self.cards_btn.setIconSize(ICON_SIZE)
        self.cards_btn.setProperty("class", "toggle-btn")
        self.cards_btn.setCheckable(True)
        self.cards_btn.setChecked(True)
        self.cards_btn.setToolTip("Widok kart")
        self.cards_btn.clicked.connect(lambda: self._set_view_mode(VIEW_MODE_CARDS))
        toggle_layout.addWidget(self.cards_btn)

        # Table view button
        self.table_btn = QPushButton("Tabela")
        self.table_btn.setIcon(get_icon("table"))  # Using table icon (mapped to menu)
        self.table_btn.setIconSize(ICON_SIZE)
        self.table_btn.setProperty("class", "toggle-btn")
        self.table_btn.setCheckable(True)
        self.table_btn.setToolTip("Widok tabeli")
        self.table_btn.clicked.connect(lambda: self._set_view_mode(VIEW_MODE_TABLE))
        toggle_layout.addWidget(self.table_btn)

        parent_layout.addWidget(toggle_widget)

    def _set_view_mode(self, mode: str):
        """Set the current view mode."""
        self.current_view_mode = mode

        # Update button states
        self.cards_btn.setChecked(mode == VIEW_MODE_CARDS)
        self.table_btn.setChecked(mode == VIEW_MODE_TABLE)

        # Emit signal
        self.sig_view_mode_changed.emit(mode)

    def _apply_styling(self):
        """Apply styling to the toolbar."""
        self.setStyleSheet("""
            Toolbar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
            QPushButton[class="primary-btn"] {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton[class="primary-btn"]:hover {
                background-color: #106ebe;
            }
            QPushButton[class="toggle-btn"] {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 12px;
                color: #374151;
                min-width: 60px;
            }
            QPushButton[class="toggle-btn"]:checked {
                background-color: #0078d4;
                color: white;
                border-color: #0078d4;
            }
            QPushButton[class="toggle-btn"]:hover {
                background-color: #e5e7eb;
            }
            QPushButton[class="toggle-btn"]:checked:hover {
                background-color: #106ebe;
            }
        """)


class BannerManager(QWidget):
    """Banner manager for showing notifications."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.banners = []

    def show_success(self, message: str, timeout_ms: int = 2500):
        self._show_banner(message, "success", timeout_ms)

    def show_info(self, message: str, timeout_ms: int = 2500):
        self._show_banner(message, "info", timeout_ms)

    def show_warning(self, message: str, timeout_ms: int = 3500):
        self._show_banner(message, "warning", timeout_ms)

    def show_error(self, message: str, timeout_ms: int = 0):
        self._show_banner(message, "error", timeout_ms)

    def _show_banner(self, message: str, banner_type: str, timeout_ms: int):
        banner = QLabel(message)
        banner.setWordWrap(True)
        banner.setStyleSheet(f"""
            QLabel {{
                background-color: {"#d4edda" if banner_type == "success" else "#f8d7da" if banner_type == "error" else "#fff3cd"};
                border: 1px solid {"#c3e6cb" if banner_type == "success" else "#f5c6cb" if banner_type == "error" else "#ffeaa7"};
                color: {"#155724" if banner_type == "success" else "#721c24" if banner_type == "error" else "#856404"};
                padding: 8px 12px;
                border-radius: 4px;
                margin: 2px 0px;
            }}
        """)

        self.layout.addWidget(banner)
        self.banners.append(banner)

        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, lambda: self._remove_banner(banner))

    def _remove_banner(self, banner):
        if banner in self.banners:
            self.banners.remove(banner)
            banner.setParent(None)

    def clear_all(self):
        for banner in self.banners[:]:
            self._remove_banner(banner)


class CabinetTableModel(QAbstractTableModel):
    """Table model for cabinet data."""

    cabinet_data_changed = Signal(int, str, object)

    def __init__(self, cabinets: List[ProjectCabinet], parent=None):
        super().__init__(parent)
        self.cabinets = cabinets or []
        self.columns = ["Lp.", "Typ", "Korpus", "Front", "Uchwyt", "Ilość"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.cabinets)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.cabinets):
            return None

        cabinet = self.cabinets[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return cabinet.sequence_number
            elif col == 1:
                return (
                    cabinet.cabinet_type.nazwa
                    if cabinet.cabinet_type
                    else "Niestandardowy"
                )
            elif col == 2:
                return cabinet.body_color or "Nie określono"
            elif col == 3:
                return cabinet.front_color or "Nie określono"
            elif col == 4:
                return cabinet.handle_type or "Nie określono"
            elif col == 5:
                return cabinet.quantity

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        return None

    def set_rows(self, cabinets: List[ProjectCabinet]):
        self.beginResetModel()
        self.cabinets = cabinets
        self.endResetModel()


class CabinetProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting cabinets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_filter = ""

    def set_search_filter(self, text: str):
        self._search_filter = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._search_filter:
            return True

        model = self.sourceModel()
        for col in range(model.columnCount()):
            index = model.index(source_row, col, source_parent)
            data = model.data(index, Qt.DisplayRole)
            if data and self._search_filter in str(data).lower():
                return True

        return False


# State management
class UiState:
    """UI state persistence."""

    def __init__(self):
        self.settings = QSettings()

    def get_view_mode(self, default="cards"):
        return self.settings.value("project_details/view_mode", default)

    def set_view_mode(self, mode):
        self.settings.setValue("project_details/view_mode", mode)


class ResponsiveFlowLayout(QLayout):
    """
    Responsive flow layout that wraps widgets based on available width.
    Based on Qt's FlowLayout example for smooth responsive behavior.
    """

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self._item_list = []
        self._spacing = spacing

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        m = self.contentsMargins()
        w = CARD_WIDTH
        h = 0
        for it in self._item_list:
            wid = it.widget()
            if wid and wid.isVisible():
                sz = it.minimumSize()
                w = max(w, sz.width())
                h = max(h, sz.height())
        return QSize(w + m.left() + m.right(), h + m.top() + m.bottom())

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        line_h = 0
        sp = self.spacing()
        right = rect.x() + rect.width() - m.right()

        for item in self._item_list:
            w = item.widget()
            if not w or not w.isVisible():
                continue

            sz = item.sizeHint()
            next_x = x + sz.width()
            if next_x > right and line_h > 0:
                # wrap
                x = rect.x() + m.left()
                y = y + line_h + sp
                next_x = x + sz.width()
                line_h = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), sz))

            x = next_x + sp
            line_h = max(line_h, sz.height())

        total_h = (y + line_h + m.bottom()) - rect.y()
        return total_h

    def spacing(self):
        if self._spacing >= 0:
            return self._spacing
        else:
            return (
                self.parent()
                .style()
                .layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
                )
            )

    def clear_layout(self):
        """Remove all items from layout without deleting widgets"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def addCard(self, card_widget):
        """Add a card widget to the layout."""
        self.addWidget(card_widget)

    def clear_cards(self):
        """Clear all cards from layout and delete them."""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                child.widget().deleteLater()

    def clear_layout_only(self):
        """Clear layout without deleting widgets."""
        # Store widgets temporarily to avoid Qt geometry issues
        widgets = []
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)  # Remove from layout without deleting
                widgets.append(widget)

        # Process events to ensure layout is cleared
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()
        return widgets

    def activate(self):
        """Force layout to recalculate."""
        try:
            super().activate()
        except:
            # If activate() doesn't exist or fails, do manual refresh
            self.update()


class CardGridFlowLayout(QVBoxLayout):
    """Custom layout that arranges cards in rows, wrapping based on available width."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(CARD_GRID_SPACING)  # Vertical spacing between rows
        self.rows = []
        self.cards = []

    def addCard(self, card_widget):
        """Add a card to the flow layout, creating new rows as needed."""
        self.cards.append(card_widget)

        # Card dimensions for layout calculation
        CARD_SPACING = CARD_GRID_SPACING  # Horizontal spacing between cards

        # Check if we need a new row
        if not self.rows:
            # Create first row
            row_layout = QHBoxLayout()
            row_layout.setSpacing(CARD_SPACING)
            row_layout.addWidget(card_widget)
            row_layout.addStretch()

            row_widget = QWidget()
            row_widget.setLayout(row_layout)
            self.addWidget(row_widget)
            self.rows.append(row_layout)
        else:
            # Try to add to last row, but check if it's still valid
            last_row = self.rows[-1]
            try:
                parent_width = (
                    self.parentWidget().width() if self.parentWidget() else 800
                )

                # Calculate if card fits in current row
                cards_in_row = last_row.count() - 1  # Subtract stretch
                needed_width = (
                    cards_in_row + 1
                ) * CARD_MIN_W + cards_in_row * CARD_SPACING

                if needed_width <= parent_width - 40:  # 40px margin
                    # Remove stretch, add card, add stretch back
                    stretch_item = last_row.takeAt(last_row.count() - 1)
                    last_row.addWidget(card_widget)
                    last_row.addItem(stretch_item)
                else:
                    # Create new row
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(CARD_SPACING)
                    row_layout.addWidget(card_widget)
                    row_layout.addStretch()

                    row_widget = QWidget()
                    row_widget.setLayout(row_layout)
                    self.addWidget(row_widget)
                    self.rows.append(row_layout)

            except RuntimeError:
                # Last row was deleted, create a new row
                row_layout = QHBoxLayout()
                row_layout.setSpacing(CARD_SPACING)
                row_layout.addWidget(card_widget)
                row_layout.addStretch()

                row_widget = QWidget()
                row_widget.setLayout(row_layout)
                self.addWidget(row_widget)
                self.rows.append(row_layout)

    def clear_cards(self):
        """Remove all cards from the layout."""
        self.cards.clear()

        # Remove all row widgets
        for i in reversed(range(self.count())):
            item = self.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        self.rows.clear()

        # Process deletion events immediately
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

    def clear_layout_only(self):
        """Remove cards from layout without deleting them."""
        # Clear the cards list to reset state
        self.cards.clear()

        # Remove cards from rows but don't delete the card widgets
        for row_layout in self.rows:
            while row_layout.count() > 0:
                item = row_layout.takeAt(0)
                # Don't delete the widget, just remove from layout

        # Remove all row widgets from the main layout
        for i in reversed(range(self.count())):
            item = self.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Clear rows list - the layouts will be deleted with their parent widgets
        self.rows.clear()

        # Process any pending deletion events
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

    def activate(self):
        """Force layout to recalculate."""
        try:
            super().activate()
        except:
            # If activate() doesn't exist or fails, do manual refresh
            self.update()

    def filter_cards(self, search_text):
        """No-op: All cabinet cards should always be visible."""
        pass

    def addStretch(self):
        """Add stretch to push cards to top."""
        super().addStretch()


class CardGrid(QWidget):
    """
    Responsive grid widget that displays cabinet cards in a shopping-cart style layout.
    Features:
    - Flow layout that wraps cards to new rows based on width
    - Search filtering with smooth animations
    - Empty state when no cabinets
    - Selection management for bulk operations
    """

    # Signals
    sig_qty_changed = Signal(int, int)  # cabinet_id, new_quantity
    sig_edit = Signal(int)  # Cabinet edit request
    sig_duplicate = Signal(int)  # Cabinet duplicate request
    sig_delete = Signal(int)  # Cabinet delete request
    sig_card_selected = Signal(int)  # cabinet_id selection
    sig_sequence_changed = Signal(int, int)  # cabinet_id, new_sequence_number
    sig_add_from_catalog = Signal()  # Add from catalog request (from empty state)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cabinet_cards = {}  # cabinet_id -> CabinetCard
        self._search_filter = ""
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)

        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # Flow layout for cards
        self.flow_layout = CardGridFlowLayout(self.content_widget)
        self.flow_layout.addStretch()  # Push cards to top

        # Empty state widget
        self.empty_state = EmptyStateWidget()
        self.empty_state.add_cabinet_requested.connect(self.sig_add_from_catalog.emit)

        # Initially show empty state
        self.scroll_area.setWidget(self.empty_state)
        main_layout.addWidget(self.scroll_area)

    def add_card(self, cabinet_data):
        """Add a new cabinet card to the grid."""
        cabinet_id = cabinet_data["id"]

        # Don't add duplicates
        if cabinet_id in self._cabinet_cards:
            return

        # Create card widget
        card = CabinetCard(cabinet_data)

        # Connect signals
        card.sig_qty_changed.connect(self.sig_qty_changed)
        card.sig_edit.connect(self.sig_edit)
        card.sig_duplicate.connect(self.sig_duplicate)
        card.sig_delete.connect(self.sig_delete)
        card.sig_selected.connect(self.sig_card_selected)
        card.sig_sequence_changed.connect(self.sig_sequence_changed)

        # Store reference
        self._cabinet_cards[cabinet_id] = card

        # Set up sequence validation for the card
        self._setup_sequence_validation(card)

        # Switch to card view if this is first card
        if len(self._cabinet_cards) == 1:
            self._switch_to_card_view()

        # Add to layout
        self.flow_layout.addCard(card)

        # No search filtering - all cards should always be visible

    def _setup_sequence_validation(self, card: CabinetCard):
        """Set up sequence validation for a cabinet card."""
        if hasattr(card, "sequence_input"):
            # Set duplicate check callback that ignores the edited card
            card.sequence_input.set_duplicate_check_callback(
                lambda seq, _id=card.cabinet_id: any(
                    (c.card_data.get("sequence", 0) == seq) and (c.cabinet_id != _id)
                    for c in self._cabinet_cards.values()
                )
            )

            # Set reasonable range
            card.sequence_input.set_range(1, 999)

            # Connect to auto-sort when sequence changes
            card.sig_sequence_changed.connect(self._on_sequence_changed_auto_sort)

    def _check_sequence_duplicate(self, sequence_number: int) -> bool:
        """Check if sequence number is already used by another cabinet."""
        for card in self._cabinet_cards.values():
            if card.card_data.get("sequence", 0) == sequence_number:
                return True
        return False

    def _on_sequence_changed_auto_sort(self, cabinet_id: int, new_sequence: int):
        """Handle sequence change with automatic sorting."""
        # Update the card data
        if cabinet_id in self._cabinet_cards:
            self._cabinet_cards[cabinet_id].card_data["sequence"] = new_sequence

        # Emit the original signal for other handlers
        self.sig_sequence_changed.emit(cabinet_id, new_sequence)

        # Auto-sort after a short delay to allow for multiple rapid changes
        QTimer.singleShot(500, self.sort_cards_by_sequence)

    def get_used_sequence_numbers(self) -> list:
        """Get list of all currently used sequence numbers."""
        sequences = []
        for card in self._cabinet_cards.values():
            sequence = card.card_data.get("sequence", 0)
            if sequence > 0:
                sequences.append(sequence)
        return sorted(sequences)

    def get_next_available_sequence(self) -> int:
        """Get the next available sequence number."""
        used_sequences = self.get_used_sequence_numbers()
        if not used_sequences:
            return 1

        # Find first gap in sequence
        for i, seq in enumerate(used_sequences):
            if i + 1 != seq:
                return i + 1

        # No gaps, return next number
        return max(used_sequences) + 1

    def add_cabinet_card(self, cabinet_data):
        """Alias for add_card method."""
        self.add_card(cabinet_data)

    def clear_cards(self):
        """Remove all cabinet cards from the grid."""
        for card in self._cabinet_cards.values():
            card.setParent(None)
            card.deleteLater()

        self._cabinet_cards.clear()
        self.flow_layout.clear_cards()
        self._switch_to_empty_state()

    def remove_cabinet_card(self, cabinet_id):
        """Remove a cabinet card from the grid."""
        if cabinet_id not in self._cabinet_cards:
            return

        card = self._cabinet_cards[cabinet_id]
        card.setParent(None)  # Remove from layout
        card.deleteLater()
        del self._cabinet_cards[cabinet_id]

        # Show empty state if no cards left
        if not self._cabinet_cards:
            self._switch_to_empty_state()

    def update_cabinet_quantity(self, cabinet_id, quantity):
        """Update the quantity display for a specific cabinet card."""
        if cabinet_id in self._cabinet_cards:
            card = self._cabinet_cards[cabinet_id]
            card.card_data["quantity"] = quantity
            if hasattr(card, "quantity_stepper"):
                card.quantity_stepper.set_value(quantity)

    def sort_cards_by_sequence(self):
        """Sort cabinet cards by sequence number with smooth transition."""
        try:
            if not self._cabinet_cards:
                return

            # Check if widgets are still valid before sorting
            valid_cards = {}
            for cabinet_id, card in self._cabinet_cards.items():
                try:
                    # Test if the widget is still valid by accessing a property
                    if (
                        card and not card.isHidden()
                    ):  # This will raise if widget is deleted
                        valid_cards[cabinet_id] = card
                except RuntimeError:
                    # Widget has been deleted, skip it
                    continue

            if not valid_cards:
                return

            # Get all valid cards and sort by sequence
            sorted_cards = sorted(
                valid_cards.items(),
                key=lambda item: item[1].card_data.get("sequence", 999),
            )

            # Remove all cards from layout
            if hasattr(self, "flow_layout") and self.flow_layout:
                self.flow_layout.clear_layout_only()

            # Re-add cards in sorted order
            for cabinet_id, card in sorted_cards:
                if hasattr(self, "flow_layout") and self.flow_layout and card:
                    try:
                        self.flow_layout.addCard(card)
                    except RuntimeError:
                        # Widget became invalid during operation
                        continue

        except Exception as e:
            logger.error(f"Error during card sorting: {e}")
            # Don't re-raise to prevent application crash

    def set_search_filter(self, search_text):
        """No-op: Search functionality removed - all cards always visible."""
        pass

    def _apply_search_filter(self):
        """No-op: All cards should always be visible."""
        pass

    def filter_cards(self, search_text):
        """No-op: All cabinet cards should always be visible."""
        pass

    def _switch_to_card_view(self):
        """Switch from empty state to card grid view."""
        try:
            if hasattr(self, "content_widget") and self.content_widget:
                # Check if widgets are still valid
                if not self.content_widget.isHidden():  # Test widget validity
                    self.scroll_area.setWidget(self.content_widget)
        except RuntimeError as e:
            logger.warning(
                f"Error switching to card view - widget no longer valid: {e}"
            )

    def _switch_to_empty_state(self):
        """Switch from card grid to empty state view."""
        try:
            if hasattr(self, "empty_state") and self.empty_state:
                # Check if widgets are still valid
                if not self.empty_state.isHidden():  # Test widget validity
                    self.scroll_area.setWidget(self.empty_state)
        except RuntimeError as e:
            logger.warning(
                f"Error switching to empty state - widget no longer valid: {e}"
            )

    def clear_selection(self):
        """Clear selection from all cards."""
        for card in self._cabinet_cards.values():
            card.set_selected(False)

    def get_selected_cabinet_ids(self):
        """Return list of currently selected cabinet IDs."""
        return [
            cabinet_id
            for cabinet_id, card in self._cabinet_cards.items()
            if card.is_card_selected()
        ]

    def get_total_cabinet_count(self):
        """Return total number of cabinet cards."""
        return len(self._cabinet_cards)


class EmptyStateWidget(QWidget):
    """Widget shown when no cabinets are added to project."""

    # Signal for when the add button is clicked
    add_cabinet_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Icon placeholder
        icon_label = QLabel("📋")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #94a3b8;")

        # Title
        title = QLabel("Brak elementów")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Medium)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #475569; margin-bottom: 8px;")

        # Subtitle
        subtitle = QLabel("Dodaj szafki aby rozpocząć planowanie projektu")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")

        # CTA Button
        add_button = QPushButton("Dodaj z katalogu")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        add_button.clicked.connect(self.add_cabinet_requested.emit)

        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(add_button)


# Main Dialog
class ProjectDetailsView(QDialog):
    """
    Main project details dialog - UI only.

    This dialog provides the user interface for viewing and editing project details.
    It delegates all business logic to controllers and focuses purely on UI concerns.

    Key responsibilities:
    - Layout and widget management
    - UI state persistence (splitter positions, etc.)
    - Event delegation to controllers
    - Basic dialog lifecycle management
    """

    # Signals for controller communication (updated per requirements)
    sig_view_mode_changed = Signal(str)  # 'cards' or 'table'
    sig_add_from_catalog = Signal()
    sig_add_custom_cabinet = Signal()  # Renamed for clarity
    sig_add_custom = Signal()  # Compatibility alias for controller
    sig_export = Signal()
    sig_print = Signal()
    sig_client_save = Signal(
        dict
    )  # {"client_name":..., "client_address":..., "client_phone":..., "client_email":...}
    sig_client_open_requested = Signal()  # New signal for client button

    # Cabinet operation signals (relayed from card widgets)
    sig_card_qty_changed = Signal(int, int)  # cabinet_id, qty
    sig_cabinet_qty_changed = Signal(int, int)  # Compatibility alias
    sig_card_edit = Signal(int)  # cabinet_id
    sig_cabinet_edit = Signal(int)  # Compatibility alias
    sig_card_duplicate = Signal(int)  # cabinet_id
    sig_cabinet_duplicate = Signal(int)  # Compatibility alias
    sig_card_delete = Signal(int)  # cabinet_id
    sig_cabinet_delete = Signal(int)  # Compatibility alias
    sig_cabinet_selected = Signal(int)  # cabinet_id (for table compatibility)
    sig_card_quantity_changed = Signal(int, int)  # New required signal name
    sig_card_sequence_changed = Signal(int, int)  # cabinet_id, sequence_number
    sig_cabinet_sequence_changed = Signal(int, int)  # Compatibility alias

    def __init__(
        self, session: Session, project: Project, modal: bool = False, parent=None
    ):
        """
        Initialize the project details view.

        Args:
            session: Database session (required)
            project: Project object (required)
            modal: Whether dialog should be modal
            parent: Parent widget
        """
        super().__init__(parent)
        self.session = session  # Store session for integrated mode
        self.project = project  # Store project for integrated mode
        self.modal = modal
        self.controller = (
            None  # Will be set by controller.attach() if using separate controller
        )
        self._current_view_mode = VIEW_MODE_CARDS

        # Initialize UI state persistence
        self.ui_state = UiState()

        # Initialize services
        from src.services.project_service import ProjectService
        from src.services.report_generator import ReportGenerator

        self.project_service = ProjectService(self.session)
        self.report_generator = ReportGenerator(self.session)

        self._setup_ui()
        self._setup_connections()
        self._setup_styling()

        # Load initial data
        self._load_data()

    def _setup_ui(self) -> None:
        """Set up the dialog UI components."""
        self.setWindowTitle("Szczegóły projektu")

        # Calculate minimum size based on card width (same as main window)
        minimum_width = CARD_WIDTH + 100  # Card width + margins/scrollbar
        self.setMinimumSize(minimum_width, 600)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar
        self.header_bar = HeaderBar()
        self.header_bar.setFixedHeight(HEADER_HEIGHT)
        main_layout.addWidget(self.header_bar)

        # Toolbar
        self.toolbar = Toolbar()
        self.toolbar.setFixedHeight(TOOLBAR_HEIGHT)
        main_layout.addWidget(self.toolbar)

        # Main content area (no splitter - cabinet cards are the focus)
        self._create_central_area()
        main_layout.addWidget(self.central_widget)

        # Banner manager for notifications (moved to bottom)
        self.banner_manager = BannerManager()
        main_layout.addWidget(self.banner_manager)

        # Footer with dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Close).setText("Zamknij")
        main_layout.addWidget(self.button_box)

        # Initialize viewport tracking for responsive behavior after widgets are set up
        QTimer.singleShot(0, self._initialize_viewport_tracking)

    def _create_central_area(self) -> None:
        """Create the central stacked widget area with responsive card layout."""
        self.central_widget = QWidget()
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(*CONTENT_MARGINS)
        central_layout.setSpacing(0)

        # Stacked widget for different view modes
        self.stacked_widget = QStackedWidget()

        # Card view with responsive layout (like main window)
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.card_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Card container with ResponsiveFlowLayout for proper responsive behavior
        self.card_container = QWidget()
        self.card_layout = ResponsiveFlowLayout(
            self.card_container, margin=8, spacing=12
        )

        # ✅ Install the layout on the container so Qt manages geometry
        self.card_container.setLayout(self.card_layout)

        self.card_scroll.setWidget(self.card_container)
        self.stacked_widget.addWidget(self.card_scroll)

        # Empty state widget for when no cabinets exist
        self.empty_state = EmptyStateWidget()
        self.empty_state.add_cabinet_requested.connect(self._handle_add_from_catalog)

        # Keep the original card_grid for compatibility (hidden, but used for logic)
        self.card_grid = CardGrid()
        self.card_grid.hide()  # Hide but keep for signal connections

        # Table view placeholder - create a basic table view
        self.table_view = QTableView()
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 8px;
                font-weight: 500;
            }
        """)
        # Table model will be set up in _setup_models() after data loading
        self.stacked_widget.addWidget(self.table_view)

        central_layout.addWidget(self.stacked_widget)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Dialog button
        self.button_box.rejected.connect(self._on_close)

        # Header bar signals - call service handlers (they handle their own signals)
        self.header_bar.sig_export.connect(self._handle_export)
        self.header_bar.sig_print.connect(self._handle_print)
        self.header_bar.sig_client.connect(self._on_client_open_requested)

        # Toolbar signals - call service handlers (they handle their own signals)
        self.toolbar.sig_add_from_catalog.connect(self._handle_add_from_catalog)
        self.toolbar.sig_add_custom.connect(self._handle_add_custom)
        self.toolbar.sig_view_mode_changed.connect(self._on_view_mode_changed)
        self.toolbar.sig_sort_by_sequence.connect(self._on_sort_by_sequence)

        # Card grid signals - call service handlers then emit compatibility signals
        self.card_grid.sig_qty_changed.connect(
            lambda cabinet_id, qty: (
                self._handle_quantity_change(cabinet_id, qty),
                self._emit_quantity_signals(cabinet_id, qty),
            )
        )
        self.card_grid.sig_edit.connect(
            lambda cabinet_id: (
                self._handle_edit(cabinet_id),
                self._emit_edit_signals(cabinet_id),
            )
        )
        self.card_grid.sig_duplicate.connect(
            lambda cabinet_id: (
                self._handle_duplicate(cabinet_id),
                self._emit_duplicate_signals(cabinet_id),
            )
        )
        self.card_grid.sig_delete.connect(
            lambda cabinet_id: (
                self._handle_delete(cabinet_id),
                self._emit_delete_signals(cabinet_id),
            )
        )
        self.card_grid.sig_card_selected.connect(self.sig_cabinet_selected)
        self.card_grid.sig_sequence_changed.connect(
            lambda cabinet_id, seq: (
                self._handle_sequence_change(cabinet_id, seq),
                self._emit_sequence_signals(cabinet_id, seq),
            )
        )
        self.card_grid.sig_add_from_catalog.connect(self._handle_add_from_catalog)

    def _setup_styling(self) -> None:
        """Apply modern styling with the main application theme."""
        # Apply main application theme to the dialog only to avoid overriding fine-grained widget styles
        theme = get_theme(self.is_dark_mode)
        self.setStyleSheet(theme)

        # Set property classes for individual components for additional styling
        self.setProperty("class", "dialog")
        self.card_grid.setProperty("class", "card-grid")

    def _initialize_viewport_tracking(self):
        """Initialize viewport width tracking after widgets are properly set up."""
        if hasattr(self, "card_scroll"):
            self._last_viewport_width = self.card_scroll.viewport().width()
            # Trigger initial layout
            if hasattr(self, "card_layout"):
                self.card_layout.invalidate()

        # Restore saved view mode preference
        initial_mode = self.ui_state.get_view_mode("cards")
        self._current_view_mode = initial_mode
        self.toolbar._set_view_mode(initial_mode)  # Set UI button states
        self._on_view_mode_changed(initial_mode)  # Apply the mode

    def resizeEvent(self, event):
        """Handle window resize for responsive card layout and force layout geometry."""
        super().resizeEvent(event)

        # Debounced viewport tracking (for responsive wrapping)
        if (
            self.stacked_widget.currentIndex() == 0
            and hasattr(self, "_last_viewport_width")
            and hasattr(self, "card_scroll")
        ):
            current_width = self.card_scroll.viewport().width()

            # UX: Update on smaller threshold for narrow widths (better responsiveness)
            threshold = min(CARD_WIDTH // 3, 50)  # Smaller threshold for narrow windows
            if abs(current_width - self._last_viewport_width) > threshold:
                self._last_viewport_width = current_width
                # Debounce layout update to avoid excessive recomputation
                if hasattr(self, "_resize_timer"):
                    self._resize_timer.stop()
                else:
                    from PySide6.QtCore import QTimer

                    self._resize_timer = QTimer(self)
                    self._resize_timer.setSingleShot(True)
                    self._resize_timer.timeout.connect(self._on_resize_timeout)

                self._resize_timer.start(100)  # 100ms debounce
        elif not hasattr(self, "_last_viewport_width") and hasattr(self, "card_scroll"):
            self._last_viewport_width = self.card_scroll.viewport().width()

        # Ensure layout geometry matches the container after resize
        self._apply_resize_layout_update()

    def _apply_resize_layout_update(self):
        """Ensure flow layout geometry matches container after resizes."""
        if hasattr(self, "card_layout") and hasattr(self, "card_container"):
            try:
                QApplication.processEvents()  # Let resize complete

                # Force layout to match new container size
                container_rect = self.card_container.rect()
                if container_rect.width() > 0 and container_rect.height() > 0:
                    self.card_layout.setGeometry(container_rect)
                    try:
                        self.card_layout.activate()
                    except Exception:
                        pass  # Ignore activation errors
            except Exception as e:
                logger.warning(f"ResizeEvent layout update failed: {e}")

    def _on_resize_timeout(self):
        """Handle debounced resize event"""
        # Performance: invalidate layout to trigger re-layout in next event cycle
        if hasattr(self, "card_layout"):
            self.card_layout.invalidate()

    @property
    def is_dark_mode(self) -> bool:
        """Check if dark mode is enabled. Default to light mode for now."""
        # TODO: Get this from application settings
        return False

    def _load_data(self):
        """Load project and cabinet data."""
        if not self.project_service or not self.project:
            logger.warning("Cannot load data: missing project service or project")
            return

        try:
            # Load cabinets
            self.cabinets = self.project_service.list_cabinets(self.project.id)

            # Update header with full project information
            project_name = getattr(self.project, "name", "Projekt")
            order_number = getattr(self.project, "order_number", "")
            kitchen_type = getattr(self.project, "kitchen_type", "")

            # Format created date if available
            created_date = ""
            if hasattr(self.project, "created_at") and self.project.created_at:
                created_date = self.project.created_at.strftime("%Y-%m-%d")

            self.header_bar.set_project_info(
                name=project_name,
                order_number=order_number,
                kitchen_type=kitchen_type,
                created_date=created_date,
            )
            self.setWindowTitle(f"Szczegóły projektu: {project_name}")

            # Setup models
            self._setup_models()

            # Update views
            self._update_card_view()

            # Toggle empty state based on cabinet count
            self._toggle_empty_state()

        except Exception as e:
            logger.error(f"Error loading project data: {e}")
            self.banner_manager.show_error(f"Błąd podczas ładowania danych: {e}")

    def _on_close(self) -> None:
        """Handle dialog close."""
        if self.modal:
            self.reject()
        else:
            self.close()

    def _on_export(self, format_type: str = None) -> None:
        """Handle export request."""
        self.sig_export.emit()

    def _on_print(self) -> None:
        """Handle print request."""
        self.sig_print.emit()

    def _on_add_from_catalog(self) -> None:
        """Handle add from catalog request."""
        self.sig_add_from_catalog.emit()

    def _on_add_custom(self) -> None:
        """Handle add custom cabinet request."""
        self.sig_add_custom_cabinet.emit()
        self.sig_add_custom.emit()  # Compatibility for controller

    def _on_client_open_requested(self) -> None:
        """Handle client button click."""
        self.sig_client_open_requested.emit()

    def _emit_quantity_signals(self, cabinet_id: int, quantity: int) -> None:
        """Helper to emit all quantity change signals for compatibility."""
        self.sig_card_qty_changed.emit(cabinet_id, quantity)
        self.sig_cabinet_qty_changed.emit(cabinet_id, quantity)
        self.sig_card_quantity_changed.emit(cabinet_id, quantity)

    def _emit_edit_signals(self, cabinet_id: int) -> None:
        """Helper to emit both edit signals for compatibility."""
        self.sig_card_edit.emit(cabinet_id)
        self.sig_cabinet_edit.emit(cabinet_id)

    def _emit_duplicate_signals(self, cabinet_id: int) -> None:
        """Helper to emit both duplicate signals for compatibility."""
        self.sig_card_duplicate.emit(cabinet_id)
        self.sig_cabinet_duplicate.emit(cabinet_id)

    def _emit_delete_signals(self, cabinet_id: int) -> None:
        """Helper to emit both delete signals for compatibility."""
        self.sig_card_delete.emit(cabinet_id)
        self.sig_cabinet_delete.emit(cabinet_id)

    def _emit_sequence_signals(self, cabinet_id: int, sequence_number: int) -> None:
        """Helper to emit sequence change signals for compatibility and handle auto-sorting."""
        self.sig_card_sequence_changed.emit(cabinet_id, sequence_number)

        # Update the cabinet data in memory if we have it
        if hasattr(self, "cabinets") and self.cabinets:
            for cabinet in self.cabinets:
                if cabinet.id == cabinet_id:
                    cabinet.sequence_number = sequence_number
                    break

        # Auto-sort after sequence change (with small delay for multiple rapid changes)
        QTimer.singleShot(300, self._auto_sort_after_sequence_change)

    def _auto_sort_after_sequence_change(self) -> None:
        """Automatically sort cards after sequence number changes."""
        try:
            # Use the existing sort method
            self._on_sort_by_sequence()
        except Exception as e:
            logger.error(f"Error during auto-sort after sequence change: {e}")

    def _on_view_mode_changed(self, mode: str) -> None:
        """Handle view mode change between cards and table."""
        self._current_view_mode = mode

        # Persist view mode preference
        self.ui_state.set_view_mode(mode)

        if mode == VIEW_MODE_CARDS:
            self.stacked_widget.setCurrentWidget(self.card_scroll)
        elif mode == VIEW_MODE_TABLE:
            self.stacked_widget.setCurrentWidget(self.table_view)
            # Sync table with card data
            self._sync_table_with_cards()

        self.sig_view_mode_changed.emit(mode)

    def _reorder_visible_cards_by_sequence(self) -> None:
        """Reorder existing cards in the layout by sequence without recreating them."""
        try:
            # Collect existing CabinetCard widgets from ResponsiveFlowLayout
            existing_cards = []

            # Extract cards from the ResponsiveFlowLayout
            for i in range(self.card_layout.count()):
                item = self.card_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, "card_data"):
                        existing_cards.append(widget)

            # If no cards found, just do a full refresh
            if not existing_cards:
                self._update_card_view()
                return

            # Sort cards by sequence number (default to 999 for missing sequences)
            existing_cards.sort(key=lambda card: card.card_data.get("sequence", 999))

            # Clear layout without deleting widgets
            self.card_layout.clear_layout_only()

            # Re-add widgets in sorted order
            for card in existing_cards:
                self.card_layout.addWidget(card)

            # 🔧 Force comprehensive layout calculation (same as initial positioning)
            self._force_initial_layout_calculation()

        except Exception as e:
            logger.warning(f"Card reordering failed: {e}")
            # Fallback to full refresh if reordering fails
            self._update_card_view()

    def _on_sort_by_sequence(self) -> None:
        """Sort cabinet cards by sequence number."""
        try:
            # Sort the cabinets list by sequence number
            if hasattr(self, "cabinets") and self.cabinets:
                self.cabinets.sort(key=lambda c: c.sequence_number)

                # Instead of full refresh, just reorder existing cards
                self._reorder_visible_cards_by_sequence()

                # Update table model as well if available
                if hasattr(self, "cabinet_model") and self.cabinet_model:
                    self.cabinet_model.set_rows(self.cabinets)

            # Also sort the card grid for compatibility if it exists and is valid
            if hasattr(self, "card_grid") and self.card_grid:
                try:
                    # Check if the widget is still valid
                    if (
                        not self.card_grid.isHidden()
                    ):  # This will raise if widget is deleted
                        self.card_grid.sort_cards_by_sequence()
                except RuntimeError as e:
                    logger.warning(
                        f"CardGrid widget no longer valid during sorting: {e}"
                    )

            # If we're in table view mode, refresh the table as well
            if (
                hasattr(self, "_current_view_mode")
                and self._current_view_mode == VIEW_MODE_TABLE
            ):
                self._sync_table_with_cards()

        except Exception as e:
            logger.error(f"Error sorting by sequence: {e}")
            if hasattr(self, "banner_manager"):
                self.banner_manager.show_error(f"Błąd podczas sortowania: {e}")

    def _sync_table_with_cards(self) -> None:
        """Synchronize table view with current cabinets list."""
        model = self.table_view.model()
        if not model:
            return
        source_model = (
            model.sourceModel()
            if hasattr(model, "sourceModel") and model.sourceModel()
            else model
        )

        # Use authoritative self.cabinets list
        rows = (
            list(self.cabinets) if hasattr(self, "cabinets") and self.cabinets else []
        )

        if hasattr(source_model, "set_rows"):
            source_model.set_rows(rows)
        else:
            source_model.cabinets = rows
            source_model.layoutChanged.emit()

    def clear_cabinet_cards(self) -> None:
        """Clear all cabinet cards from the view."""
        # Clear from new FlowLayout
        if hasattr(self, "card_layout") and self.card_layout:
            while self.card_layout.count():
                child = self.card_layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)

        # Clear from old CardGrid for compatibility
        if hasattr(self, "card_grid") and self.card_grid:
            self.card_grid.clear_cards()

    def add_cabinet_card(self, card_data: dict) -> None:
        """Add a cabinet card to the view."""
        # Add to new FlowLayout
        if hasattr(self, "card_layout") and self.card_layout:
            # Create card widget
            card = CabinetCard(card_data)

            # Connect signals (relay to the hidden card_grid for compatibility)
            self._connect_card_signals(card)

            # Add to FlowLayout (it handles QWidget properly)
            self.card_layout.addWidget(card)

        # Add to old CardGrid for compatibility
        if hasattr(self, "card_grid") and self.card_grid:
            self.card_grid.add_card(card_data)

    def show_dialog(self) -> None:
        """Show the dialog in the appropriate mode."""
        if self.modal:
            self.exec()
        else:
            self.show()

    def save_geometry(self) -> None:
        """Save dialog geometry to settings."""
        from PySide6.QtCore import QSettings

        settings = QSettings()
        settings.setValue("project_details/geometry", self.saveGeometry())

    def restore_geometry(self) -> None:
        """Restore dialog geometry from settings."""
        from PySide6.QtCore import QSettings

        settings = QSettings()
        geometry = settings.value("project_details/geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.save_geometry()
        event.accept()

    def _setup_models(self):
        """Setup table model and proxy."""
        self.cabinet_model = CabinetTableModel(self.cabinets)
        self.cabinet_proxy = CabinetProxyModel()
        self.cabinet_proxy.setSourceModel(self.cabinet_model)
        self.table_view.setModel(self.cabinet_proxy)

    def _toggle_empty_state(self):
        """Toggle between empty state and card container based on cabinets."""
        if not self.cabinets:
            self.card_scroll.setWidget(self.empty_state)
        else:
            self.card_scroll.setWidget(self.card_container)

    def _update_card_view(self):
        """Update card view with current cabinet data."""
        # Clear existing cards from FlowLayout
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        # Add cabinet cards to FlowLayout
        for cabinet in self.cabinets:
            card_data = {
                "id": cabinet.id,
                "name": cabinet.cabinet_type.nazwa
                if cabinet.cabinet_type
                else "Niestandardowy",
                "body_color": cabinet.body_color or "biały",
                "front_color": cabinet.front_color or "biały",
                "handle_type": cabinet.handle_type or "Nie określono",
                "quantity": cabinet.quantity,
                "sequence": cabinet.sequence_number,
                "is_custom": cabinet.type_id is None,
            }

            card = CabinetCard(card_data)
            self._connect_card_signals(card)
            self.card_layout.addCard(card)

        # Also add to hidden CardGrid for compatibility
        self.card_grid.clear_cards()
        for cabinet in self.cabinets:
            card_data = {
                "id": cabinet.id,
                "name": cabinet.cabinet_type.nazwa
                if cabinet.cabinet_type
                else "Niestandardowy",
                "body_color": cabinet.body_color or "biały",
                "front_color": cabinet.front_color or "biały",
                "handle_type": cabinet.handle_type or "Nie określono",
                "quantity": cabinet.quantity,
                "sequence": cabinet.sequence_number,
                "is_custom": cabinet.type_id is None,
            }
            self.card_grid.add_card(card_data)

        # Toggle empty state based on cabinet count
        self._toggle_empty_state()

        # 🔧 Force proper layout calculation for initial card positioning
        self._force_initial_layout_calculation()

    def showEvent(self, event):
        """Override showEvent to ensure proper layout calculation when dialog is shown."""
        super().showEvent(event)

        # Force layout calculation after dialog is properly sized
        QApplication.processEvents()  # Ensure sizing is complete
        self._force_initial_layout_calculation()

    def _force_initial_layout_calculation(self):
        """Force proper layout calculation when cards are first loaded."""
        try:
            # Skip if no cards to position
            if self.card_layout.count() == 0:
                return

            # Force layout geometry setup
            try:
                self.card_layout.activate()
            except Exception:
                pass
            self.card_layout.invalidate()

            # Ensure proper visibility for layout calculation (same as sorting)
            was_visible = self.isVisible()
            if not was_visible:
                # Temporarily show to force proper layout calculation
                self.show()
                QApplication.processEvents()

            # Ensure layout has proper geometry - force synchronization
            container_rect = self.card_container.rect()
            if container_rect.width() > 0 and container_rect.height() > 0:
                # Force layout to match container size exactly
                self.card_layout.setGeometry(container_rect)
                self.card_layout.activate()

                # Double-check and force again if needed
                QApplication.processEvents()
                current_layout_geom = self.card_layout.geometry()
                if current_layout_geom != container_rect:
                    self.card_layout.setGeometry(container_rect)
                    self.card_layout.activate()

            # Restore original visibility if we changed it
            if not was_visible:
                self.hide()

            # Force comprehensive geometry updates
            self.card_container.adjustSize()
            self.card_container.updateGeometry()
            self.card_scroll.updateGeometry()

            # Force layout recalculation with current geometry
            final_rect = self.card_container.rect()
            self.card_layout.setGeometry(final_rect)

            if self.card_scroll.viewport():
                self.card_scroll.viewport().update()

            # Multiple event processing to ensure all updates complete
            QApplication.processEvents()
            QApplication.processEvents()  # Second pass for any delayed updates

            # Final step: Force layout recalculation like manual resize does
            self._simulate_resize_layout_fix()

        except Exception as e:
            logger.warning(f"Initial layout calculation failed: {e}")

    def _simulate_resize_layout_fix(self):
        """Simulate what manual resize does to fix layout positioning."""
        try:
            # This simulates the effect of manual resize that fixes positioning
            current_size = self.size()

            # Temporarily change size by 1 pixel (like manual resize)
            self.resize(current_size.width() + 1, current_size.height())
            QApplication.processEvents()

            # Restore original size
            self.resize(current_size.width(), current_size.height())
            QApplication.processEvents()

            # Force layout to recalculate with final size
            final_container_rect = self.card_container.rect()
            self.card_layout.setGeometry(final_container_rect)

            # Additional Qt-level invalidation that manual resize triggers
            self.card_container.updateGeometry()
            self.update()  # Force widget update
            self.repaint()  # Force immediate repaint

        except Exception as e:
            logger.warning(f"Resize simulation failed: {e}")

    def force_layout_recalculation(self):
        """Public method to force layout recalculation if stacking issues occur."""
        try:
            # This method can be called manually if layout issues are detected
            self._force_initial_layout_calculation()

            # Additional force if needed
            if hasattr(self, "card_layout") and hasattr(self, "card_container"):
                self._simulate_resize_layout_fix()

        except Exception as e:
            logger.warning(f"Manual layout recalculation failed: {e}")

    def _force_layout_refresh(self):
        """Force layout refresh to prevent card stacking after sequence changes."""
        try:
            # Try to activate the layout first
            if hasattr(self, "card_layout") and self.card_layout:
                try:
                    self.card_layout.activate()
                except:
                    pass  # activate() might not exist

                self.card_layout.invalidate()

            # Force geometry recalculation on card container
            if hasattr(self, "card_container") and self.card_container:
                self.card_container.adjustSize()
                self.card_container.updateGeometry()
                self.card_container.update()

            # Update scroll area and its viewport
            if hasattr(self, "card_scroll") and self.card_scroll:
                self.card_scroll.updateGeometry()
                if self.card_scroll.viewport():
                    self.card_scroll.viewport().updateGeometry()
                self.card_scroll.update()

            # Process pending events to ensure layout update
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()

        except Exception as e:
            logger.warning(f"Layout refresh failed: {e}")

    def _connect_card_signals(self, card: CabinetCard):
        """Connect card signals to handlers and set up sequence validation."""
        # Connect to service handlers first, then emit compatibility signals
        card.sig_qty_changed.connect(
            lambda cabinet_id, qty: (
                self._handle_quantity_change(cabinet_id, qty),
                self._emit_quantity_signals(cabinet_id, qty),
            )
        )
        card.sig_edit.connect(
            lambda cabinet_id: (
                self._handle_edit(cabinet_id),
                self._emit_edit_signals(cabinet_id),
            )
        )
        card.sig_duplicate.connect(
            lambda cabinet_id: (
                self._handle_duplicate(cabinet_id),
                self._emit_duplicate_signals(cabinet_id),
            )
        )
        card.sig_delete.connect(
            lambda cabinet_id: (
                self._handle_delete(cabinet_id),
                self._emit_delete_signals(cabinet_id),
            )
        )
        card.sig_selected.connect(self.sig_cabinet_selected.emit)
        card.sig_sequence_changed.connect(
            lambda cabinet_id, seq: (
                self._handle_sequence_change(cabinet_id, seq),
                self._emit_sequence_signals(cabinet_id, seq),
            )
        )

        # Set up sequence validation
        self._setup_card_sequence_validation(card)

    def _setup_card_sequence_validation(self, card: CabinetCard):
        """Set up sequence validation for a cabinet card."""
        if hasattr(card, "sequence_input"):
            # Set duplicate check callback that excludes the current card's ID
            card.sequence_input.set_duplicate_check_callback(
                lambda seq, card_id=card.cabinet_id: any(
                    c.sequence_number == seq and c.id != card_id
                    for c in (self.cabinets or [])
                )
            )

            # Set reasonable range
            card.sequence_input.set_range(1, 999)

    def _wire_signals(self):
        """Wire internal signals."""
        # Dialog
        self.button_box.rejected.connect(self.reject if self.modal else self.close)

        # Header
        self.header_bar.sig_export.connect(self._handle_export)
        self.header_bar.sig_print.connect(self._handle_print)

        # Toolbar
        self.toolbar.sig_add_from_catalog.connect(self._handle_add_from_catalog)
        self.toolbar.sig_add_custom.connect(self._handle_add_custom)
        self.toolbar.sig_view_mode_changed.connect(self._handle_view_mode_changed)

    def _check_services_available(self) -> bool:
        """Check if services are available for operations."""
        if not self.project_service or not self.project:
            self.banner_manager.show_warning(
                "Operacja niedostępna: brak połączenia z bazą danych"
            )
            return False
        return True

    # Event handlers
    def _handle_qty_changed(self, cabinet_id: int, new_quantity: int):
        """Handle cabinet quantity change."""
        if not self._check_services_available():
            return

        try:
            updated_cabinet = self.project_service.update_cabinet(
                cabinet_id, quantity=new_quantity
            )
            if updated_cabinet:
                # Update local data
                for i, cabinet in enumerate(self.cabinets):
                    if cabinet.id == cabinet_id:
                        self.cabinets[i] = updated_cabinet
                        break

                # Update model
                if self.cabinet_model:
                    self.cabinet_model.set_rows(self.cabinets)

                self.banner_manager.show_success(
                    f"Ilość została zaktualizowana na {new_quantity}"
                )
                self.sig_cabinet_qty_changed.emit(cabinet_id, new_quantity)
            else:
                self.banner_manager.show_error("Nie udało się zaktualizować ilości")
        except Exception as e:
            logger.error(f"Error updating cabinet quantity: {e}")
            self.banner_manager.show_error(f"Błąd podczas aktualizacji ilości: {e}")

    def _handle_cabinet_edit(self, cabinet_id: int):
        """Handle cabinet edit request."""
        if not self._check_services_available():
            return

        try:
            cabinet = next((c for c in self.cabinets if c.id == cabinet_id), None)
            if not cabinet:
                self.banner_manager.show_error("Nie znaleziono szafki do edycji")
                return

            if cabinet.type_id is None:
                # Custom cabinet
                dialog = AdhocCabinetDialog(
                    self.session, self.project, cabinet_id, self
                )
                dialog.load_cabinet_data(cabinet_id)
            else:
                # Catalog cabinet - show info for now
                self.banner_manager.show_info(
                    "Edycja szafek katalogowych będzie dostępna wkrótce"
                )
                self.sig_cabinet_edit.emit(cabinet_id)
                return

            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_data()
                self.banner_manager.show_success("Szafka została zaktualizowana")

            self.sig_cabinet_edit.emit(cabinet_id)

        except Exception as e:
            logger.error(f"Error editing cabinet: {e}")
            self.banner_manager.show_error(f"Błąd podczas edycji szafki: {e}")

    def _handle_cabinet_duplicate(self, cabinet_id: int):
        """Handle cabinet duplicate request."""
        if not self._check_services_available():
            return

        try:
            original = next((c for c in self.cabinets if c.id == cabinet_id), None)
            if not original:
                self.banner_manager.show_error("Nie znaleziono szafki do duplikacji")
                return

            next_seq = self.project_service.get_next_cabinet_sequence(self.project.id)

            if original.type_id is None:
                # Custom cabinet
                new_cabinet = self.project_service.add_cabinet(
                    self.project.id,
                    cabinet_type_id=None,
                    quantity=original.quantity,
                    sequence_number=next_seq,
                    body_color=original.body_color,
                    front_color=original.front_color,
                    handle_type=original.handle_type,
                )
            else:
                # Catalog cabinet
                new_cabinet = self.project_service.add_cabinet(
                    self.project.id,
                    cabinet_type_id=original.type_id,
                    quantity=original.quantity,
                    sequence_number=next_seq,
                    body_color=original.body_color,
                    front_color=original.front_color,
                    handle_type=original.handle_type,
                )

            if new_cabinet:
                self._load_data()
                self.banner_manager.show_success("Szafka została zduplikowana")

            self.sig_cabinet_duplicate.emit(cabinet_id)

        except Exception as e:
            logger.error(f"Error duplicating cabinet: {e}")
            self.banner_manager.show_error(f"Błąd podczas duplikacji szafki: {e}")

    def _handle_cabinet_delete(self, cabinet_id: int):
        """Handle cabinet delete request."""
        if not self._check_services_available():
            return

        try:
            reply = QMessageBox.question(
                self,
                "Potwierdzenie",
                "Czy na pewno chcesz usunąć tę szafkę?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                success = self.project_service.delete_cabinet(cabinet_id)
                if success:
                    self._load_data()
                    self.banner_manager.show_success("Szafka została usunięta")
                else:
                    self.banner_manager.show_error("Nie udało się usunąć szafki")

            self.sig_cabinet_delete.emit(cabinet_id)

        except Exception as e:
            logger.error(f"Error deleting cabinet: {e}")
            self.banner_manager.show_error(f"Błąd podczas usuwania szafki: {e}")

    def _handle_sequence_changed(self, cabinet_id: int, new_sequence: int):
        """Handle sequence number change."""
        if not self._check_services_available():
            return

        try:
            updated_cabinet = self.project_service.update_cabinet(
                cabinet_id, sequence_number=new_sequence
            )
            if updated_cabinet:
                # Update local data
                for i, cabinet in enumerate(self.cabinets):
                    if cabinet.id == cabinet_id:
                        self.cabinets[i] = updated_cabinet
                        break

                # Refresh view to show proper ordering
                self._update_card_view()
                if self.cabinet_model:
                    self.cabinet_model.set_rows(self.cabinets)

                # Force layout refresh to prevent card stacking
                self._force_layout_refresh()

                self.sig_cabinet_sequence_changed.emit(cabinet_id, new_sequence)
            else:
                self.banner_manager.show_error("Nie udało się zaktualizować sekwencji")
        except Exception as e:
            logger.error(f"Error updating sequence: {e}")
            self.banner_manager.show_error(f"Błąd podczas aktualizacji sekwencji: {e}")

    def _handle_export(self):
        """Handle export request."""
        if not self._check_services_available():
            return

        try:
            report_path = self.report_generator.generate(
                self.project, format_type="pdf"
            )
            if report_path:
                success = open_or_print(report_path, "open")
                if success:
                    self.banner_manager.show_success(
                        "Raport został wygenerowany i otwarty"
                    )
                else:
                    self.banner_manager.show_error("Nie udało się otworzyć raportu")
            else:
                self.banner_manager.show_error("Nie udało się wygenerować raportu")

            self.sig_export.emit()
        except Exception as e:
            logger.error(f"Error exporting: {e}")
            self.banner_manager.show_error(f"Błąd podczas eksportu: {e}")

    def _handle_print(self):
        """Handle print request."""
        if not self._check_services_available():
            return

        try:
            report_path = self.report_generator.generate(
                self.project, format_type="pdf"
            )
            if report_path:
                success = open_or_print(report_path, "print")
                if success:
                    self.banner_manager.show_success(
                        "Raport został wysłany do drukarki"
                    )
                else:
                    self.banner_manager.show_error("Nie udało się wydrukować raportu")
            else:
                self.banner_manager.show_error("Nie udało się wygenerować raportu")

            self.sig_print.emit()
        except Exception as e:
            logger.error(f"Error printing: {e}")
            self.banner_manager.show_error(f"Błąd podczas drukowania: {e}")

    def _handle_add_from_catalog(self):
        """Handle add cabinet from catalog."""
        if not self._check_services_available():
            return

        try:
            dialog = AddCabinetDialog(self.session, self.project, None, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_data()
                self.banner_manager.show_success("Szafka została dodana z katalogu")

            self.sig_add_from_catalog.emit()
        except Exception as e:
            logger.error(f"Error adding from catalog: {e}")
            self.banner_manager.show_error(f"Błąd podczas dodawania szafki: {e}")

    def _handle_add_custom(self):
        """Handle add custom cabinet."""
        if not self._check_services_available():
            return

        try:
            dialog = AdhocCabinetDialog(self.session, self.project, None, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_data()
                self.banner_manager.show_success("Niestandardowa szafka została dodana")

            self.sig_add_custom.emit()
        except Exception as e:
            logger.error(f"Error adding custom cabinet: {e}")
            self.banner_manager.show_error(f"Błąd podczas dodawania szafki: {e}")

    def _handle_view_mode_changed(self, mode: str):
        """Handle view mode change."""
        self._current_view_mode = mode
        self.ui_state.set_view_mode(mode)

        if mode == VIEW_MODE_CARDS:
            self.stacked_widget.setCurrentWidget(self.card_scroll)
        else:
            self.stacked_widget.setCurrentWidget(self.table_view)

        self.sig_view_mode_changed.emit(mode)

    # Aliases for handler methods to match connection calls
    def _handle_quantity_change(self, cabinet_id: int, qty: int):
        """Handle quantity change - alias for existing method."""
        return self._handle_qty_changed(cabinet_id, qty)

    def _handle_edit(self, cabinet_id: int):
        """Handle edit request - alias for existing method."""
        return self._handle_cabinet_edit(cabinet_id)

    def _handle_duplicate(self, cabinet_id: int):
        """Handle duplicate request - alias for existing method."""
        return self._handle_cabinet_duplicate(cabinet_id)

    def _handle_delete(self, cabinet_id: int):
        """Handle delete request - alias for existing method."""
        return self._handle_cabinet_delete(cabinet_id)

    def _handle_sequence_change(self, cabinet_id: int, seq: int):
        """Handle sequence change - alias for existing method."""
        return self._handle_sequence_changed(cabinet_id, seq)


# Convenience class for backwards compatibility with controller pattern
class ProjectDetailsController(QObject):
    """Controller wrapper for the integrated dialog."""

    def __init__(self, session: Session, project: Project, modal: bool = True):
        super().__init__()
        self.session = session
        self.project = project
        self.modal = modal
        self.view = None

    def attach(self, view):
        """Attach is no longer needed - functionality is integrated."""
        self.view = view

    def open(self):
        """Open the integrated dialog."""
        dialog = ProjectDetailsView(self.session, self.project, self.modal)
        return dialog.show_dialog()


# Public interface for backwards compatibility
def create_project_details_dialog(
    session: Session, project: Project, modal: bool = True, parent=None
):
    """Create and return a project details dialog."""
    return ProjectDetailsView(session, project, modal, parent)
