"""
Cabinet Card Widget

A self-contained card widget for displaying individual cabinet information
with inline editing capabilities for quantity and sequence numbers.
"""

from typing import Dict, Any
import time as _time
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
        # Prevent any chance of flashing as a separate window during construction
        self.setAttribute(Qt.WA_DontShowOnScreen, True)
        # Per-card instrumentation
        self._card_start = _time.perf_counter()
        self._card_dbg = lambda msg: print(
            f"[CARD DEBUG][{self.cabinet_id}][{(_time.perf_counter() - self._card_start) * 1000:.1f}ms] {msg}"
        )

        # Timer for delayed single-click handling to prevent conflict with double-click
        self._click_timer = QTimer()
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._handle_single_click)

        self._setup_ui()
        self._connect_signals()
        # Report total card construction time
        self._card_dbg("total construction complete")
        # Allow normal display after construction completes
        self.setAttribute(Qt.WA_DontShowOnScreen, False)

    def _setup_ui(self):
        self._card_dbg("_setup_ui starting")
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

        self._card_dbg("creating SequenceNumberInput")
        self.sequence_input = SequenceNumberInput(
            self.card_data.get("sequence", 1), parent=self
        )
        self.sequence_input.sequence_changed.connect(self._on_sequence_changed)
        header_layout.addWidget(self.sequence_input)

        header_layout.addStretch()

        # Action menu
        self.menu_btn = QToolButton(self)
        self.menu_btn.setText("⋮")
        self.menu_btn.setPopupMode(QToolButton.InstantPopup)
        self._setup_menu()
        header_layout.addWidget(self.menu_btn)

        main_layout.addLayout(header_layout)

        # Cabinet name
        self._card_dbg("setting name label")
        name = self.card_data.get("name", "Niestandardowy")
        self.name_label = QLabel(name, parent=self)
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        self.name_label.setWordWrap(True)
        main_layout.addWidget(self.name_label)

        # Colors section
        self._card_dbg("creating ColorChip body")
        colors_layout = QHBoxLayout()
        colors_layout.addWidget(QLabel("Korpus:", parent=self))
        self.body_color_chip = ColorChip(
            self.card_data.get("body_color", "Biały"), "Korpus", parent=self
        )
        colors_layout.addWidget(self.body_color_chip)

        colors_layout.addSpacing(10)
        colors_layout.addWidget(QLabel("Front:", parent=self))
        self._card_dbg("creating ColorChip front")
        self.front_color_chip = ColorChip(
            self.card_data.get("front_color", "Biały"), "Front", parent=self
        )
        colors_layout.addWidget(self.front_color_chip)
        colors_layout.addStretch()

        main_layout.addLayout(colors_layout)

        # Dimensions section (shape summary)
        self._card_dbg("adding dimensions section")
        self._add_dimensions_section(main_layout)

        # Quantity section (lazy: create a lightweight placeholder; real widget created on demand)
        self._card_dbg("creating quantity placeholder")
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Ilość:"))

        qty = int(self.card_data.get("quantity", 1))
        self._qty_placeholder = QLabel(str(qty))
        self._qty_placeholder.setObjectName("quantityPlaceholder")
        qty_layout.addWidget(self._qty_placeholder)
        qty_layout.addStretch()

        # keep reference so we can replace placeholder later
        self._qty_layout = qty_layout

        main_layout.addLayout(qty_layout)
        main_layout.addStretch()

        self._update_selection_style()
        self._card_dbg("_setup_ui complete")

    def _add_dimensions_section(self, main_layout):
        """Add cabinet dimensions/shape summary section."""
        # Create dimensions layout (always, but may be hidden)
        self.dims_layout = QHBoxLayout()
        self.dims_label_title = QLabel("Wymiary:", parent=self)
        self.dims_layout.addWidget(self.dims_label_title)

        # Create dimensions label
        self.dims_label = QLabel(parent=self)
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
        self.context_menu = QMenu(self)

        edit_action = QAction("Edytuj", self)
        edit_action.triggered.connect(lambda: self.sig_edit.emit(self.cabinet_id))
        self.context_menu.addAction(edit_action)

        duplicate_action = QAction("Duplikuj", self)
        duplicate_action.triggered.connect(
            lambda: self.sig_duplicate.emit(self.cabinet_id)
        )
        self.context_menu.addAction(duplicate_action)

        self.context_menu.addSeparator()

        delete_action = QAction("Usuń", self)
        delete_action.triggered.connect(lambda: self.sig_delete.emit(self.cabinet_id))
        self.context_menu.addAction(delete_action)

        self.menu_btn.setMenu(self.context_menu)

    def _connect_signals(self):
        pass

    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        self.context_menu.exec(event.globalPos())

    def showEvent(self, event):
        """Ensure heavy sub-widgets are created when card becomes visible."""
        super().showEvent(event)
        # Create QuantityStepper lazily when the card is shown
        self._ensure_quantity_stepper()

    def _ensure_quantity_stepper(self):
        """Create QuantityStepper if not already present and replace placeholder."""
        if hasattr(self, "quantity_stepper"):
            return

        self._card_dbg("creating lazy QuantityStepper")
        qty_val = int(self.card_data.get("quantity", 1))
        try:
            self.quantity_stepper = QuantityStepper(qty_val, parent=self)
            self.quantity_stepper.value_changed.connect(self._on_quantity_changed)
        except Exception:
            # Fallback: keep placeholder if creation fails
            self._card_dbg("failed to create QuantityStepper, keeping placeholder")
            return

        # Replace placeholder widget in layout
        if hasattr(self, "_qty_placeholder") and hasattr(self, "_qty_layout"):
            # find index of placeholder in layout
            for i in range(self._qty_layout.count()):
                item = self._qty_layout.itemAt(i)
                if item and item.widget() == self._qty_placeholder:
                    # remove placeholder
                    widget = item.widget()
                    self._qty_layout.removeWidget(widget)
                    widget.setParent(None)
                    break

            # insert the real stepper at the same position (append before stretch)
            self._qty_layout.insertWidget(i, self.quantity_stepper)
            # update placeholder reference
            delattr(self, "_qty_placeholder")

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
            new_body_color = new_card_data.get("body_color", "Biały")
            self.body_color_chip.set_color(new_body_color)

        if hasattr(self, "front_color_chip"):
            new_front_color = new_card_data.get("front_color", "Biały")
            self.front_color_chip.set_color(new_front_color)

        # Update quantity
        new_quantity = new_card_data.get("quantity", 1)
        if hasattr(self, "quantity_stepper"):
            self.quantity_stepper.set_value(new_quantity)
        else:
            if hasattr(self, "_qty_placeholder"):
                self._qty_placeholder.setText(str(new_quantity))

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
            # Restore default card style explicitly to avoid visual glitches
            self.setStyleSheet(f"""
                QFrame#cabinetCard {{
                    background-color: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                }}
                QFrame#cabinetCard:hover {{
                    border-color: {PRIMARY};
                    border-width: 2px;
                    background-color: {CARD_HOVER};
                }}
            """)
