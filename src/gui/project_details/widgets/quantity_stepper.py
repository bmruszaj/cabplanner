"""
Quantity stepper widget for inline value adjustment.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSpinBox

from ..constants import (
    MIN_CABINET_QUANTITY,
    MAX_CABINET_QUANTITY,
    QUANTITY_STEPPER_BUTTON_SIZE,
    QUANTITY_INPUT_WIDTH,
)


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

        btn_size = QUANTITY_STEPPER_BUTTON_SIZE
        stepper_button_style = f"""
QPushButton {{
    min-width: {btn_size}px;
    max-width: {btn_size}px;
    min-height: {btn_size}px;
    max-height: {btn_size}px;
    padding: 0px;
    text-align: center;
    font-size: 11pt;
    font-weight: 600;
}}
"""

        button_font = QFont(self.font())
        button_font.setPointSize(11)
        button_font.setWeight(QFont.Weight.DemiBold)

        self.decrease_btn = QPushButton("-")
        self.decrease_btn.setFont(button_font)
        self.decrease_btn.setStyleSheet(stepper_button_style)
        self.decrease_btn.setFixedSize(btn_size, btn_size)
        self.decrease_btn.clicked.connect(self._decrease_value)
        layout.addWidget(self.decrease_btn)

        self.spinbox = QSpinBox()
        self.spinbox.setRange(MIN_CABINET_QUANTITY, MAX_CABINET_QUANTITY)
        self.spinbox.setValue(self._value)
        self.spinbox.setFixedSize(QUANTITY_INPUT_WIDTH, btn_size)
        self.spinbox.setStyleSheet("QSpinBox { padding: 0px 4px; }")
        self.spinbox.setButtonSymbols(QSpinBox.NoButtons)
        self.spinbox.setAlignment(Qt.AlignCenter)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        layout.addWidget(self.spinbox)

        self.increase_btn = QPushButton("+")
        self.increase_btn.setFont(button_font)
        self.increase_btn.setStyleSheet(stepper_button_style)
        self.increase_btn.setFixedSize(btn_size, btn_size)
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
