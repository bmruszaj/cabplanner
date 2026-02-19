"""
Add footer for project integration.

Provides quantity controls, options, and "Add to project" functionality.
"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QComboBox,
    QPushButton,
    QSizePolicy,
    QGroupBox,
    QCompleter,
    QDialog,
)
from PySide6.QtCore import Signal, QSize, Qt

from src.gui.resources.styles import get_theme, PRIMARY
from src.gui.resources.resources import get_icon
from src.gui.constants.colors import POPULAR_COLORS
from src.gui.dialogs.color_edit_dialog import ColorEditDialog
from src.services.color_palette_service import ColorPaletteService


class AddFooter(QWidget):
    """Footer for adding cabinets to project."""

    # Signals
    sig_add_to_project = Signal()

    def __init__(
        self,
        parent=None,
        color_service: ColorPaletteService | None = None,
        is_dark_mode: bool = False,
    ):
        super().__init__(parent)
        self.color_service = color_service
        self.is_dark_mode = is_dark_mode
        self._setup_ui()
        self._setup_connections()
        self._apply_styles()
        self._load_color_controls()
        self.set_enabled(False)

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        # Quantity group
        qty_group = QGroupBox("Ilość")
        qty_layout = QVBoxLayout(qty_group)
        qty_layout.setContentsMargins(8, 8, 8, 8)

        self.qty_spinbox = QSpinBox()
        self.qty_spinbox.setRange(1, 999)
        self.qty_spinbox.setValue(1)
        self.qty_spinbox.setSuffix(" szt")
        qty_layout.addWidget(self.qty_spinbox)

        layout.addWidget(qty_group)

        # Options group
        options_group = QGroupBox("Opcje")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(8, 8, 8, 8)
        options_layout.setSpacing(4)

        # Body color
        body_layout = QHBoxLayout()
        body_layout.addWidget(QLabel("Korpus:"))
        self.body_color_combo = QComboBox()
        self.body_color_combo.setEditable(True)
        self.body_color_combo.setCurrentText("Biały")
        body_layout.addWidget(self.body_color_combo)

        self.body_add_color_btn = QPushButton("Dodaj kolor")
        self.body_add_color_btn.setObjectName("addColorBtn")
        body_layout.addWidget(self.body_add_color_btn)
        options_layout.addLayout(body_layout)

        # Front color
        front_layout = QHBoxLayout()
        front_layout.addWidget(QLabel("Front:"))
        self.front_color_combo = QComboBox()
        self.front_color_combo.setEditable(True)
        self.front_color_combo.setCurrentText("Biały")
        front_layout.addWidget(self.front_color_combo)

        self.front_add_color_btn = QPushButton("Dodaj kolor")
        self.front_add_color_btn.setObjectName("addColorBtn")
        front_layout.addWidget(self.front_add_color_btn)
        options_layout.addLayout(front_layout)

        # Handle type
        handle_layout = QHBoxLayout()
        handle_layout.addWidget(QLabel("Uchwyt:"))
        self.handle_combo = QComboBox()
        self.handle_combo.addItems(
            ["Standardowy", "Nowoczesny", "Klasyczny", "Bez uchwytów"]
        )
        self.handle_combo.setCurrentText("Standardowy")
        handle_layout.addWidget(self.handle_combo)
        options_layout.addLayout(handle_layout)

        layout.addWidget(options_group)

        # Add stretch to push button to right
        layout.addStretch()

        # Add button
        self.add_button = QPushButton("Dodaj do projektu")
        self.add_button.setIcon(get_icon("add"))
        icon_size = int(self.add_button.fontMetrics().height() * 0.8)
        self.add_button.setIconSize(QSize(icon_size, icon_size))
        self.add_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.add_button)

    def _setup_connections(self):
        """Setup signal connections."""
        self.add_button.clicked.connect(self.sig_add_to_project.emit)
        self.body_add_color_btn.clicked.connect(
            lambda: self._open_add_color_dialog(self.body_color_combo)
        )
        self.front_add_color_btn.clicked.connect(
            lambda: self._open_add_color_dialog(self.front_color_combo)
        )

    def _apply_styles(self):
        """Apply styling to the footer."""
        panel_border = "#4A4A4A" if self.is_dark_mode else "#D0D0D0"
        panel_bg = "#2F2F2F" if self.is_dark_mode else "#FAFAFA"
        input_bg = "#333333" if self.is_dark_mode else "white"
        input_border = "#5A5A5A" if self.is_dark_mode else "#D0D0D0"
        text_color = "#E0E0E0" if self.is_dark_mode else "#333333"
        disabled_bg = "#555555" if self.is_dark_mode else "#CCCCCC"
        disabled_text = "#9A9A9A" if self.is_dark_mode else "#666666"
        down_arrow_color = "#D0D0D0" if self.is_dark_mode else "#999999"
        add_color_bg = "#333333" if self.is_dark_mode else "white"
        add_color_border = "#5A5A5A" if self.is_dark_mode else "#D0D0D0"
        add_color_hover = "#3A3A3A" if self.is_dark_mode else "#F8F8F8"

        self.setStyleSheet(
            get_theme(self.is_dark_mode)
            + f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {panel_border};
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 4px;
                background-color: {panel_bg};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background-color: {panel_bg};
                color: {text_color};
            }}
            QSpinBox {{
                padding: 4px;
                border: 1px solid {input_border};
                border-radius: 4px;
                background-color: {input_bg};
                color: {text_color};
                font-size: 10pt;
            }}
            QSpinBox:focus {{
                border-color: {PRIMARY};
            }}
            QComboBox {{
                padding: 4px;
                border: 1px solid {input_border};
                border-radius: 4px;
                background-color: {input_bg};
                color: {text_color};
                font-size: 10pt;
                min-width: 80px;
            }}
            QComboBox:focus {{
                border-color: {PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: 1px solid {down_arrow_color};
                width: 8px;
                height: 8px;
                border-style: solid;
                border-width: 0 2px 2px 0;
                margin-right: 6px;
            }}
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY.replace("#0A766C", "#0B8A7A")};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY.replace("#0A766C", "#085D56")};
            }}
            QPushButton:disabled {{
                background-color: {disabled_bg};
                color: {disabled_text};
            }}
            QPushButton#addColorBtn {{
                background-color: {add_color_bg};
                color: {text_color};
                border: 1px solid {add_color_border};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9pt;
                font-weight: normal;
                min-width: 0;
            }}
            QPushButton#addColorBtn:hover {{
                border-color: {PRIMARY};
                background-color: {add_color_hover};
            }}
            QLabel {{
                font-size: 9pt;
                font-weight: normal;
                min-width: 40px;
                color: {text_color};
            }}
        """
        )

    def set_enabled(self, enabled: bool, tooltip: str = ""):
        """Enable/disable the footer controls."""
        self.qty_spinbox.setEnabled(enabled)
        self.body_color_combo.setEnabled(enabled)
        self.front_color_combo.setEnabled(enabled)
        self.body_add_color_btn.setEnabled(enabled)
        self.front_add_color_btn.setEnabled(enabled)
        self.handle_combo.setEnabled(enabled)
        self.add_button.setEnabled(enabled)

        if not enabled and tooltip:
            self.add_button.setToolTip(tooltip)
        else:
            self.add_button.setToolTip("")

    def values(self) -> tuple[int, dict]:
        """Get current quantity and options."""
        quantity = self.qty_spinbox.value()
        options = {
            "body_color": self.body_color_combo.currentText(),
            "front_color": self.front_color_combo.currentText(),
            "handle_type": self.handle_combo.currentText(),
        }
        return quantity, options

    def _open_add_color_dialog(self, target_combo: QComboBox) -> None:
        """Open dialog for adding a custom color entry."""
        if not self.color_service:
            return

        dialog = ColorEditDialog(self.color_service, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.created_color_name:
            self._load_color_controls()
            target_combo.setCurrentText(dialog.created_color_name)

    def _load_color_controls(self) -> None:
        """Populate recent-first color controls and searchable completers."""
        recent_names = self._recent_names()
        searchable_names = self._searchable_names()

        current_body = self.body_color_combo.currentText() or "Biały"
        current_front = self.front_color_combo.currentText() or "Biały"

        for combo in (self.body_color_combo, self.front_color_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(recent_names)
            combo.blockSignals(False)

            completer = QCompleter(searchable_names, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            combo.setCompleter(completer)

        self.body_color_combo.setCurrentText(current_body)
        self.front_color_combo.setCurrentText(current_front)

    def _recent_names(self) -> list[str]:
        if self.color_service:
            try:
                self.color_service.ensure_seeded()
                names = self.color_service.list_recent(limit=12)
                if names:
                    return names
            except Exception:
                pass
        return POPULAR_COLORS[:12]

    def _searchable_names(self) -> list[str]:
        if self.color_service:
            try:
                self.color_service.ensure_seeded()
                names = self.color_service.list_searchable_names()
                if names:
                    return names
            except Exception:
                pass
        return list(POPULAR_COLORS)
