"""Cabinet type card widget for grid view."""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from src.gui.resources.resources import get_icon
from src.gui.utils.ui_bits import dot


class CabinetTypeCard(QFrame):
    """A card widget displaying cabinet type information"""

    clicked = Signal(object)  # Signal emits the cabinet type object

    def __init__(self, cabinet_type: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.cabinet_type = cabinet_type
        self.setObjectName("cabinetTypeCard")
        self.setProperty("class", "card")
        self.setFixedHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(f"Typ szafki {self.cabinet_type.nazwa}")
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the card UI."""
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{self.cabinet_type.nazwa}</b>")
        name_label.setStyleSheet("font-size: 14pt;")
        header_layout.addWidget(name_label)

        kitchen_type_label = QLabel(self.cabinet_type.kitchen_type)
        kitchen_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(kitchen_type_label)
        layout.addLayout(header_layout)

        details_layout = QFormLayout()
        details_layout.setHorizontalSpacing(20)
        details_layout.setVerticalSpacing(5)

        components_label = QLabel(
            f"Boki: {self.cabinet_type.bok_count}, "
            f"Wieńce: {self.cabinet_type.wieniec_count}, "
            f"Półki: {self.cabinet_type.polka_count}, "
            f"Fronty: {self.cabinet_type.front_count}, "
            f"Listwy: {self.cabinet_type.listwa_count}"
        )
        components_label.setWordWrap(True)
        details_layout.addRow("Komponenty:", components_label)

        hdf_value = "Tak" if self.cabinet_type.hdf_plecy else "Nie"
        hdf_label = QLabel(hdf_value)
        hdf_label.setPixmap(
            dot(QColor("#2ecc71") if self.cabinet_type.hdf_plecy else QColor("#e74c3c"))
        )
        details_layout.addRow("Plecy HDF:", hdf_label)

        layout.addLayout(details_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        edit_btn = QPushButton("Edytuj")
        edit_btn.setProperty("class", "secondary")
        edit_btn.setIcon(get_icon("edit"))
        edit_btn.clicked.connect(lambda: self.clicked.emit(self.cabinet_type))
        button_layout.addWidget(edit_btn)
        layout.addLayout(button_layout)

        layout.addStretch()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """Handle mouse press events to emit clicked signal."""
        super().mousePressEvent(event)
        self.clicked.emit(self.cabinet_type)
