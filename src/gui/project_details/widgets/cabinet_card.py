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
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QFont, QAction, QTextLayout

from ..constants import (
    CARD_MIN_WIDTH,
    CARD_MIN_HEIGHT,
    CARD_WIDTH,
    CARD_PADDING,
)
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
        self._full_name = ""
        self._dims_full_text = ""
        # Prevent any chance of flashing as a separate window during construction
        self.setAttribute(Qt.WA_DontShowOnScreen, True)
        self._card_dbg = lambda _msg: None

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
        self.setFocusPolicy(Qt.StrongFocus)
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
        self._full_name = self.card_data.get("name", "Niestandardowy")
        self.name_label = QLabel(parent=self)
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.name_label.setMaximumHeight(
            self.name_label.fontMetrics().lineSpacing() * 2 + 2
        )
        self._update_name_display()
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
        self._qty_placeholder.setAlignment(Qt.AlignCenter)
        # Reserve exact width to prevent layout jump when replacing with QuantityStepper.
        self._reserved_qty_width = QuantityStepper.expected_width()
        self._qty_placeholder.setFixedWidth(self._reserved_qty_width)
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
        self.dims_label.setProperty("class", "card-dimensions")
        self.dims_label.setWordWrap(False)
        self.dims_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
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

        has_width = isinstance(width_mm, (int, float)) and width_mm > 0
        has_height = isinstance(height_mm, (int, float)) and height_mm > 0
        has_depth = isinstance(depth_mm, (int, float)) and depth_mm > 0

        display_text = "brak wymiarów"
        if has_width and has_height:
            display_text = f"{int(width_mm)}x{int(height_mm)}"
            if has_depth:
                display_text += f"x{int(depth_mm)}"
            display_text += " mm"

        self.dims_label_title.setText("Wymiary:")
        self._dims_full_text = display_text
        self._update_dimensions_elide()
        self.dims_label_title.setVisible(True)
        self.dims_label.setVisible(True)

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
            if hasattr(self, "_reserved_qty_width"):
                self.quantity_stepper.setFixedWidth(self._reserved_qty_width)
        except Exception:
            # Fallback: keep placeholder if creation fails
            self._card_dbg("failed to create QuantityStepper, keeping placeholder")
            return

        # Replace placeholder widget in layout
        if hasattr(self, "_qty_placeholder") and hasattr(self, "_qty_layout"):
            placeholder_index = -1
            for i in range(self._qty_layout.count()):
                item = self._qty_layout.itemAt(i)
                if item and item.widget() == self._qty_placeholder:
                    placeholder_index = i
                    widget = item.widget()
                    self._qty_layout.removeWidget(widget)
                    widget.setParent(None)
                    break

            # Insert before stretch even if placeholder is missing.
            if placeholder_index < 0:
                placeholder_index = max(0, self._qty_layout.count() - 1)
            self._qty_layout.insertWidget(placeholder_index, self.quantity_stepper)
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
            self._full_name = new_name
            self._update_name_display()

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

    def update_sequence_display(self, sequence: int):
        """Compatibility method for legacy grid API."""
        self.card_data["sequence"] = sequence
        if hasattr(self, "sequence_input"):
            self.sequence_input.set_value(sequence)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            click_pos = event.position().toPoint()
            # Check if click is on an interactive child widget
            if self._is_click_on_interactive_widget(click_pos):
                return  # Let the child widget handle it

            self.setFocus(Qt.MouseFocusReason)
            # Select immediately to avoid click-delay and keep UX responsive.
            self.sig_selected.emit(self.cabinet_id)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            click_pos = event.position().toPoint()
            # Check if double-click is on an interactive child widget
            if self._is_click_on_interactive_widget(click_pos):
                return  # Let the child widget handle it

            # Emit edit signal for double-click
            self.sig_edit.emit(self.cabinet_id)

    def keyPressEvent(self, event):
        """Keyboard accessibility for card selection and edit actions."""
        if event.key() in (Qt.Key_Space,):
            self.sig_selected.emit(self.cabinet_id)
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_F2):
            self.sig_edit.emit(self.cabinet_id)
            event.accept()
            return
        super().keyPressEvent(event)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_name_display()
        self._update_dimensions_elide()

    def _update_name_display(self):
        """Clamp cabinet name to two lines and keep full text in tooltip."""
        text = self._full_name or "Niestandardowy"
        display_text, was_elided = self._elide_to_lines(text, self.name_label, 2)
        self.name_label.setText(display_text)
        self.name_label.setToolTip(text if was_elided else "")

    def _elide_to_lines(
        self, text: str, label: QLabel, max_lines: int
    ) -> tuple[str, bool]:
        """Elide text to a fixed number of wrapped lines for stable card height."""
        available_width = max(40, label.width() or (self.width() - 2 * CARD_PADDING))
        layout = QTextLayout(text, label.font())
        layout.beginLayout()
        lines = []
        ranges = []
        while len(lines) < max_lines:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(available_width)
            start = line.textStart()
            length = line.textLength()
            ranges.append((start, length))
            lines.append(text[start : start + length].rstrip())
        layout.endLayout()

        if not ranges:
            return text, False

        consumed = ranges[-1][0] + ranges[-1][1]
        truncated = consumed < len(text)
        if truncated:
            last_start = ranges[-1][0]
            lines[-1] = label.fontMetrics().elidedText(
                text[last_start:], Qt.ElideRight, available_width
            )
        return "\n".join(lines), truncated

    def _update_dimensions_elide(self):
        if not hasattr(self, "dims_label"):
            return
        full_text = self._dims_full_text or ""
        if not full_text:
            self.dims_label.clear()
            self.dims_label.setToolTip("")
            return
        width = max(40, self.dims_label.width() or (self.width() // 2))
        elided = self.dims_label.fontMetrics().elidedText(
            full_text, Qt.ElideRight, width
        )
        self.dims_label.setText(elided)
        self.dims_label.setToolTip(full_text if elided != full_text else "")

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
        """Update selected dynamic property for theme-driven styling."""
        self.setProperty("selected", self._selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
