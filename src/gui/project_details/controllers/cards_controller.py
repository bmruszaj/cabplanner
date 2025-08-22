"""
Cards Controller for cabinet card grid management.

This controller handles the specific UX patterns for the card-based cabinet view,
managing card creation, signals, and integration with the main controller.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Callable, Dict, Any, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

# Import widgets
from ..widgets import CabinetCard, CardGrid, EmptyCardGrid

if TYPE_CHECKING:
    from src.db_schema.orm_models import ProjectCabinet

logger = logging.getLogger(__name__)


class CardsController(QObject):
    """
    Controller for cabinet card grid interactions.

    This controller manages:
    - Creating CabinetCard widgets for each cabinet DTO
    - Connecting card signals to main controller callbacks
    - Maintaining card selection state
    - Showing empty state when no cabinets
    - Optional table selection sync (future scope)
    """

    # Signals for main controller communication
    selection_changed = Signal(list)  # List of selected cabinet IDs

    def __init__(
        self,
        card_grid: CardGrid,
        qty_changed_callback: Callable[[int, int], None],
        edit_callback: Callable[[int], None],
        duplicate_callback: Callable[[int], None],
        delete_callback: Callable[[int], None],
        selection_callback: Optional[Callable[[int], None]] = None,
        parent=None,
    ):
        """
        Initialize the cards controller.

        Args:
            card_grid: The CardGrid widget to manage
            qty_changed_callback: Callback for quantity changes (cabinet_id, new_qty)
            edit_callback: Callback for edit requests (cabinet_id)
            duplicate_callback: Callback for duplicate requests (cabinet_id)
            delete_callback: Callback for delete requests (cabinet_id)
            selection_callback: Optional callback for selection changes (cabinet_id)
            parent: Parent QObject
        """
        super().__init__(parent)

        self.card_grid = card_grid
        self.qty_changed_callback = qty_changed_callback
        self.edit_callback = edit_callback
        self.duplicate_callback = duplicate_callback
        self.delete_callback = delete_callback
        self.selection_callback = selection_callback

        # State tracking
        self._cabinets: List[ProjectCabinet] = []
        self._cabinet_cards: Dict[int, CabinetCard] = {}  # cabinet_id -> CabinetCard
        self._selected_cabinet_ids: set[int] = set()

        logger.debug("Initialized CardsController with callbacks")

    def set_cabinets(self, cabinets: List[ProjectCabinet]) -> None:
        """
        Set the list of cabinets and create cards.

        Args:
            cabinets: List of project cabinets to display
        """
        self._cabinets = cabinets
        self._selected_cabinet_ids.clear()

        # Clear existing cards
        self.card_grid.clear_cards()
        self._cabinet_cards.clear()

        if not cabinets:
            # Show empty state
            self._show_empty_state()
        else:
            # Create cards for all cabinets
            self._create_cabinet_cards()

        logger.debug(f"Set {len(cabinets)} cabinets in cards controller")

    def _show_empty_state(self) -> None:
        """Show empty state when no cabinets."""
        empty_widget = EmptyCardGrid()
        self.card_grid.set_empty_state(empty_widget)
        logger.debug("Showing empty cabinet state")

    def _create_cabinet_cards(self) -> None:
        """Create CabinetCard widgets for all cabinets."""
        for cabinet in self._cabinets:
            try:
                card = self._create_cabinet_card(cabinet)
                self._cabinet_cards[cabinet.id] = card
                self.card_grid.add_card(card)

            except Exception as e:
                logger.error(f"Error creating card for cabinet {cabinet.id}: {e}")

    def _create_cabinet_card(self, cabinet: ProjectCabinet) -> CabinetCard:
        """
        Create a CabinetCard widget for a cabinet.

        Args:
            cabinet: Cabinet data to create card for

        Returns:
            Configured CabinetCard widget
        """
        # Create cabinet card with data
        card = CabinetCard()

        # Set cabinet data
        card.set_cabinet_data(
            {
                "id": cabinet.id,
                "name": cabinet.cabinet_type.nazwa
                if cabinet.cabinet_type
                else "Niestandardowy",
                "body_color": cabinet.body_color or "Nie określono",
                "front_color": cabinet.front_color or "Nie określono",
                "handle_type": cabinet.handle_type or "Nie określono",
                "quantity": cabinet.quantity or 1,
                "is_custom": cabinet.type_id is None,
                "sequence": cabinet.sequence_number or 0,
            }
        )

        # Connect card signals to controller handlers
        card.sig_qty_changed.connect(self._handle_qty_changed)
        card.sig_edit.connect(self._handle_edit)
        card.sig_duplicate.connect(self._handle_duplicate)
        card.sig_delete.connect(self._handle_delete)
        card.sig_selected.connect(self._handle_selection)

        logger.debug(f"Created card for cabinet {cabinet.id}")
        return card

    def _handle_qty_changed(self, cabinet_id: int, new_quantity: int) -> None:
        """
        Handle quantity change from a card.

        Args:
            cabinet_id: ID of cabinet whose quantity changed
            new_quantity: New quantity value
        """
        try:
            # Update local cabinet data
            for cabinet in self._cabinets:
                if cabinet.id == cabinet_id:
                    old_quantity = cabinet.quantity
                    cabinet.quantity = new_quantity
                    logger.debug(
                        f"Updated local cabinet {cabinet_id} quantity: {old_quantity} -> {new_quantity}"
                    )
                    break

            # Call main controller callback for persistence
            self.qty_changed_callback(cabinet_id, new_quantity)

        except Exception as e:
            logger.error(
                f"Error handling quantity change for cabinet {cabinet_id}: {e}"
            )

    def _handle_edit(self, cabinet_id: int) -> None:
        """
        Handle edit request from a card.

        Args:
            cabinet_id: ID of cabinet to edit
        """
        try:
            self.edit_callback(cabinet_id)
            logger.debug(f"Requested edit for cabinet {cabinet_id}")

        except Exception as e:
            logger.error(f"Error handling edit request for cabinet {cabinet_id}: {e}")

    def _handle_duplicate(self, cabinet_id: int) -> None:
        """
        Handle duplicate request from a card.

        Args:
            cabinet_id: ID of cabinet to duplicate
        """
        try:
            self.duplicate_callback(cabinet_id)
            logger.debug(f"Requested duplicate for cabinet {cabinet_id}")

        except Exception as e:
            logger.error(
                f"Error handling duplicate request for cabinet {cabinet_id}: {e}"
            )

    def _handle_delete(self, cabinet_id: int) -> None:
        """
        Handle delete request from a card.

        Args:
            cabinet_id: ID of cabinet to delete
        """
        try:
            self.delete_callback(cabinet_id)
            logger.debug(f"Requested delete for cabinet {cabinet_id}")

        except Exception as e:
            logger.error(f"Error handling delete request for cabinet {cabinet_id}: {e}")

    def _handle_selection(self, cabinet_id: int) -> None:
        """
        Handle selection change from a card.

        Args:
            cabinet_id: ID of selected cabinet
        """
        try:
            # Update selection state
            if cabinet_id in self._selected_cabinet_ids:
                self._selected_cabinet_ids.remove(cabinet_id)
            else:
                self._selected_cabinet_ids.add(cabinet_id)

            # Emit selection change
            self.selection_changed.emit(list(self._selected_cabinet_ids))

            # Call optional selection callback
            if self.selection_callback:
                self.selection_callback(cabinet_id)

            logger.debug(
                f"Selection changed: cabinet {cabinet_id}, total selected: {len(self._selected_cabinet_ids)}"
            )

        except Exception as e:
            logger.error(f"Error handling selection for cabinet {cabinet_id}: {e}")

    def refresh_cards(self) -> None:
        """Refresh all cards with current cabinet data."""
        try:
            for cabinet in self._cabinets:
                if cabinet.id in self._cabinet_cards:
                    card = self._cabinet_cards[cabinet.id]

                    # Update card data
                    card.set_cabinet_data(
                        {
                            "id": cabinet.id,
                            "name": cabinet.cabinet_type.nazwa
                            if cabinet.cabinet_type
                            else "Niestandardowy",
                            "body_color": cabinet.body_color or "Nie określono",
                            "front_color": cabinet.front_color or "Nie określono",
                            "handle_type": cabinet.handle_type or "Nie określono",
                            "quantity": cabinet.quantity or 1,
                            "is_custom": cabinet.type_id is None,
                            "sequence": cabinet.sequence_number or 0,
                        }
                    )

            logger.debug("Refreshed all cabinet cards")

        except Exception as e:
            logger.error(f"Error refreshing cards: {e}")

    def get_selected_cabinets(self) -> List[ProjectCabinet]:
        """
        Get currently selected cabinets.

        Returns:
            List of selected cabinet objects
        """
        return [
            cabinet
            for cabinet in self._cabinets
            if cabinet.id in self._selected_cabinet_ids
        ]

    def select_cabinet(self, cabinet_id: int, multi_select: bool = False) -> None:
        """
        Programmatically select a cabinet card.

        Args:
            cabinet_id: ID of cabinet to select
            multi_select: Whether to add to existing selection
        """
        if not multi_select:
            self._selected_cabinet_ids.clear()
            # Clear visual selection on all cards
            for card in self._cabinet_cards.values():
                card.set_selected(False)

        self._selected_cabinet_ids.add(cabinet_id)

        # Set visual selection on the card
        if cabinet_id in self._cabinet_cards:
            self._cabinet_cards[cabinet_id].set_selected(True)

        self.selection_changed.emit(list(self._selected_cabinet_ids))
        logger.debug(f"Programmatically selected cabinet {cabinet_id}")

    def clear_selection(self) -> None:
        """Clear all card selections."""
        self._selected_cabinet_ids.clear()

        # Clear visual selection on all cards
        for card in self._cabinet_cards.values():
            card.set_selected(False)

        self.selection_changed.emit([])
        logger.debug("Cleared all card selections")

    def get_selection_count(self) -> int:
        """Get the number of selected cards."""
        return len(self._selected_cabinet_ids)

    def is_cabinet_selected(self, cabinet_id: int) -> bool:
        """
        Check if a cabinet is selected.

        Args:
            cabinet_id: ID of cabinet to check

        Returns:
            True if cabinet is selected
        """
        return cabinet_id in self._selected_cabinet_ids

    def sync_selection_from_table(self, selected_cabinet_ids: List[int]) -> None:
        """
        Sync selection state from table view (optional feature).

        Args:
            selected_cabinet_ids: List of cabinet IDs selected in table
        """
        try:
            # Clear current selection visually
            for card in self._cabinet_cards.values():
                card.set_selected(False)

            # Update selection state
            self._selected_cabinet_ids = set(selected_cabinet_ids)

            # Set visual selection on relevant cards
            for cabinet_id in selected_cabinet_ids:
                if cabinet_id in self._cabinet_cards:
                    self._cabinet_cards[cabinet_id].set_selected(True)

            logger.debug(
                f"Synced selection from table: {len(selected_cabinet_ids)} cabinets"
            )

        except Exception as e:
            logger.error(f"Error syncing selection from table: {e}")

    def update_cabinet_totals(self) -> Dict[str, Any]:
        """
        Calculate and return cabinet totals for display.

        Returns:
            Dictionary with total counts and other summary data
        """
        try:
            total_cabinets = len(self._cabinets)
            total_quantity = sum(cabinet.quantity or 0 for cabinet in self._cabinets)
            custom_count = sum(
                1 for cabinet in self._cabinets if cabinet.type_id is None
            )
            catalog_count = total_cabinets - custom_count

            totals = {
                "total_cabinets": total_cabinets,
                "total_quantity": total_quantity,
                "custom_count": custom_count,
                "catalog_count": catalog_count,
                "selected_count": len(self._selected_cabinet_ids),
            }

            logger.debug(f"Calculated cabinet totals: {totals}")
            return totals

        except Exception as e:
            logger.error(f"Error calculating cabinet totals: {e}")
            return {}

    def has_cabinets(self) -> bool:
        """Check if there are any cabinets to display."""
        return len(self._cabinets) > 0
