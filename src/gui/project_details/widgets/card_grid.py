"""
Card Grid widget for displaying cabinet cards in a flow layout.

This widget manages a collection of cabinet cards with graceful wrapping and selection.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
)

from .cabinet_card import CabinetCard
from .empty_states import EmptyCardGrid, EmptySearchResults
from ..constants import COLORS

logger = logging.getLogger(__name__)


class FlowLayout(QVBoxLayout):
    """Custom layout that flows cards horizontally with wrapping."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.card_width = 200
        self.card_spacing = 12

    def addCard(self, card: CabinetCard) -> None:
        """Add a card to the flow layout."""
        # Find or create a row with space
        row_layout = None
        container_width = self.parentWidget().width() if self.parentWidget() else 800
        cards_per_row = max(
            1, (container_width - 32) // (self.card_width + self.card_spacing)
        )

        # Check existing rows for space
        for row in self.rows:
            if row.count() < cards_per_row:
                row_layout = row
                break

        # Create new row if needed
        if row_layout is None:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(self.card_spacing)
            row_layout.addStretch()  # Add stretch at the end

            self.addWidget(row_widget)
            self.rows.append(row_layout)

        # Insert card before the stretch
        row_layout.insertWidget(row_layout.count() - 1, card)

    def removeCard(self, card: CabinetCard) -> None:
        """Remove a card from the layout."""
        for row in self.rows:
            for i in range(row.count() - 1):  # -1 to skip stretch
                if row.itemAt(i).widget() == card:
                    row.removeWidget(card)
                    card.setParent(None)
                    return

    def clear(self) -> None:
        """Clear all cards from the layout."""
        while self.rows:
            row = self.rows.pop()
            while row.count() > 0:
                item = row.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            if row.parent():
                row.parent().setParent(None)


