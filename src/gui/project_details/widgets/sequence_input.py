"""
Sequence number input widget with validation.
"""

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit


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
        self.input_field.setProperty("invalid", False)
        self.input_field.setProperty("duplicate", False)
        self.input_field.hide()
        self.input_field.editingFinished.connect(self._finish_editing)
        self.input_field.textChanged.connect(self._validate_input_realtime)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field)

        # Set up number validation (1-999 range)
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
        """Set input field dynamic properties for theme-driven validation styling."""
        invalid = state == "error"
        duplicate = state == "warning"
        self.input_field.setProperty("invalid", invalid)
        self.input_field.setProperty("duplicate", duplicate)
        self._refresh_input_style()

    def _refresh_input_style(self):
        self.input_field.style().unpolish(self.input_field)
        self.input_field.style().polish(self.input_field)
        self.input_field.update()

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
                self._set_input_style("normal")
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
            self._set_input_style("normal")
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
