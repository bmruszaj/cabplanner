"""
Dialog for creating a user-defined color entry.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QColorDialog,
    QFrame,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor

from src.services.color_palette_service import ColorPaletteService


class ColorEditDialog(QDialog):
    """Create a color (name + HEX) and store it in the DB."""

    sig_color_created = Signal(str)

    def __init__(self, color_service: ColorPaletteService, parent=None):
        super().__init__(parent)
        self.color_service = color_service
        self.created_color_name = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Dodaj kolor")
        self.resize(440, 190)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("np. Dąb Naturalny")
        form.addRow("Nazwa*:", self.name_edit)

        hex_row = QWidget(self)
        hex_row_layout = QHBoxLayout(hex_row)
        hex_row_layout.setContentsMargins(0, 0, 0, 0)
        hex_row_layout.setSpacing(8)

        self.hex_edit = QLineEdit()
        self.hex_edit.setPlaceholderText("#AABBCC")
        self.hex_edit.textChanged.connect(self._update_preview_from_hex)
        hex_row_layout.addWidget(self.hex_edit, 1)

        self.pick_color_btn = QPushButton("Koło kolorów")
        self.pick_color_btn.clicked.connect(self._open_color_wheel)
        hex_row_layout.addWidget(self.pick_color_btn)
        form.addRow("HEX*:", hex_row)

        self.color_preview = QFrame(self)
        self.color_preview.setFixedSize(28, 28)
        form.addRow("Podgląd:", self.color_preview)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = buttons.button(QDialogButtonBox.Save)
        if save_button is not None:
            save_button.setText("Zapisz")
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        if cancel_button is not None:
            cancel_button.setText("Anuluj")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.hex_edit.setText("#FFFFFF")

    def _open_color_wheel(self) -> None:
        """Open non-native QColorDialog to provide wheel/spectrum picker."""
        current = QColor(self.hex_edit.text().strip())
        if not current.isValid():
            current = QColor("#FFFFFF")

        picker = QColorDialog(self)
        picker.setWindowTitle("Wybierz kolor")
        picker.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        picker.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        picker.setCurrentColor(current)

        if picker.exec() == QDialog.DialogCode.Accepted:
            chosen = picker.currentColor()
            if chosen.isValid():
                self.hex_edit.setText(chosen.name(QColor.NameFormat.HexRgb).upper())

    def _update_preview_from_hex(self, raw_hex: str) -> None:
        """Refresh preview swatch from current HEX input."""
        color = QColor((raw_hex or "").strip())
        border_color = "#CFCFCF"
        fill_color = "#FFFFFF"

        if color.isValid():
            fill_color = color.name(QColor.NameFormat.HexRgb).upper()
        else:
            border_color = "#D9534F"

        self.color_preview.setStyleSheet(
            f"""
            QFrame {{
                background-color: {fill_color};
                border: 2px solid {border_color};
                border-radius: 4px;
            }}
            """
        )

    def accept(self):
        name = self.name_edit.text().strip()
        hex_code = self.hex_edit.text().strip()

        try:
            color = self.color_service.add_user_color(name, hex_code)
            self.color_service.sync_runtime_color_map()
        except ValueError as exc:
            QMessageBox.warning(self, "Błąd walidacji", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się zapisać koloru:\n{str(exc)}"
            )
            return

        self.created_color_name = color.name
        self.sig_color_created.emit(color.name)
        super().accept()
