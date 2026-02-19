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
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        # Left section: Add buttons
        self._create_add_buttons(layout)

        # Add stretch before view toggle to push it to the right
        layout.addStretch()

        # Right section: View mode toggle
        self._create_view_toggle(layout)

    def _create_add_buttons(self, parent_layout: QHBoxLayout):
        """Create the add buttons section."""
        # Add from catalog button - uses default primary style from global theme
        self.add_catalog_btn = QPushButton("Katalog")
        self.add_catalog_btn.setIcon(get_icon("catalog_white"))
        self.add_catalog_btn.setIconSize(ICON_SIZE)
        self.add_catalog_btn.setToolTip("Dodaj z katalogu")
        self.add_catalog_btn.clicked.connect(self.sig_add_from_catalog.emit)
        parent_layout.addWidget(self.add_catalog_btn)

        # Add custom button
        self.add_custom_btn = QPushButton("Niestandardowa")
        self.add_custom_btn.setIcon(get_icon("cabinet_white"))
        self.add_custom_btn.setIconSize(ICON_SIZE)
        self.add_custom_btn.setToolTip("Dodaj niestandardową szafkę")
        self.add_custom_btn.clicked.connect(self.sig_add_custom.emit)
        parent_layout.addWidget(self.add_custom_btn)
        # Keep both action buttons equal width and prevent text clipping.
        shared_min_width = max(
            self.add_catalog_btn.sizeHint().width(),
            self.add_custom_btn.sizeHint().width(),
        )
        self.add_catalog_btn.setMinimumWidth(shared_min_width)
        self.add_custom_btn.setMinimumWidth(shared_min_width)

    def _create_view_toggle(self, parent_layout: QHBoxLayout):
        """Create the view mode toggle buttons."""
        # Container for toggle buttons
        toggle_widget = QWidget()
        toggle_layout = QHBoxLayout(toggle_widget)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(2)

        # Cards view button - uses secondary style
        self.cards_btn = QPushButton("Karty")
        self.cards_btn.setIcon(get_icon("dashboard"))
        self.cards_btn.setIconSize(ICON_SIZE)
        self.cards_btn.setProperty("class", "secondary")
        self.cards_btn.setCheckable(True)
        self.cards_btn.setChecked(True)
        self.cards_btn.setToolTip("Widok kart")
        self.cards_btn.clicked.connect(lambda: self._set_view_mode(VIEW_MODE_CARDS))
        toggle_layout.addWidget(self.cards_btn)

        # Table view button - uses secondary style
        self.table_btn = QPushButton("Tabela")
        self.table_btn.setIcon(get_icon("table"))  # Using table icon (mapped to menu)
        self.table_btn.setIconSize(ICON_SIZE)
        self.table_btn.setProperty("class", "secondary")
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
        # Only style the toolbar container
        # Button styles (primary/secondary) come from global theme
        self.setStyleSheet("""
            Toolbar {
                border-bottom: 1px solid palette(mid);
            }
        """)