class CardGrid(QWidget):
    """
    Grid widget for displaying cabinet cards in a flow layout.

    Features:
    - Flow layout with graceful wrapping
    - Selection handling with visual feedback
    - Empty state display
    - Signal relay from cards
    """

    # Signals (relayed from cards)
    sig_card_selected = Signal(int)  # cab_id
    sig_qty_changed = Signal(int, int)  # cab_id, new_quantity
    sig_edit = Signal(int)  # cab_id
    sig_duplicate = Signal(int)  # cab_id
    sig_delete = Signal(int)  # cab_id

    def __init__(self, parent=None):
        """Initialize the card grid."""
        super().__init__(parent)
        self.cards: Dict[int, CabinetCard] = {}
        self.selected_card_id: Optional[int] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the card grid UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS["background"]};
            }}
            QScrollBar:vertical {{
                background-color: {COLORS["background"]};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS["border"]};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS["text_secondary"]};
            }}
        """)
        main_layout.addWidget(self.scroll_area)

        # Cards container
        self.cards_container = QWidget()
        self.cards_layout = FlowLayout(self.cards_container)
        self.cards_layout.setContentsMargins(16, 16, 16, 16)
        self.cards_layout.setSpacing(16)

        # Empty state - specialized for card grid
        self.empty_hint = EmptyCardGrid()
        self.empty_search_hint = None  # Will be created when needed
        self.cards_layout.addWidget(self.empty_hint)

        self.scroll_area.setWidget(self.cards_container)

    def set_cards(self, cards_data: List[Dict[str, Any]]) -> None:
        """
        Set the cards to display.

        Args:
            cards_data: List of cabinet data dictionaries
        """
        # Clear existing cards
        self.clear_cards()

        if not cards_data:
            self._show_empty_state()
            return

        self._hide_empty_state()

        # Add new cards
        for card_data in cards_data:
            cabinet_id = card_data.get("id", 0)
            card = CabinetCard(cabinet_id)
            card.set_data(card_data)

            # Connect signals
            card.sig_selected.connect(self._on_card_selected)
            card.sig_qty_changed.connect(self.sig_qty_changed.emit)
            card.sig_edit.connect(self.sig_edit.emit)
            card.sig_duplicate.connect(self.sig_duplicate.emit)
            card.sig_delete.connect(self.sig_delete.emit)

            self.cards[cabinet_id] = card
            self.cards_layout.addCard(card)

        logger.debug(f"Added {len(cards_data)} cards to grid")

    def add_card(self, card_data: Dict[str, Any]) -> None:
        """
        Add a single card.

        Args:
            card_data: Cabinet data dictionary
        """
        self._hide_empty_state()

        cabinet_id = card_data.get("id", 0)
        card = CabinetCard(cabinet_id)
        card.set_data(card_data)

        # Connect signals
        card.sig_selected.connect(self._on_card_selected)
        card.sig_qty_changed.connect(self.sig_qty_changed.emit)
        card.sig_edit.connect(self.sig_edit.emit)
        card.sig_duplicate.connect(self.sig_duplicate.emit)
        card.sig_delete.connect(self.sig_delete.emit)

        self.cards[cabinet_id] = card
        self.cards_layout.addCard(card)

        logger.debug(f"Added card for cabinet {cabinet_id}")

    def remove_card(self, cabinet_id: int) -> None:
        """
        Remove a card by cabinet ID.

        Args:
            cabinet_id: The cabinet ID to remove
        """
        if cabinet_id in self.cards:
            card = self.cards.pop(cabinet_id)
            self.cards_layout.removeCard(card)

            # Clear selection if this card was selected
            if self.selected_card_id == cabinet_id:
                self.selected_card_id = None

            # Show empty state if no cards left
            if not self.cards:
                self._show_empty_state()

            logger.debug(f"Removed card for cabinet {cabinet_id}")

    def update_card(self, cabinet_id: int, card_data: Dict[str, Any]) -> None:
        """
        Update an existing card.

        Args:
            cabinet_id: The cabinet ID to update
            card_data: New cabinet data
        """
        if cabinet_id in self.cards:
            self.cards[cabinet_id].set_data(card_data)
            logger.debug(f"Updated card for cabinet {cabinet_id}")

    def clear_cards(self) -> None:
        """Clear all cards."""
        self.cards.clear()
        self.selected_card_id = None
        self.cards_layout.clear()
        self._show_empty_state()

    def select_card(self, cabinet_id: int) -> None:
        """
        Select a card by cabinet ID.

        Args:
            cabinet_id: The cabinet ID to select
        """
        # Deselect current selection
        if self.selected_card_id and self.selected_card_id in self.cards:
            self.cards[self.selected_card_id].set_selected(False)

        # Select new card
        if cabinet_id in self.cards:
            self.selected_card_id = cabinet_id
            self.cards[cabinet_id].set_selected(True)
            self.sig_card_selected.emit(cabinet_id)
        else:
            self.selected_card_id = None

    def clear_selection(self) -> None:
        """Clear the current selection."""
        if self.selected_card_id and self.selected_card_id in self.cards:
            self.cards[self.selected_card_id].set_selected(False)
        self.selected_card_id = None

    def get_selected_card_id(self) -> Optional[int]:
        """Get the currently selected card ID."""
        return self.selected_card_id

    def _on_card_selected(self, cabinet_id: int) -> None:
        """Handle card selection."""
        self.select_card(cabinet_id)

    def _show_empty_state(self, search_term: str = "") -> None:
        """
        Show the appropriate empty state.

        Args:
            search_term: If provided, shows search-specific empty state
        """
        # Hide any existing empty states
        self.empty_hint.hide()
        if self.empty_search_hint:
            self.empty_search_hint.hide()

        if search_term:
            # Show search-specific empty state
            if not self.empty_search_hint:
                self.empty_search_hint = EmptySearchResults(search_term)
                self.cards_layout.addWidget(self.empty_search_hint)
            else:
                self.empty_search_hint.set_message(
                    f"Brak wyników dla '{search_term}'\nSpróbuj zmienić kryteria wyszukiwania"
                )
            self.empty_search_hint.show()
        else:
            # Show general empty state
            self.empty_hint.show()

    def _hide_empty_state(self) -> None:
        """Hide all empty state hints."""
        self.empty_hint.hide()
        if self.empty_search_hint:
            self.empty_search_hint.hide()

    def update_search_filter(self, search_term: str) -> None:
        """
        Update search filter and empty state accordingly.

        Args:
            search_term: Current search term
        """
        # If no cards are visible and there's a search term, show search empty state
        visible_cards = sum(1 for card in self.cards.values() if card.isVisible())

        if visible_cards == 0:
            self._show_empty_state(search_term if search_term.strip() else "")
        else:
            self._hide_empty_state()

    def get_card_count(self) -> int:
        """Get the number of cards."""
        return len(self.cards)

    def resizeEvent(self, event) -> None:
        """Handle resize to reflow cards."""
        super().resizeEvent(event)
        # The FlowLayout will handle reflowing automatically
        # based on the new container width
