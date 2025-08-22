"""
Cabinet Card widget for displaying individual cabinets.

This widget represents a single cabinet in the card view with inline quantity editing
and context menu actions.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction, QColor, QPainter, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMenu,
    QToolButton,
)

from ..constants import (
    COLORS,
    CARD_MIN_W,
    CARD_MIN_H,
    CSS_CABINET_CARD,
    CARD_STYLESHEET,
)

logger = logging.getLogger(__name__)


class ColorChip(QWidget):
    """Small color chip widget for displaying cabinet colors."""

    def __init__(self, color: str, label: str = "", parent=None):
        super().__init__(parent)
        self.color = color
        self.label = label
        self.setFixedSize(20, 20)
        self.setToolTip(f"{label}: {color}" if label else color)

    def paintEvent(self, event):
        """Paint the color chip."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw color circle
        painter.setBrush(QBrush(QColor(self.color)))
        painter.setPen(QColor("#ccc"))
        painter.drawEllipse(2, 2, 16, 16)


class QuantityStepper(QWidget):
    """Inline quantity stepper widget with +/- buttons."""

    value_changed = Signal(int)

    def __init__(self, initial_value: int = 1, parent=None):
        super().__init__(parent)
        self._value = initial_value
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the stepper UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Decrease button
        self.decrease_btn = QPushButton("–")
        self.decrease_btn.setFixedSize(24, 24)
        self.decrease_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["button_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS["button_hover"]};
            }}
            QPushButton:disabled {{
                background-color: {COLORS["disabled"]};
                color: {COLORS["text_disabled"]};
            }}
        """)
        layout.addWidget(self.decrease_btn)

        # Value label
        self.value_label = QLabel(str(self._value))
        self.value_label.setFixedWidth(30)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                border: 1px solid {COLORS["border"]};
                border-left: none;
                border-right: none;
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        layout.addWidget(self.value_label)

        # Increase button
        self.increase_btn = QPushButton("+")
        self.increase_btn.setFixedSize(24, 24)
        self.increase_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["button_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS["button_hover"]};
            }}
        """)
        layout.addWidget(self.increase_btn)

    def _connect_signals(self) -> None:
        """Connect signals."""
        self.decrease_btn.clicked.connect(self._decrease)
        self.increase_btn.clicked.connect(self._increase)

    def _decrease(self) -> None:
        """Decrease the value."""
        if self._value > 1:
            self._value -= 1
            self._update_display()
            self.value_changed.emit(self._value)

    def _increase(self) -> None:
        """Increase the value."""
        self._value += 1
        self._update_display()
        self.value_changed.emit(self._value)

    def _update_display(self) -> None:
        """Update the display."""
        self.value_label.setText(str(self._value))
        self.decrease_btn.setEnabled(self._value > 1)

    def set_value(self, value: int) -> None:
        """Set the current value."""
        if value >= 1:
            self._value = value
            self._update_display()

    def get_value(self) -> int:
        """Get the current value."""
        return self._value


