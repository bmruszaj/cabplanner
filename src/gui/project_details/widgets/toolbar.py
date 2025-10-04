"""
Toolbar Widget

A modern toolbar with view mode controls, add buttons, and sort functionality.
Provides intuitive access to main project cabinet management actions.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Signal

from src.gui.resources.resources import get_icon
from ..constants import TOOLBAR_HEIGHT, ICON_SIZE, VIEW_MODE_CARDS, VIEW_MODE_TABLE


class Toolbar(QWidget):
    """
    Modern toolbar widget with view mode controls and actions.

    Layout:
    - Left: Add buttons ("Dodaj z listy", "Dodaj niestandardową")
    - Middle: Sort button
    - Right: View mode toggle chips ("Karty", "Tabela")
    """

    sig_add_from_catalog = Signal()
    sig_add_custom = Signal()
    sig_view_mode_changed = Signal(str)
    sig_sort_by_sequence = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_view_mode = VIEW_MODE_CARDS
        self._setup_ui()
        self._apply_styling()

    def _setup_ui(self):
        """Set up the toolbar UI layout."""
        self.setMinimumHeight(TOOLBAR_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setProperty("class", "toolbar")

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        # Left section: Add buttons
        self._create_add_buttons(layout)

        # Middle section: Sort button
        self._create_sort_button(layout)

        # Add stretch before view toggle to push it to the right
        layout.addStretch()

        # Right section: View mode toggle
        self._create_view_toggle(layout)

    def _create_add_buttons(self, parent_layout: QHBoxLayout):
        """Create the add buttons section."""
        # Add from catalog button
        self.add_catalog_btn = QPushButton("Katalog")
        self.add_catalog_btn.setIcon(get_icon("catalog"))
        self.add_catalog_btn.setIconSize(ICON_SIZE)
        self.add_catalog_btn.setProperty("class", "primary-btn")
        self.add_catalog_btn.setToolTip("Dodaj z katalogu")
        self.add_catalog_btn.clicked.connect(self.sig_add_from_catalog.emit)
        parent_layout.addWidget(self.add_catalog_btn)

        # Add custom button
        self.add_custom_btn = QPushButton("Niestandardowa")
        self.add_custom_btn.setIcon(get_icon("add"))
        self.add_custom_btn.setIconSize(ICON_SIZE)
        self.add_custom_btn.setProperty("class", "secondary")
        self.add_custom_btn.setToolTip("Dodaj niestandardową szafkę")
        self.add_custom_btn.clicked.connect(self.sig_add_custom.emit)
        parent_layout.addWidget(self.add_custom_btn)

    def _create_sort_button(self, parent_layout: QHBoxLayout):
        """Create the sort button."""
        self.sort_btn = QPushButton("Sortuj")
        self.sort_btn.setIcon(get_icon("filter"))  # Using filter icon for sort
        self.sort_btn.setIconSize(ICON_SIZE)
        self.sort_btn.setProperty("class", "secondary")
        self.sort_btn.setToolTip("Sortuj według sekwencji")
        self.sort_btn.clicked.connect(self.sig_sort_by_sequence.emit)
        parent_layout.addWidget(self.sort_btn)

    def _create_view_toggle(self, parent_layout: QHBoxLayout):
        """Create the view mode toggle buttons."""
        # Container for toggle buttons
        toggle_widget = QWidget()
        toggle_layout = QHBoxLayout(toggle_widget)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(2)

        # Cards view button
        self.cards_btn = QPushButton("Karty")
        self.cards_btn.setIcon(get_icon("dashboard"))
        self.cards_btn.setIconSize(ICON_SIZE)
        self.cards_btn.setProperty("class", "toggle-btn")
        self.cards_btn.setCheckable(True)
        self.cards_btn.setChecked(True)
        self.cards_btn.setToolTip("Widok kart")
        self.cards_btn.clicked.connect(lambda: self._set_view_mode(VIEW_MODE_CARDS))
        toggle_layout.addWidget(self.cards_btn)

        # Table view button
        self.table_btn = QPushButton("Tabela")
        self.table_btn.setIcon(get_icon("table"))  # Using table icon (mapped to menu)
        self.table_btn.setIconSize(ICON_SIZE)
        self.table_btn.setProperty("class", "toggle-btn")
        self.table_btn.setCheckable(True)
        self.table_btn.setToolTip("Widok tabeli")
        self.table_btn.clicked.connect(lambda: self._set_view_mode(VIEW_MODE_TABLE))
        toggle_layout.addWidget(self.table_btn)

        parent_layout.addWidget(toggle_widget)

    def _set_view_mode(self, mode: str):
        """Set the current view mode."""
        self.current_view_mode = mode

        # Update button states
        self.cards_btn.setChecked(mode == VIEW_MODE_CARDS)
        self.table_btn.setChecked(mode == VIEW_MODE_TABLE)

        # Emit signal
        self.sig_view_mode_changed.emit(mode)

    def set_view_mode(self, mode: str):
        """Set the view mode programmatically without emitting signal."""
        self.current_view_mode = mode
        self.cards_btn.setChecked(mode == VIEW_MODE_CARDS)
        self.table_btn.setChecked(mode == VIEW_MODE_TABLE)

    def _apply_styling(self):
        """Apply styling to the toolbar."""
        self.setStyleSheet("""
            Toolbar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
            QPushButton[class="primary-btn"] {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton[class="primary-btn"]:hover {
                background-color: #106ebe;
            }
            QPushButton[class="toggle-btn"] {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 6px 12px;
                color: #374151;
                min-width: 60px;
            }
            QPushButton[class="toggle-btn"]:checked {
                background-color: #0078d4;
                color: white;
                border-color: #0078d4;
            }
            QPushButton[class="toggle-btn"]:hover {
                background-color: #e5e7eb;
            }
            QPushButton[class="toggle-btn"]:checked:hover {
                background-color: #106ebe;
            }
        """)
