"""Cabinet type card widget for grid view."""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
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

        # Calculate dimensions from parts
        width = height = depth = 0
        parts_count = 0

        if hasattr(self.cabinet_type, "parts") and self.cabinet_type.parts:
            parts_count = len(self.cabinet_type.parts)
            # Calculate max dimensions from parts
            for part in self.cabinet_type.parts:
                if hasattr(part, "width_mm") and part.width_mm:
                    width = max(width, part.width_mm)
                if hasattr(part, "height_mm") and part.height_mm:
                    height = max(height, part.height_mm)
                if hasattr(part, "depth_mm") and part.depth_mm:
                    depth = max(depth, part.depth_mm)

        # Display dimensions and parts count
        if width > 0 and height > 0:
            dimensions_text = f"{width} × {height}"
            if depth > 0:
                dimensions_text += f" × {depth}"
            dimensions_text += " mm"
        else:
            dimensions_text = "Brak wymiarów"

        dimensions_label = QLabel(dimensions_text)
        details_layout.addRow("Wymiary:", dimensions_label)

        parts_label = QLabel(f"{parts_count} części")
        details_layout.addRow("Części:", parts_label)

        layout.addLayout(details_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        edit_btn = QPushButton("Edytuj")
        edit_btn.setProperty("class", "secondary")
        edit_btn.setIcon(get_icon("edit_white"))
        edit_btn.clicked.connect(lambda: self.clicked.emit(self.cabinet_type))
        button_layout.addWidget(edit_btn)
        layout.addLayout(button_layout)

        layout.addStretch()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        """Handle mouse press events to emit clicked signal."""
        super().mousePressEvent(event)
        self.clicked.emit(self.cabinet_type)