class CabinetCard(QWidget):
    """
    Widget representing a single cabinet card.

    Displays:
    - Sequence number (#1, #2, etc.)
    - Cabinet type name
    - Color chips for korpus/front
    - Handle type
    - Inline quantity stepper
    - Overflow menu with actions
    """

    # Signals
    sig_qty_changed = Signal(int, int)  # cab_id, new_quantity
    sig_edit = Signal(int)  # cab_id
    sig_duplicate = Signal(int)  # cab_id
    sig_delete = Signal(int)  # cab_id
    sig_selected = Signal(int)  # cab_id

    def __init__(self, cabinet_id: int = 0, parent=None):
        """
        Initialize the cabinet card.

        Args:
            cabinet_id: The cabinet ID
            parent: Parent widget
        """
        super().__init__(parent)
        self.cabinet_id = cabinet_id
        self._is_selected = False
        self._data = {}

        self._setup_ui()
        self._connect_signals()
        self._update_selection_style()

    def _setup_ui(self) -> None:
        """Set up the card UI with modern styling."""
        # Set minimum size using constants
        self.setMinimumSize(CARD_MIN_W, CARD_MIN_H)

        # Apply CSS class for styling
        self.setProperty("class", CSS_CABINET_CARD)

        # Set object name for selection styling
        self.setObjectName("cabinet_card")

        # Apply modern card styling
        self.setStyleSheet(CARD_STYLESHEET)

        # Main layout with proper margins
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.setCursor(Qt.PointingHandCursor)

        # Header row - sequence + overflow menu
        header_layout = QHBoxLayout()

        self.sequence_label = QLabel("#1")
        sequence_font = QFont()
        sequence_font.setBold(True)
        sequence_font.setPointSize(11)
        self.sequence_label.setFont(sequence_font)
        self.sequence_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(self.sequence_label)

        header_layout.addStretch()

        # Overflow menu button
        self.menu_btn = QToolButton()
        self.menu_btn.setText("⋮")
        self.menu_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                background: transparent;
                color: {COLORS["text_secondary"]};
                font-size: 16px;
                font-weight: bold;
                width: 20px;
                height: 20px;
            }}
            QToolButton:hover {{
                background-color: {COLORS["hover"]};
                border-radius: 10px;
                color: {COLORS["text_primary"]};
            }}
        """)
        self.menu_btn.setPopupMode(QToolButton.InstantPopup)
        self._setup_overflow_menu()
        header_layout.addWidget(self.menu_btn)

        layout.addLayout(header_layout)

        # Cabinet type name
        self.type_label = QLabel("Cabinet Type")
        type_font = QFont()
        type_font.setBold(True)
        type_font.setPointSize(13)
        self.type_label.setFont(type_font)
        self.type_label.setWordWrap(True)
        self.type_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.type_label)

        # Color chips row
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(8)

        # Korpus color
        korpus_container = QHBoxLayout()
        korpus_container.setSpacing(4)
        self.korpus_chip = ColorChip("#ffffff", "Korpus")
        korpus_label = QLabel("K:")
        korpus_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        korpus_container.addWidget(korpus_label)
        korpus_container.addWidget(self.korpus_chip)

        # Front color
        front_container = QHBoxLayout()
        front_container.setSpacing(4)
        self.front_chip = ColorChip("#ffffff", "Front")
        front_label = QLabel("F:")
        front_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        front_container.addWidget(front_label)
        front_container.addWidget(self.front_chip)

        colors_layout.addLayout(korpus_container)
        colors_layout.addLayout(front_container)
        colors_layout.addStretch()

        layout.addLayout(colors_layout)

        # Handle type
        self.handle_label = QLabel("Handle Type")
        self.handle_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px;"
        )
        layout.addWidget(self.handle_label)

        layout.addStretch()

        # Bottom row - quantity stepper
        bottom_layout = QHBoxLayout()

        qty_label = QLabel("Qty:")
        qty_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        bottom_layout.addWidget(qty_label)

        self.quantity_stepper = QuantityStepper(1)
        bottom_layout.addWidget(self.quantity_stepper)

        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

    def _setup_overflow_menu(self) -> None:
        """Set up the overflow menu."""
        menu = QMenu(self)

        # Edit action
        edit_action = QAction("Edytuj", self)
        edit_action.triggered.connect(lambda: self.sig_edit.emit(self.cabinet_id))
        menu.addAction(edit_action)

        # Duplicate action
        duplicate_action = QAction("Duplikuj", self)
        duplicate_action.triggered.connect(
            lambda: self.sig_duplicate.emit(self.cabinet_id)
        )
        menu.addAction(duplicate_action)

        menu.addSeparator()

        # Delete action
        delete_action = QAction("Usuń", self)
        delete_action.triggered.connect(lambda: self.sig_delete.emit(self.cabinet_id))
        menu.addAction(delete_action)

        self.menu_btn.setMenu(menu)

    def _connect_signals(self) -> None:
        """Connect signals."""
        self.quantity_stepper.value_changed.connect(
            lambda qty: self.sig_qty_changed.emit(self.cabinet_id, qty)
        )

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for selection."""
        if event.button() == Qt.LeftButton:
            self.sig_selected.emit(self.cabinet_id)
            event.accept()
        else:
            super().mousePressEvent(event)

    def set_data(self, data: Dict[str, Any]) -> None:
        """
        Set the cabinet data with resilience for missing values.

        Args:
            data: Cabinet data dictionary
        """
        self._data = data

        # Update sequence (with safe fallback)
        sequence = data.get("sequence", 1)
        try:
            sequence_num = int(sequence) if sequence is not None else 1
        except (ValueError, TypeError):
            sequence_num = 1
        self.sequence_label.setText(f"#{sequence_num}")

        # Update type name (with safe fallback for missing cabinet_type)
        type_name = data.get("type_name")
        if not type_name or type_name.strip() == "":
            # Fallback for missing or empty type name
            if data.get("type_id") is None:
                type_name = "Szafka niestandardowa"
            else:
                type_name = "Szafka katalogowa"
        self.type_label.setText(type_name)

        # Update colors (with safe fallbacks)
        korpus_color = data.get("korpus_color") or "#f5f5f5"
        front_color = data.get("front_color") or "#ffffff"

        # Validate color format
        if not isinstance(korpus_color, str) or not korpus_color.startswith("#"):
            korpus_color = "#f5f5f5"
        if not isinstance(front_color, str) or not front_color.startswith("#"):
            front_color = "#ffffff"

        self.korpus_chip.color = korpus_color
        self.front_chip.color = front_color
        self.korpus_chip.update()
        self.front_chip.update()

        # Update handle (with safe fallback)
        handle_type = data.get("handle_type")
        if not handle_type or handle_type.strip() == "":
            handle_type = "Standardowy"
        self.handle_label.setText(f"Uchwyt: {handle_type}")

        # Update quantity (with safe fallback)
        quantity = data.get("quantity", 1)
        try:
            quantity_num = int(quantity) if quantity is not None else 1
            quantity_num = max(1, quantity_num)  # Ensure at least 1
        except (ValueError, TypeError):
            quantity_num = 1
        self.quantity_stepper.set_value(quantity_num)

    def set_selected(self, selected: bool) -> None:
        """Set the selection state."""
        if self._is_selected != selected:
            self._is_selected = selected
            self._update_selection_style()

    def _update_selection_style(self) -> None:
        """Update the card style based on selection state."""
        if self._is_selected:
            border_color = COLORS["accent"]
            background_color = COLORS["selected"]
        else:
            border_color = COLORS["border"]
            background_color = COLORS["background"]

        self.setStyleSheet(f"""
            CabinetCard {{
                background-color: {background_color};
                border: 2px solid {border_color};
                border-radius: 6px;
            }}
            CabinetCard:hover {{
                border-color: {COLORS["accent"]};
            }}
        """)

    def get_cabinet_id(self) -> int:
        """Get the cabinet ID."""
        return self.cabinet_id

    def is_selected(self) -> bool:
        """Check if the card is selected."""
        return self._is_selected
