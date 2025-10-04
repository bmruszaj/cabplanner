"""
Preview panel for cabinet editor.

Shows cabinet image, key facts, and color swatches.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from src.gui.resources.resources import get_icon
from src.gui.resources.styles import get_theme, PRIMARY
from .validators import format_dimensions


class ColorChip(QWidget):
    """Small color chip widget."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(20, 20)
        self.setToolTip(f"Kolor: {color}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw color circle
        painter.setBrush(QColor(self.color))
        painter.setPen(QColor("#ddd"))
        painter.drawEllipse(2, 2, 16, 16)


class PreviewPanel(QWidget):
    """Preview panel showing cabinet image and key facts."""

    sig_change_preview = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cabinet_type = None
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        """Setup the user interface."""
        self.setFixedWidth(340)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title_label = QLabel("Podgląd")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Image section
        image_frame = QFrame()
        image_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(12, 12, 12, 12)

        # Image display
        self.image_label = QLabel()
        self.image_label.setFixedSize(280, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ddd;
                border-radius: 8px;
                background-color: #fafafa;
                color: #888;
            }
        """)
        self._show_placeholder()
        image_layout.addWidget(self.image_label)

        # Change preview button
        self.preview_button = QPushButton("Zmień podgląd...")
        self.preview_button.setIcon(get_icon("image"))
        self.preview_button.clicked.connect(self.sig_change_preview.emit)
        image_layout.addWidget(self.preview_button)

        layout.addWidget(image_frame)

        # Facts section
        facts_frame = QFrame()
        facts_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        facts_layout = QVBoxLayout(facts_frame)
        facts_layout.setContentsMargins(12, 12, 12, 12)

        facts_title = QLabel("Informacje")
        facts_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        facts_layout.addWidget(facts_title)

        # Name and SKU
        self.name_label = QLabel("—")
        self.name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        facts_layout.addWidget(self.name_label)

        self.sku_label = QLabel("SKU: —")
        self.sku_label.setStyleSheet("color: #666;")
        facts_layout.addWidget(self.sku_label)

        # Dimensions
        self.dimensions_label = QLabel("—")
        self.dimensions_label.setFont(QFont("Segoe UI", 9))
        facts_layout.addWidget(self.dimensions_label)

        # Color swatches section
        colors_label = QLabel("Domyślne kolory")
        colors_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        colors_label.setContentsMargins(0, 8, 0, 4)
        facts_layout.addWidget(colors_label)

        self.colors_layout = QHBoxLayout()
        self.colors_layout.setSpacing(6)
        facts_layout.addLayout(self.colors_layout)

        layout.addWidget(facts_frame)

        # Spacer
        layout.addStretch()

    def _apply_styles(self):
        """Apply visual styling."""
        get_theme()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY};
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY};
                opacity: 0.8;
            }}
        """)

    def _show_placeholder(self):
        """Show placeholder image."""
        self.image_label.setText("Brak podglądu")
        self.image_label.setPixmap(QPixmap())

    def _clear_colors(self):
        """Clear color swatches."""
        while self.colors_layout.count():
            child = self.colors_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_from(self, cabinet_type):
        """Update preview from cabinet type data."""
        self.cabinet_type = cabinet_type

        if not cabinet_type:
            self.name_label.setText("—")
            self.sku_label.setText("SKU: —")
            self.dimensions_label.setText("—")
            self._show_placeholder()
            self._clear_colors()
            return

        # Update name and SKU
        self.name_label.setText(getattr(cabinet_type, "nazwa", "") or "—")
        sku = getattr(cabinet_type, "sku", None) or ""
        self.sku_label.setText(f"SKU: {sku or '—'}")

        # Update dimensions - try various attribute names
        width = (
            getattr(cabinet_type, "width_mm", None)
            or getattr(cabinet_type, "bok_w_mm", 0)
            or 0
        )
        height = (
            getattr(cabinet_type, "height_mm", None)
            or getattr(cabinet_type, "bok_h_mm", 0)
            or 0
        )
        depth = getattr(cabinet_type, "depth_mm", None) or 560  # Standard depth
        self.dimensions_label.setText(format_dimensions(width, height, depth))

        # Update image (placeholder for now)
        self._show_placeholder()

        # Update color swatches
        self._clear_colors()

        # Add default colors if available
        body_color = getattr(cabinet_type, "default_body_color", None) or "#ffffff"
        front_color = getattr(cabinet_type, "default_front_color", None) or "#ffffff"

        if body_color:
            body_chip = ColorChip(body_color)
            body_label = QLabel("Korpus")
            body_label.setStyleSheet("color: #666; font-size: 8pt;")
            chip_layout = QVBoxLayout()
            chip_layout.setSpacing(2)
            chip_layout.addWidget(body_chip, alignment=Qt.AlignmentFlag.AlignCenter)
            chip_layout.addWidget(body_label, alignment=Qt.AlignmentFlag.AlignCenter)
            chip_widget = QWidget()
            chip_widget.setLayout(chip_layout)
            self.colors_layout.addWidget(chip_widget)

        if front_color and front_color != body_color:
            front_chip = ColorChip(front_color)
            front_label = QLabel("Front")
            front_label.setStyleSheet("color: #666; font-size: 8pt;")
            chip_layout = QVBoxLayout()
            chip_layout.setSpacing(2)
            chip_layout.addWidget(front_chip, alignment=Qt.AlignmentFlag.AlignCenter)
            chip_layout.addWidget(front_label, alignment=Qt.AlignmentFlag.AlignCenter)
            chip_widget = QWidget()
            chip_widget.setLayout(chip_layout)
            self.colors_layout.addWidget(chip_widget)

        self.colors_layout.addStretch()

    def set_preview_image(self, image_path: str):
        """Set preview image from file path."""
        if not image_path:
            self._show_placeholder()
            return

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale to fit while maintaining aspect ratio
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            self.image_label.setText("")
        else:
            self._show_placeholder()

    def clear(self):
        """Clear preview panel and show placeholder."""
        self._show_placeholder()
        self._clear_colors()
