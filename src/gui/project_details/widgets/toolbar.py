"""
Toolbar widget for cabinet management actions.

This widget provides buttons and controls for adding cabinets, searching, and switching views.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QButtonGroup,
    QFrame,
    QToolButton,
)

from ..constants import (
    COLORS,
    VIEW_MODE_CARDS,
    VIEW_MODE_TABLE,
    TOOLBAR_HEIGHT,
    ICON_SIZE,
    CONTENT_MARGINS,
    LAYOUT_SPACING,
    SHORTCUTS,
    BUTTON_STYLESHEET,
    TOOLTIP_ADD_CATALOG,
    TOOLTIP_ADD_CUSTOM,
    TOOLTIP_VIEW_CARDS,
    TOOLTIP_VIEW_TABLE,
)

logger = logging.getLogger(__name__)


class Toolbar(QWidget):
    """
    Toolbar widget for cabinet management actions.

    Provides:
    - Add cabinet buttons ("Dodaj z listy", "Dodaj niestandardową")
    - Search functionality with clear button
    - View mode switching (cards/table) with segmented button group
    """

    # Signals
    sig_add_from_catalog = Signal()
    sig_add_custom = Signal()
    sig_search_changed = Signal(str)  # search_text
    sig_view_mode_changed = Signal(str)  # "cards" or "table"

    def __init__(self, parent=None):
        """Initialize the toolbar."""
        super().__init__(parent)
        self._current_view_mode = VIEW_MODE_CARDS

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the toolbar UI with modern styling and shortcuts."""
        self.setFixedHeight(TOOLBAR_HEIGHT)

        # Apply button stylesheet for all buttons
        self.setStyleSheet(BUTTON_STYLESHEET)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*CONTENT_MARGINS)
        layout.setSpacing(LAYOUT_SPACING)

        # Left side - Add buttons
        self._create_add_buttons(layout)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(separator)

        # Search box with Ctrl+F shortcut
        self._create_search_box(layout)

        layout.addStretch()

        # Right side - View mode toggle with keyboard shortcuts
        self._create_view_mode_toggle(layout)

    def _create_add_buttons(self, layout: QHBoxLayout) -> None:
        """Create the add cabinet buttons with modern styling."""
        # Add from catalog button
        self.add_catalog_btn = QPushButton("Dodaj z listy")
        self.add_catalog_btn.setToolTip(TOOLTIP_ADD_CATALOG)
        self.add_catalog_btn.setIconSize(ICON_SIZE)
        layout.addWidget(self.add_catalog_btn)

        # Add custom button
        self.add_custom_btn = QPushButton("Dodaj niestandardową")
        self.add_custom_btn.setToolTip(TOOLTIP_ADD_CUSTOM)
        self.add_custom_btn.setIconSize(ICON_SIZE)
        layout.addWidget(self.add_custom_btn)

    def _create_search_box(self, layout: QHBoxLayout) -> None:
        """Create the search input with clear button."""
        # Container for search with clear button
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        # Search input with Ctrl+F shortcut
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj szafek...")
        self.search_edit.setMinimumWidth(200)

        # Add shortcut for focusing search
        from PySide6.QtGui import QShortcut, QKeySequence

        self.search_shortcut = QShortcut(QKeySequence(SHORTCUTS["search_focus"]), self)
        self.search_shortcut.activated.connect(self.search_edit.setFocus)
        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
                padding: 6px 32px 6px 12px;
                font-size: 13px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {COLORS["accent"]};
            }}
        """)
        search_layout.addWidget(self.search_edit)

        # Clear button (positioned over the input)
        self.clear_btn = QToolButton()
        self.clear_btn.setText("×")
        self.clear_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                background: transparent;
                color: {COLORS["text_secondary"]};
                font-size: 16px;
                font-weight: bold;
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }}
            QToolButton:hover {{
                color: {COLORS["text_primary"]};
                background-color: {COLORS["hover"]};
                border-radius: 10px;
            }}
        """)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.hide()  # Initially hidden

        # Position clear button over search field
        search_layout.addWidget(self.clear_btn)
        search_layout.setContentsMargins(0, 0, 6, 0)

        layout.addWidget(search_container)

    def _create_view_mode_toggle(self, layout: QHBoxLayout) -> None:
        """Create the segmented view mode toggle."""
        # Container for segmented buttons
        toggle_container = QWidget()
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(0)

        # Button group for exclusive selection
        self.view_mode_group = QButtonGroup()

        # Cards button with Ctrl+1 shortcut
        self.cards_btn = QPushButton("Cards")
        self.cards_btn.setCheckable(True)
        self.cards_btn.setChecked(True)  # Default selected
        self.cards_btn.setShortcut(SHORTCUTS["view_cards"])
        self.cards_btn.setToolTip(f"{TOOLTIP_VIEW_CARDS} ({SHORTCUTS['view_cards']})")
        self.view_mode_group.addButton(self.cards_btn, 0)
        toggle_layout.addWidget(self.cards_btn)

        # Table button with Ctrl+2 shortcut
        self.table_btn = QPushButton("Table")
        self.table_btn.setCheckable(True)
        self.table_btn.setShortcut(SHORTCUTS["view_table"])
        self.table_btn.setToolTip(f"{TOOLTIP_VIEW_TABLE} ({SHORTCUTS['view_table']})")
        self.view_mode_group.addButton(self.table_btn, 1)
        toggle_layout.addWidget(self.table_btn)

        layout.addWidget(toggle_container)

    def _get_segmented_button_style(self, is_selected: bool, position: str) -> str:
        """Get the CSS style for segmented buttons."""
        bg_color = (
            COLORS["button_primary"] if is_selected else COLORS["button_secondary"]
        )
        text_color = "white" if is_selected else COLORS["text_primary"]

        # Border radius based on position
        if position == "left":
            border_radius = "border-radius: 4px 0 0 4px;"
        elif position == "right":
            border_radius = "border-radius: 0 4px 4px 0;"
        else:
            border_radius = "border-radius: 0;"

        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {COLORS["border"]};
                {border_radius}
                padding: 6px 16px;
                font-size: 12px;
                min-width: 60px;
            }}
            QPushButton:checked {{
                background-color: {COLORS["button_primary"]};
                color: white;
            }}
            QPushButton:hover:!checked {{
                background-color: {COLORS["button_hover"]};
            }}
        """

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Add buttons
        self.add_catalog_btn.clicked.connect(self.sig_add_from_catalog.emit)
        self.add_custom_btn.clicked.connect(self.sig_add_custom.emit)

        # Search
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.clear_btn.clicked.connect(self._clear_search)

        # View mode
        self.view_mode_group.buttonClicked.connect(self._on_view_mode_clicked)

    def _on_search_changed(self, text: str) -> None:
        """Handle search text changes."""
        # Show/hide clear button
        self.clear_btn.setVisible(bool(text.strip()))

        # Emit search signal
        self.sig_search_changed.emit(text)

    def _clear_search(self) -> None:
        """Clear the search field."""
        self.search_edit.clear()

    def _on_view_mode_clicked(self, button: QPushButton) -> None:
        """Handle view mode button clicks."""
        if button == self.cards_btn:
            mode = VIEW_MODE_CARDS
        else:
            mode = VIEW_MODE_TABLE

        if mode != self._current_view_mode:
            self._current_view_mode = mode
            self._update_button_styles()
            self.sig_view_mode_changed.emit(mode)

    def _update_button_styles(self) -> None:
        """Update button styles based on current selection."""
        cards_selected = self._current_view_mode == VIEW_MODE_CARDS
        table_selected = self._current_view_mode == VIEW_MODE_TABLE

        self.cards_btn.setStyleSheet(
            self._get_segmented_button_style(cards_selected, "left")
        )
        self.table_btn.setStyleSheet(
            self._get_segmented_button_style(table_selected, "right")
        )

    def set_view_mode(self, mode: str) -> None:
        """
        Set the current view mode.

        Args:
            mode: View mode ("cards" or "table")
        """
        if mode in (VIEW_MODE_CARDS, VIEW_MODE_TABLE):
            self._current_view_mode = mode

            # Update button states
            self.cards_btn.setChecked(mode == VIEW_MODE_CARDS)
            self.table_btn.setChecked(mode == VIEW_MODE_TABLE)

            self._update_button_styles()

    def get_current_view_mode(self) -> str:
        """Get the current view mode."""
        return self._current_view_mode

    def get_search_text(self) -> str:
        """Get the current search text."""
        return self.search_edit.text()

    def set_search_text(self, text: str) -> None:
        """Set the search text."""
        self.search_edit.setText(text)
