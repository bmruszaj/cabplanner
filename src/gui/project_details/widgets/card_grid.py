"""
Responsive card grid widget for Project Details with shopping-cart experience.
Displays cabinet cards in a flow layout that adapts to container width.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QFrame,
    QSizePolicy,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .cabinet_card import CabinetCard
from ..constants import CARD_GRID_SPACING
from src.gui.layouts.flow_layout import FlowLayout


class EmptyStateWidget(QWidget):
    """Widget shown when no cabinets are added to project."""

    # Signal for when the add button is clicked
    add_cabinet_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Icon placeholder
        icon_label = QLabel("📋")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("color: #94a3b8;")

        # Title
        title = QLabel("Brak elementów")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Medium)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #475569; margin-bottom: 8px;")

        # Subtitle
        subtitle = QLabel("Dodaj szafki aby rozpocząć planowanie projektu")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-size: 14px;")

        # CTA Button
        add_button = QPushButton("Dodaj z katalogu")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        add_button.clicked.connect(self.add_cabinet_requested.emit)

        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(add_button)


class CardGrid(QWidget):
    """
    Responsive grid widget that displays cabinet cards in a shopping-cart style layout.
    Features:
    - Flow layout that wraps cards to new rows based on width
    - Search filtering with smooth animations
    - Empty state when no cabinets
    - Selection management for bulk operations
    """

    # Signals
    sig_qty_changed = Signal(int, int)  # cabinet_id, new_quantity
    sig_edit = Signal(int)  # Cabinet edit request
    sig_duplicate = Signal(int)  # Cabinet duplicate request
    sig_delete = Signal(int)  # Cabinet delete request
    sig_card_selected = Signal(int)  # cabinet_id selection
    sig_sequence_changed = Signal(int, int)  # cabinet_id, new_sequence_number
    sig_add_from_catalog = Signal()  # Add from catalog request (from empty state)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cabinet_cards = {}  # cabinet_id -> CabinetCard
        self._search_filter = ""
        self._setup_ui()

    def _setup_ui(self):
        """Initialize the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        # Main vertical layout for content (cards + button)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Cards container with flow layout
        self.cards_container = QWidget()
        self.flow_layout = FlowLayout(
            self.cards_container, margin=8, spacing=CARD_GRID_SPACING
        )
        self.cards_container.setLayout(self.flow_layout)
        content_layout.addWidget(self.cards_container)

        # Add button at the bottom of cards - uses global theme primary style
        self.add_catalog_btn = QPushButton("+ Dodaj z katalogu")
        self.add_catalog_btn.clicked.connect(self.sig_add_from_catalog.emit)
        content_layout.addWidget(self.add_catalog_btn, 0, Qt.AlignmentFlag.AlignLeft)

        # Empty state widget
        self.empty_state = EmptyStateWidget()
        self.empty_state.add_cabinet_requested.connect(self.sig_add_from_catalog.emit)

        # Initially show empty state
        self.scroll_area.setWidget(self.empty_state)
        main_layout.addWidget(self.scroll_area)

    def add_card(self, cabinet_data):
        """
        Add a new cabinet card to the grid.

        Args:
            cabinet_data: Dictionary with cabinet information
                - id: Cabinet ID
                - name: Cabinet name
                - body_color: Body color
                - front_color: Front color
                - handle_type: Handle type
                - quantity: Current quantity
                - sequence: Order in project
        """
        cabinet_id = cabinet_data["id"]

        # Don't add duplicates
        if cabinet_id in self._cabinet_cards:
            return

        # Create card widget with explicit parent to avoid stray windows
        card = CabinetCard(cabinet_data, parent=self.content_widget)

        # Set up sequence validation to prevent duplicates
        card.sequence_input.set_validation_callback(self._validate_sequence_number)

        # Connect signals
        card.sig_qty_changed.connect(self.sig_qty_changed)
        card.sig_edit.connect(self.sig_edit)
        card.sig_duplicate.connect(self.sig_duplicate)
        card.sig_delete.connect(self.sig_delete)
        card.sig_selected.connect(self._on_card_selected)  # Handle single selection
        card.sig_sequence_changed.connect(self.sig_sequence_changed)

        # Store reference
        self._cabinet_cards[cabinet_id] = card

        # Switch to card view if this is first card
        if len(self._cabinet_cards) == 1:
            self._switch_to_card_view()

        # Add to layout
        self.flow_layout.addCard(card)

        # Apply current search filter
        self._apply_search_filter()

    def _on_card_selected(self, cabinet_id: int):
        """Handle card selection - implement single selection behavior."""
        # Clear selection from all other cards
        for card_id, card in self._cabinet_cards.items():
            if card_id != cabinet_id:
                card.set_selected(False)

        # Toggle selection on the clicked card
        clicked_card = self._cabinet_cards.get(cabinet_id)
        if clicked_card:
            clicked_card.set_selected(not clicked_card.is_card_selected())

        # Emit the selection signal
        self.sig_card_selected.emit(cabinet_id)

    def add_cabinet_card(self, cabinet_data):
        """Alias for add_card method."""
        self.add_card(cabinet_data)

    def clear_cards(self):
        """Remove all cabinet cards from the grid."""
        for card in self._cabinet_cards.values():
            card.setParent(None)
            card.deleteLater()

        self._cabinet_cards.clear()
        self.flow_layout.clear_cards()
        self._switch_to_empty_state()

    def remove_cabinet_card(self, cabinet_id):
        """Remove a cabinet card from the grid."""
        if cabinet_id not in self._cabinet_cards:
            return

        card = self._cabinet_cards[cabinet_id]
        card.setParent(None)  # Remove from layout
        card.deleteLater()
        del self._cabinet_cards[cabinet_id]

        # Show empty state if no cards left
        if not self._cabinet_cards:
            self._switch_to_empty_state()

    def update_cabinet_quantity(self, cabinet_id, quantity):
        """Update the quantity display for a specific cabinet card."""
        if cabinet_id in self._cabinet_cards:
            card = self._cabinet_cards[cabinet_id]
            # Update the card's internal data and UI
            card.card_data["quantity"] = quantity
            if hasattr(card, "quantity_stepper"):
                card.quantity_stepper.set_value(quantity)

    def update_cabinet_sequence(self, cabinet_id, sequence):
        """Update the sequence number display for a specific cabinet card."""
        if cabinet_id in self._cabinet_cards:
            card = self._cabinet_cards[cabinet_id]
            # Update the card's internal data and UI
            card.update_sequence_display(sequence)

    def sort_cards_by_sequence(self):
        """Sort cabinet cards by sequence number with smooth transition."""
        if not self._cabinet_cards:
            return

        # Use position-based sorting instead of layout clearing for all cases
        self._sort_cards_by_position()

    def _sort_cards_by_position(self):
        """Sort cards by temporarily setting their visibility and positions."""
        from PySide6.QtWidgets import QApplication

        # Get all cards and sort by sequence
        sorted_cards = sorted(
            self._cabinet_cards.items(),
            key=lambda item: item[1].card_data.get("sequence", 999),
        )

        # If cards are already in correct order, no need to sort
        current_order = [card for _, card in sorted_cards]
        layout_order = []
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item and item.widget() and item.widget() in self._cabinet_cards.values():
                layout_order.append(item.widget())

        if current_order == layout_order:
            return  # Already sorted correctly

        # Disable layout updates temporarily
        self.content_widget.setUpdatesEnabled(False)

        # Remove all cards from layout but keep them as children
        widgets_removed = []
        while self.flow_layout.count() > 0:
            item = self.flow_layout.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                if widget in self._cabinet_cards.values():
                    widgets_removed.append(widget)
                    # Keep widget as child but hide it temporarily
                    widget.hide()

        # Process events to ensure removal is complete
        QApplication.processEvents()

        # Re-add cards in sorted order
        for cabinet_id, card in sorted_cards:
            self.flow_layout.addCard(card)
            card.show()

        # Re-enable updates and force geometry update
        self.content_widget.setUpdatesEnabled(True)
        self.content_widget.updateGeometry()
        self.scroll_area.updateGeometry()
        self.updateGeometry()

        # Process events to ensure smooth layout
        QApplication.processEvents()

    def _sort_cards_immediate(self):
        """Immediate sorting for small numbers of cards to avoid stacking."""
        # This method is now replaced by _sort_cards_by_position
        self._sort_cards_by_position()

    def _sort_cards_standard(self):
        """Standard sorting approach for larger numbers of cards."""
        # This method is now replaced by _sort_cards_by_position
        self._sort_cards_by_position()

    def _validate_sequence_number(
        self, new_value: int, current_value: int
    ) -> tuple[bool, str]:
        """Validate sequence number to prevent duplicates.

        Args:
            new_value: The new sequence number being set
            current_value: The current sequence number of the card being edited

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check if the new value is already used by another cabinet
        for cabinet_id, card in self._cabinet_cards.items():
            if hasattr(card, "card_data"):
                card_sequence = card.card_data.get("sequence")
                # If another card already has this sequence number, it's invalid
                if card_sequence == new_value and card_sequence != current_value:
                    return False, f"Numer kolejny #{new_value} jest już używany"

        return True, ""

    def set_search_filter(self, search_text):
        """Filter cards based on search text."""
        self._search_filter = search_text.lower()
        self._apply_search_filter()

    def _apply_search_filter(self):
        """Apply current search filter to all cards."""
        visible_count = 0

        for card in self._cabinet_cards.values():
            # Check if search text matches cabinet name
            cabinet_name = card.card_data.get("name", "").lower()
            matches = (
                self._search_filter in cabinet_name if self._search_filter else True
            )
            card.setVisible(matches)
            if matches:
                visible_count += 1

        # Show empty state if no cards match filter
        if visible_count == 0 and self._cabinet_cards:
            self._show_no_results_state()
        elif self._search_filter and visible_count > 0:
            self._show_filtered_results()

    def _switch_to_card_view(self):
        """Switch from empty state to card grid view."""
        # Check if content_widget still exists and is valid, recreate if needed
        try:
            if (
                not hasattr(self, "content_widget")
                or not self.content_widget
                or self.content_widget.isWidgetType() is False
            ):
                raise RuntimeError("Content widget invalid")
        except (RuntimeError, AttributeError):
            # Recreate the content widget with cards container and button
            self.content_widget = QWidget()
            self.content_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            content_layout = QVBoxLayout(self.content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(16)

            self.cards_container = QWidget()
            self.flow_layout = FlowLayout(
                self.cards_container, margin=8, spacing=CARD_GRID_SPACING
            )
            self.cards_container.setLayout(self.flow_layout)
            content_layout.addWidget(self.cards_container)

            self.add_catalog_btn = QPushButton("+ Dodaj z katalogu")
            self.add_catalog_btn.clicked.connect(self.sig_add_from_catalog.emit)
            content_layout.addWidget(
                self.add_catalog_btn, 0, Qt.AlignmentFlag.AlignLeft
            )

        try:
            if self.scroll_area.widget() != self.content_widget:
                self.scroll_area.setWidget(self.content_widget)
        except RuntimeError:
            # If setting widget fails, recreate and try again
            self.content_widget = QWidget()
            self.content_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            content_layout = QVBoxLayout(self.content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(16)

            self.cards_container = QWidget()
            self.flow_layout = FlowLayout(self.cards_container)
            self.cards_container.setLayout(self.flow_layout)
            content_layout.addWidget(self.cards_container)

            self.add_catalog_btn = QPushButton("+ Dodaj z katalogu")
            self.add_catalog_btn.clicked.connect(self.sig_add_from_catalog.emit)
            content_layout.addWidget(
                self.add_catalog_btn, 0, Qt.AlignmentFlag.AlignLeft
            )

            self.scroll_area.setWidget(self.content_widget)

    def _switch_to_empty_state(self):
        """Switch from card grid to empty state view."""
        # Check if empty_state widget still exists and is valid, recreate if needed
        try:
            if (
                not hasattr(self, "empty_state")
                or not self.empty_state
                or self.empty_state.isWidgetType() is False
            ):
                raise RuntimeError("Empty state widget invalid")
        except (RuntimeError, AttributeError):
            # Recreate the empty state widget
            self.empty_state = EmptyStateWidget()
            self.empty_state.add_cabinet_requested.connect(
                self.sig_add_from_catalog.emit
            )

        try:
            self.scroll_area.setWidget(self.empty_state)
        except RuntimeError:
            # If setting widget fails, recreate and try again
            self.empty_state = EmptyStateWidget()
            self.empty_state.add_cabinet_requested.connect(
                self.sig_add_from_catalog.emit
            )
            self.scroll_area.setWidget(self.empty_state)

    def _show_no_results_state(self):
        """Show a 'no search results' message."""
        # Could implement a different empty state for search results
        pass

    def _show_filtered_results(self):
        """Ensure card view is shown for filtered results."""
        if self.scroll_area.widget() != self.content_widget:
            self.scroll_area.setWidget(self.content_widget)

    def clear_selection(self):
        """Clear selection from all cards."""
        for card in self._cabinet_cards.values():
            card.set_selected(False)

    def get_selected_cabinet_ids(self):
        """Return list of currently selected cabinet IDs."""
        return [
            cabinet_id
            for cabinet_id, card in self._cabinet_cards.items()
            if card.is_card_selected()
        ]

    def select_all_visible(self):
        """Select all currently visible cards."""
        for card in self._cabinet_cards.values():
            if card.isVisible():
                card.set_selected(True)

    def get_total_cabinet_count(self):
        """Return total number of cabinet cards."""
        return len(self._cabinet_cards)

    def get_visible_cabinet_count(self):
        """Return number of currently visible cabinet cards."""
        return sum(1 for card in self._cabinet_cards.values() if card.isVisible())

    # Public methods to trigger actions (for context menu or external use)
    def emit_edit_signal(self, cabinet_id):
        """Emit edit signal for a specific cabinet."""
        self.sig_edit.emit(cabinet_id)

    def emit_duplicate_signal(self, cabinet_id):
        """Emit duplicate signal for a specific cabinet."""
        self.sig_duplicate.emit(cabinet_id)

    def emit_delete_signal(self, cabinet_id):
        """Emit delete signal for a specific cabinet."""
        self.sig_delete.emit(cabinet_id)
