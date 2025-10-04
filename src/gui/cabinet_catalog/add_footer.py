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
)
from PySide6.QtCore import Signal, QSize

from src.gui.resources.styles import get_theme, PRIMARY
from src.gui.resources.resources import get_icon


class AddFooter(QWidget):
    """Footer for adding cabinets to project."""

    # Signals
    sig_add_to_project = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()
        self._apply_styles()
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
        self.body_color_combo.addItems(["Biały", "Czarny", "Szary", "Dąb", "Orzech"])
        self.body_color_combo.setCurrentText("Biały")
        body_layout.addWidget(self.body_color_combo)
        options_layout.addLayout(body_layout)

        # Front color
        front_layout = QHBoxLayout()
        front_layout.addWidget(QLabel("Front:"))
        self.front_color_combo = QComboBox()
        self.front_color_combo.addItems(
            ["Biały", "Czarny", "Szary", "Dąb", "Orzech", "Lacobel"]
        )
        self.front_color_combo.setCurrentText("Biały")
        front_layout.addWidget(self.front_color_combo)
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

    def _apply_styles(self):
        """Apply styling to the footer."""
        self.setStyleSheet(
            get_theme()
            + f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 4px;
                background-color: #FAFAFA;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                background-color: #FAFAFA;
            }}
            QSpinBox {{
                padding: 4px;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                background-color: white;
                font-size: 10pt;
            }}
            QSpinBox:focus {{
                border-color: {PRIMARY};
            }}
            QComboBox {{
                padding: 4px;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                background-color: white;
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
                border: 1px solid #999999;
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
                background-color: #CCCCCC;
                color: #666666;
            }}
            QLabel {{
                font-size: 9pt;
                font-weight: normal;
                min-width: 40px;
            }}
        """
        )

    def set_enabled(self, enabled: bool, tooltip: str = ""):
        """Enable/disable the footer controls."""
        self.qty_spinbox.setEnabled(enabled)
        self.body_color_combo.setEnabled(enabled)
        self.front_color_combo.setEnabled(enabled)
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
