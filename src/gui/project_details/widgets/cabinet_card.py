"""
Cabinet Card Widget

A self-contained card widget for displaying individual cabinet information
with inline editing capabilities for quantity and sequence numbers.
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QMenu,
    QSizePolicy,
    QAbstractButton,
    QLineEdit,
    QSpinBox,
)
from PySide6.QtCore import Signal, Qt, QSize, QTimer
from PySide6.QtGui import QFont, QAction

from src.gui.resources.styles import PRIMARY, CARD_HOVER
from ..constants import CARD_MIN_WIDTH, CARD_MIN_HEIGHT, CARD_WIDTH, CARD_PADDING
from . import ColorChip, QuantityStepper, SequenceNumberInput


class CabinetCard(QFrame):
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
        self._selected = False

        # Timer for delayed single-click handling to prevent conflict with double-click
        self._click_timer = QTimer()
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._handle_single_click)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setMinimumWidth(CARD_MIN_WIDTH)
        self.setMinimumHeight(CARD_MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setObjectName("cabinetCard")

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

        # Dimensions section (shape summary)
        self._add_dimensions_section(main_layout)

        # Quantity section
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Ilość:"))

        self.quantity_stepper = QuantityStepper(self.card_data.get("quantity", 1))
        self.quantity_stepper.value_changed.connect(self._on_quantity_changed)
        qty_layout.addWidget(self.quantity_stepper)
        qty_layout.addStretch()

        main_layout.addLayout(qty_layout)
        main_layout.addStretch()

        self._update_selection_style()

    def _add_dimensions_section(self, main_layout):
        """Add cabinet dimensions/shape summary section."""
        # Create dimensions layout (always, but may be hidden)
        self.dims_layout = QHBoxLayout()
        self.dims_label_title = QLabel("Wymiary:")
        self.dims_layout.addWidget(self.dims_label_title)

        # Create dimensions label
        self.dims_label = QLabel()
        self.dims_label.setStyleSheet("color: #666666; font-size: 11px;")
        self.dims_layout.addWidget(self.dims_label)
        self.dims_layout.addStretch()

        # Update dimensions display
        self._update_dimensions_display()

        main_layout.addLayout(self.dims_layout)

    def _update_dimensions_display(self):
        """Update the dimensions display based on current card data."""
        width_mm = self.card_data.get("width_mm")
        height_mm = self.card_data.get("height_mm")
        depth_mm = self.card_data.get("depth_mm")
        kitchen_type = self.card_data.get("kitchen_type")

        display_text = ""
        label_text = "Wymiary:"

        if width_mm and height_mm:
            # Format dimensions in a compact way
            display_text = f"{int(width_mm)}×{int(height_mm)}"
            if depth_mm:
                display_text += f"×{int(depth_mm)}"
            display_text += " mm"
            label_text = "Wymiary:"
        elif kitchen_type:
            # Show kitchen type if no dimensions available
            display_text = kitchen_type
            label_text = "Typ:"

        if display_text:
            self.dims_label_title.setText(label_text)
            self.dims_label.setText(display_text)
            self.dims_label_title.setVisible(True)
            self.dims_label.setVisible(True)
        else:
            # Hide both labels if no info available
            self.dims_label_title.setVisible(False)
            self.dims_label.setVisible(False)

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

    def update_data(self, new_card_data: Dict[str, Any]):
        """
        Update the card with new data.

        Args:
            new_card_data: Dictionary containing updated card data
        """
        self.card_data = new_card_data
        self.cabinet_id = new_card_data.get("id", 0)

        # Update sequence number
        new_sequence = new_card_data.get("sequence", 1)
        if hasattr(self, "sequence_input"):
            self.sequence_input.set_value(new_sequence)

        # Update cabinet name
        new_name = new_card_data.get("name", "Niestandardowy")
        if hasattr(self, "name_label"):
            self.name_label.setText(new_name)

        # Update colors
        if hasattr(self, "body_color_chip"):
            new_body_color = new_card_data.get("body_color", "#ffffff")
            self.body_color_chip.set_color(new_body_color)

        if hasattr(self, "front_color_chip"):
            new_front_color = new_card_data.get("front_color", "#ffffff")
            self.front_color_chip.set_color(new_front_color)

        # Update quantity
        new_quantity = new_card_data.get("quantity", 1)
        if hasattr(self, "quantity_stepper"):
            self.quantity_stepper.set_value(new_quantity)

        # Update dimensions display
        if hasattr(self, "dims_label"):
            self._update_dimensions_display()

    def _on_quantity_changed(self, new_quantity: int):
        self.card_data["quantity"] = new_quantity
        self.sig_qty_changed.emit(self.cabinet_id, new_quantity)

    def _on_sequence_changed(self, new_sequence: int):
        self.card_data["sequence"] = new_sequence
        self.sig_sequence_changed.emit(self.cabinet_id, new_sequence)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            # Check if click is on an interactive child widget
            if self._is_click_on_interactive_widget(event.pos()):
                return  # Let the child widget handle it

            # Start timer for delayed single-click handling
            # Will be cancelled if double-click occurs within system double-click time
            self._click_timer.start(200)  # 200ms is more responsive

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            # Check if double-click is on an interactive child widget
            if self._is_click_on_interactive_widget(event.pos()):
                return  # Let the child widget handle it

            # Cancel pending single-click action
            self._click_timer.stop()

            # Emit edit signal for double-click
            self.sig_edit.emit(self.cabinet_id)

    def _is_click_on_interactive_widget(self, pos):
        """Check if the click position is on an interactive child widget."""
        child = self.childAt(pos)
        if not child:
            return False

        # Check if it's an interactive widget type or our custom widgets
        interactive_types = (QAbstractButton, QLineEdit, QSpinBox)
        if isinstance(child, interactive_types):
            return True

        # Check for our custom interactive widgets by class name
        class_name = child.__class__.__name__
        if class_name in ("QuantityStepper", "SequenceNumberInput"):
            return True

        # Check if the child is part of an interactive widget
        parent = child.parent()
        while parent and parent != self:
            if isinstance(parent, interactive_types):
                return True
            if parent.__class__.__name__ in ("QuantityStepper", "SequenceNumberInput"):
                return True
            parent = parent.parent()

        return False

    def _handle_single_click(self):
        """Handle delayed single-click for selection toggle."""
        # Always emit signal, let parent handle single selection logic
        self.sig_selected.emit(self.cabinet_id)

    def sizeHint(self):
        """Provide target size hint for consistent appearance while allowing flexibility."""
        if hasattr(self, "layout") and self.layout():
            h = self.layout().sizeHint().height() + 2 * CARD_PADDING
        else:
            h = CARD_MIN_HEIGHT
        return QSize(CARD_WIDTH, max(CARD_MIN_HEIGHT, h))

    def is_card_selected(self):
        """Return current selection state."""
        return self._selected

    def set_selected(self, value: bool):
        """Set selection state with visual feedback."""
        if self._selected != value:
            self._selected = value
            self._update_selection_style()

    def _update_selection_style(self):
        """Update visual style based on selection state."""
        if self._selected:
            self.setStyleSheet(f"""
                QFrame#cabinetCard {{
                    border: 2px solid {PRIMARY};
                    background-color: {CARD_HOVER};
                    border-radius: 8px;
                }}
            """)
        else:
            # Clear any selection styling to use default theme styles
            self.setStyleSheet("")
