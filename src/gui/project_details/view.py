"""
Project Details View

Main view class for the project details dialog.
Focused on UI layout and presentation, delegates business logic to controllers.
"""

from typing import List, Dict, Any
import logging
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QStackedWidget,
    QScrollArea,
    QTableView,
    QDialogButtonBox,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Signal, Qt, QTimer, QSettings
from PySide6.QtGui import QFont
from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project, ProjectCabinet
from src.gui.resources.styles import get_theme
from src.controllers.project_details_controller import ProjectDetailsController
from src.gui.cabinet_catalog.window import CatalogWindow
from src.services.catalog_service import CatalogService
from src.services.color_palette_service import ColorPaletteService
from src.services.settings_service import SettingsService
from .constants import (
    CARD_WIDTH,
    VIEW_MODE_CARDS,
    VIEW_MODE_TABLE,
    CONTENT_MARGINS,
)
from src.gui.layouts.flow_layout import FlowLayout
from .widgets import HeaderBar, Toolbar, BannerManager, CabinetCard

logger = logging.getLogger(__name__)


class UiState:
    """UI state persistence."""

    def __init__(self):
        self.settings = QSettings()

    def get_view_mode(self, default="cards"):
        return self.settings.value("project_details/view_mode", default)

    def set_view_mode(self, mode):
        self.settings.setValue("project_details/view_mode", mode)


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

        # CTA Button - uses primary theme color
        add_button = QPushButton("Dodaj z katalogu")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #0A766C;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #085f56;
            }
            QPushButton:pressed {
                background-color: #064e46;
            }
        """)
        add_button.clicked.connect(self.add_cabinet_requested.emit)

        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(add_button)


class ProjectDetailsView(QDialog):
    """
    Main project details dialog - UI only.

    This dialog provides the user interface for viewing and editing project details.
    It delegates all business logic to controllers and focuses purely on UI concerns.

    Key responsibilities:
    - Layout and widget management
    - UI state persistence (splitter positions, etc.)
    - Event delegation to controllers
    - Basic dialog lifecycle management
    """

    # Clean signals - remove compatibility aliases
    sig_view_mode_changed = Signal(str)  # 'cards' or 'table'
    sig_add_from_catalog = Signal()
    sig_add_custom = Signal()
    sig_export = Signal()
    sig_back = Signal()  # Back to project list

    sig_client_save = Signal(dict)
    sig_client_open_requested = Signal()

    # Cabinet operation signals
    sig_cabinet_qty_changed = Signal(int, int)  # cabinet_id, qty
    sig_cabinet_edit = Signal(int)  # cabinet_id
    sig_cabinet_duplicate = Signal(int)  # cabinet_id
    sig_cabinet_delete = Signal(int)  # cabinet_id
    sig_cabinet_selected = Signal(int)  # cabinet_id
    sig_cabinet_sequence_changed = Signal(int, int)  # cabinet_id, sequence_number

    def __init__(
        self,
        session: Session = None,
        project: Project = None,
        modal: bool = False,
        parent=None,
    ):
        """
        Initialize the project details view.

        Args:
            session: Database session (optional for compatibility)
            project: Project object (optional for compatibility)
            modal: Whether dialog should be modal
            parent: Parent widget
        """
        import time as _time

        # Start timing as early as possible for instrumentation
        self._dbg_start_time = _time.perf_counter()

        # Small helper to log elapsed ms from constructor start
        self._dbg = lambda msg: logger.debug(
            "[VIEW DEBUG][%.1fms] %s",
            (_time.perf_counter() - self._dbg_start_time) * 1000,
            msg,
        )

        self._dbg(
            f"Creating ProjectDetailsView for project: {project.name if project else 'None'}"
        )

        super().__init__(parent)
        self.session = session
        self.project = project
        self.modal = modal
        self._current_view_mode = VIEW_MODE_CARDS
        self.is_dark_mode = False
        self.color_service = None
        if self.session:
            try:
                self.is_dark_mode = bool(
                    SettingsService(self.session).get_setting_value("dark_mode", False)
                )
            except Exception as exc:
                logger.warning("Failed to read dark mode setting: %s", exc)

        self._dbg("Setting visibility flags...")
        # Prevent any visibility during construction
        self.setVisible(False)
        self.hide()

        # Set attribute to prevent automatic showing
        self.setAttribute(Qt.WA_DontShowOnScreen, True)

        # Set window flags to prevent premature showing
        if parent:
            self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        self._dbg("Blocking signals during construction...")
        # Block all signals during construction to prevent Qt from auto-showing
        self.blockSignals(True)

        # Data management - no longer authoritative, just for UI
        self.cabinets = []  # Cached list for UI display
        self._cards_by_id = {}  # cabinet_id -> CabinetCard mapping

        # Initialize UI state persistence
        self.ui_state = UiState()

        # Initialize controller if session and project are provided
        self.controller = None
        self.catalog_service = None
        if session and project:
            self.controller = ProjectDetailsController(session, project, self)
            self._setup_controller_connections()

            # Initialize catalog service for unified catalog access
            self.catalog_service = CatalogService(session)

            self.color_service = ColorPaletteService(session)
            self.color_service.ensure_seeded()
            self.color_service.sync_runtime_color_map()

        # Initialize services for compatibility (removed in favor of controller)
        if session and project:
            from src.services.report_generator import ReportGenerator

            self.report_generator = ReportGenerator(db_session=self.session)
        else:
            self.report_generator = None

        self._dbg("Setting up UI...")
        self._setup_ui()
        self._dbg("Setting up connections...")
        self._setup_connections()
        self._dbg("Setting up styling...")
        self._setup_styling()

        # Update header info if project is available
        if self.project:
            self._update_header_info()

        # Don't load data in constructor - will be loaded when shown
        # Data loading deferred to showEvent to prevent flash
        self._data_loaded = False

        # Set initial view mode from saved settings
        saved_view_mode = self.ui_state.get_view_mode(VIEW_MODE_CARDS)
        self._on_view_mode_changed(saved_view_mode)

        # Update toolbar to reflect current view mode
        if hasattr(self.toolbar, "set_view_mode"):
            self.toolbar.set_view_mode(saved_view_mode)

        # Unblock signals after construction is complete
        self.blockSignals(False)

        # Remove the "don't show" attribute now that construction is done
        self.setAttribute(Qt.WA_DontShowOnScreen, False)

    def _setup_ui(self) -> None:
        """Set up the dialog UI components."""
        self._dbg("_setup_ui starting...")

        self.setWindowTitle("Szczegóły projektu")

        # Calculate minimum size based on card width (same as main window)
        minimum_width = CARD_WIDTH + 100  # Card width + margins/scrollbar
        self.setMinimumSize(minimum_width, 600)

        self._dbg("Creating main layout...")
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._dbg("Creating header bar...")
        # Header bar
        self.header_bar = HeaderBar()
        # Don't set fixed height - let it size naturally for better layout
        main_layout.addWidget(self.header_bar)

        # Toolbar
        self.toolbar = Toolbar()
        main_layout.addWidget(self.toolbar)

        # Main content area (no splitter - cabinet cards are the focus)
        self._create_central_area()
        main_layout.addWidget(self.central_widget)

        # Banner manager for notifications (moved to bottom)
        self.banner_manager = BannerManager()
        main_layout.addWidget(self.banner_manager)

        # Footer with dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Close).setText("Zamknij")
        main_layout.addWidget(self.button_box)

        # Initialize viewport tracking for responsive behavior after widgets are set up
        QTimer.singleShot(0, self._initialize_viewport_tracking)

    def _create_central_area(self) -> None:
        """Create the central stacked widget area with responsive card layout."""
        self._dbg("_create_central_area: starting...")

        self.central_widget = QWidget()
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(*CONTENT_MARGINS)
        central_layout.setSpacing(0)

        # Stacked widget for different view modes
        self.stacked_widget = QStackedWidget()

        # Card view with responsive layout and sticky add button
        self.card_view_widget = QWidget()
        card_view_layout = QVBoxLayout(self.card_view_widget)
        card_view_layout.setContentsMargins(0, 0, 0, 0)
        card_view_layout.setSpacing(12)

        # Card scroll area
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.card_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Wrapper widget for scroll area content (cards only)
        self.scroll_content = QWidget()
        scroll_content_layout = QVBoxLayout(self.scroll_content)
        scroll_content_layout.setContentsMargins(0, 0, 0, 0)
        scroll_content_layout.setSpacing(16)

        # Card container with FlowLayout for simple, flash-free behavior (like main window)
        self.card_container = QWidget()
        self.card_layout = FlowLayout(self.card_container, margin=8, spacing=12)
        self.card_container.setLayout(self.card_layout)
        scroll_content_layout.addWidget(self.card_container)
        scroll_content_layout.addStretch()

        self.card_scroll.setWidget(self.scroll_content)
        card_view_layout.addWidget(self.card_scroll, 1)

        # Add from catalog button - pinned below scroll area (always visible)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.addStretch()
        self.add_catalog_btn = QPushButton("+ Dodaj z katalogu")
        self.add_catalog_btn.clicked.connect(self._handle_add_from_catalog)
        footer_layout.addWidget(self.add_catalog_btn)
        footer_layout.addStretch()
        card_view_layout.addLayout(footer_layout)

        self.stacked_widget.addWidget(self.card_view_widget)

        # Empty state widget for when no cabinets exist
        self.empty_state = EmptyStateWidget(parent=self)
        self.empty_state.add_cabinet_requested.connect(self._handle_add_from_catalog)
        self.stacked_widget.addWidget(self.empty_state)

        # Table view with proper setup
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.stacked_widget.addWidget(self.table_view)
        central_layout.addWidget(self.stacked_widget)

        self._dbg("_create_central_area: complete")

    def _setup_controller_connections(self) -> None:
        """Set up connections between controller and view."""
        if not self.controller:
            return

        # Connect controller signals to view methods
        self.controller.data_loaded.connect(self.apply_card_order)
        self.controller.data_error.connect(self._show_error)
        self.controller.cabinet_updated.connect(self._on_cabinet_updated)
        self.controller.validation_error.connect(self._show_validation_error)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Dialog button
        self.button_box.rejected.connect(self._on_close)

        # Header bar signals
        self.header_bar.sig_export.connect(self._handle_export)
        self.header_bar.sig_client.connect(self._on_client_open_requested)
        self.header_bar.sig_back.connect(self.sig_back.emit)

        # Toolbar signals
        self.toolbar.sig_add_from_catalog.connect(self._handle_add_from_catalog)
        self.toolbar.sig_add_custom.connect(self._handle_add_custom)
        self.toolbar.sig_view_mode_changed.connect(self._on_view_mode_changed)
        # Delegate sort to controller instead of handling directly
        self.toolbar.sig_sort_by_sequence.connect(self._on_sort_requested)

        # Table view signals
        self.table_view.doubleClicked.connect(self._on_table_double_click)

        # Cabinet card signals - delegate to controller
        self.sig_cabinet_sequence_changed.connect(self._on_sequence_changed_request)
        self.sig_cabinet_qty_changed.connect(self._on_quantity_changed_request)
        self.sig_cabinet_delete.connect(self._on_delete_request)
        self.sig_cabinet_duplicate.connect(self._on_duplicate_request)

        # Cabinet edit signal - handle locally
        self.sig_cabinet_edit.connect(self._handle_cabinet_edit)

    def _setup_styling(self) -> None:
        """Apply modern styling with the main application theme."""
        # Apply main application theme to the dialog and all child widgets
        theme = get_theme(self.is_dark_mode)
        self.setStyleSheet(theme)

        # Set property classes for individual components for additional styling
        self.setProperty("class", "dialog")

        # Child widgets inherit dialog theme from the parent stylesheet.

    def _apply_theme_to_children(self) -> None:
        """Backward-compatible no-op; children inherit parent theme."""
        return

    def apply_card_order(self, ordered_cabinets: List[ProjectCabinet]) -> None:
        """
        Apply the given cabinet order to the view.

        This method is called by the controller when data changes.
        It rebuilds the layout in the order provided by controller.

        Args:
            ordered_cabinets: List of cabinets in the desired display order
        """
        try:
            self._dbg("apply_card_order starting...")
            # Update cached cabinet list
            self.cabinets = ordered_cabinets

            # Update header info with project details
            self._update_header_info()

            # Check if we can avoid full rebuild by just reordering existing cards
            if self._can_reorder_existing_cards(ordered_cabinets):
                self._dbg("Reordering existing cards (fast path)...")
                self._reorder_existing_cards(ordered_cabinets)
                return

            # Full rebuild needed
            self._dbg("Full rebuild needed - rebuilding all cards...")
            self._rebuild_all_cards(ordered_cabinets)

        except Exception as e:
            logger.exception("Error applying card order")
            self._show_error(f"Błąd podczas odświeżania widoku: {e}")

    def _can_reorder_existing_cards(
        self, ordered_cabinets: List[ProjectCabinet]
    ) -> bool:
        """Check if we can reorder existing cards instead of rebuilding all."""
        # If more cabinets than cards, we need to create new ones - full rebuild
        if len(ordered_cabinets) > len(self._cards_by_id):
            return False

        # Check if all cabinets have existing cards
        for cabinet in ordered_cabinets:
            if cabinet.id not in self._cards_by_id:
                return False

        # Can reorder even if some cards were deleted (we'll remove them)
        return True

    def _reorder_existing_cards(self, ordered_cabinets: List[ProjectCabinet]) -> None:
        """Reorder existing cards and update their data."""
        self._dbg("_reorder_existing_cards: starting...")

        # Find cards to remove (cabinet was deleted)
        current_cabinet_ids = {cabinet.id for cabinet in ordered_cabinets}
        cards_to_remove = [
            cid for cid in self._cards_by_id if cid not in current_cabinet_ids
        ]

        self._dbg(f"_reorder_existing_cards: removing {len(cards_to_remove)} cards")

        # Remove cards for deleted cabinets
        for cabinet_id in cards_to_remove:
            card = self._cards_by_id.pop(cabinet_id)
            self.card_layout.removeWidget(card)
            card.deleteLater()

        # If no cabinets left, just clear and return
        if not ordered_cabinets:
            self._clear_flow_layout_without_deleting()
            self._update_view_state()
            return

        # Freeze updates during rebuild
        self.card_container.setUpdatesEnabled(False)
        try:
            # Clear layout without deleting widgets
            self._clear_flow_layout_without_deleting()

            # Re-add cards in the new order and update their data
            for cabinet in ordered_cabinets:
                if cabinet.id in self._cards_by_id:
                    card = self._cards_by_id[cabinet.id]
                    # Update card data with fresh cabinet information
                    updated_card_data = self._cabinet_to_card_data(cabinet)
                    card.update_data(updated_card_data)
                    self.card_layout.addWidget(card)
        finally:
            self.card_container.setUpdatesEnabled(True)

    def _rebuild_all_cards(self, ordered_cabinets: List[ProjectCabinet]) -> None:
        """Rebuild all cards from scratch."""
        if not ordered_cabinets:
            return
        import time as _time

        start = _time.perf_counter()
        self._dbg("_rebuild_all_cards: starting...")

        # Freeze updates during rebuild
        self.card_container.setUpdatesEnabled(False)
        per_card_times = []
        try:
            # Clear existing cards
            self._clear_flow_layout_without_deleting()
            self._cards_by_id.clear()

            # Create cards in the provided order and record per-card timings
            for cabinet in ordered_cabinets:
                cstart = _time.perf_counter()
                card_data = self._cabinet_to_card_data(cabinet)
                card = CabinetCard(card_data, parent=self.card_container)

                # Connect card signals
                self._connect_card_signals(card)

                self.card_layout.addWidget(card)
                self._cards_by_id[cabinet.id] = card

                per_card_times.append((_time.perf_counter() - cstart) * 1000.0)

            # Update view state
            self._update_view_state()
        finally:
            self.card_container.setUpdatesEnabled(True)
            elapsed = (_time.perf_counter() - start) * 1000.0
            # Summarize per-card timings
            if per_card_times:
                total_card_ms = sum(per_card_times)
                avg = total_card_ms / len(per_card_times)
                # Top 5 slowest cards
                indexed = list(enumerate(per_card_times))
                indexed.sort(key=lambda x: x[1], reverse=True)
                top_n = indexed[:5]
                self._dbg(
                    f"_rebuild_all_cards: created {len(per_card_times)} cards in {total_card_ms:.1f}ms (avg {avg:.1f}ms/card); total elapsed {elapsed:.1f}ms"
                )
                for idx, t in top_n:
                    cab = ordered_cabinets[idx]
                    self._dbg(
                        f"  slow card[{idx}] id={getattr(cab, 'id', None)} name={getattr(cab, 'name', None)} {t:.1f}ms"
                    )
            else:
                self._dbg(
                    f"_rebuild_all_cards finished in {elapsed:.1f}ms (no cards created)"
                )

    def _clear_flow_layout_without_deleting(self) -> None:
        """Clear layout without deleting the widgets."""
        self._dbg("_clear_flow_layout_without_deleting: clearing layout...")
        removed = 0
        while self.card_layout.count():
            self.card_layout.takeAt(0)
            # Don't delete the widget, just remove from layout
            removed += 1
        self._dbg(f"_clear_flow_layout_without_deleting: removed {removed} items")

    def _is_sequence_duplicate(self, sequence: int, exclude_cabinet_id: int) -> bool:
        """
        Check if a sequence number is already used by another cabinet.

        Args:
            sequence: Sequence number to check
            exclude_cabinet_id: Cabinet ID to exclude from the check (current cabinet)

        Returns:
            True if sequence is duplicate, False otherwise
        """
        for cabinet in self.cabinets:
            if cabinet.id != exclude_cabinet_id and cabinet.sequence_number == sequence:
                return True
        return False

    def _connect_card_signals(self, card: CabinetCard) -> None:
        """Connect signals from a cabinet card to the view's signal system."""
        card.sig_qty_changed.connect(self.sig_cabinet_qty_changed.emit)
        card.sig_edit.connect(self.sig_cabinet_edit.emit)
        card.sig_duplicate.connect(self.sig_cabinet_duplicate.emit)
        card.sig_delete.connect(self.sig_cabinet_delete.emit)
        card.sig_selected.connect(self._on_card_selected)  # Handle single selection
        card.sig_sequence_changed.connect(self.sig_cabinet_sequence_changed.emit)

        # Set up duplicate sequence number prevention
        if hasattr(card, "sequence_input"):
            card.sequence_input.set_duplicate_check_callback(
                lambda seq: self._is_sequence_duplicate(seq, card.cabinet_id)
            )

    def _on_sort_requested(self) -> None:
        """Handle sort request from toolbar - delegate to controller."""
        if self.controller:
            self.controller.on_sort_requested()

    def _on_card_selected(self, cabinet_id: int):
        """Handle card selection - implement single selection behavior."""
        # Clear selection from all other cards
        for card_id, card in self._cards_by_id.items():
            if card_id != cabinet_id:
                card.set_selected(False)

        # Toggle selection on the clicked card
        clicked_card = self._cards_by_id.get(cabinet_id)
        if clicked_card:
            clicked_card.set_selected(not clicked_card.is_card_selected())

        # Emit the selection signal
        self.sig_cabinet_selected.emit(cabinet_id)

    def _get_selected_cabinet_id(self) -> int | None:
        """Get the ID of the currently selected cabinet card."""
        for card_id, card in self._cards_by_id.items():
            if card.is_card_selected():
                return card_id
        return None

    def _delete_selected_cabinet(self) -> None:
        """Delete the currently selected cabinet (called from keyboard shortcut)."""
        cabinet_id = self._get_selected_cabinet_id()
        if cabinet_id is not None:
            self._on_delete_request(cabinet_id)

    def _on_sequence_changed_request(self, cabinet_id: int, new_sequence: int) -> None:
        """Handle sequence change request from card - delegate to controller."""
        if self.controller:
            self.controller.on_sequence_changed(cabinet_id, new_sequence)

    def _on_quantity_changed_request(self, cabinet_id: int, new_quantity: int) -> None:
        """Handle quantity change request from card - delegate to controller."""
        if self.controller:
            self.controller.on_quantity_changed(cabinet_id, new_quantity)

    def _on_delete_request(self, cabinet_id: int) -> None:
        """Handle delete request from card - delegate to controller."""
        self._dbg(f"_on_delete_request: cabinet_id={cabinet_id}")
        if self.controller:
            self.controller.on_cabinet_deleted(cabinet_id)
        else:
            self._dbg("_on_delete_request: no controller!")

    def _on_duplicate_request(self, cabinet_id: int) -> None:
        """Handle duplicate request from card - delegate to controller."""
        self._dbg(f"_on_duplicate_request: cabinet_id={cabinet_id}")
        if self.controller:
            self.controller.on_cabinet_duplicated(cabinet_id)
            self._show_success("Szafka zduplikowana")
        else:
            self._dbg("_on_duplicate_request: no controller!")

    def _on_table_double_click(self, index):
        """Handle double-click on table view row to edit cabinet."""
        if not index.isValid() or not self.table_view.model():
            return

        # Get the cabinet ID from the table model
        # Assuming the cabinet ID is in the first column or stored in model data
        row = index.row()
        model = self.table_view.model()

        # Try to get cabinet ID from the model - this may need adjustment based on actual table model implementation
        try:
            # If the model stores cabinet objects directly
            if hasattr(model, "cabinets") and row < len(model.cabinets):
                cabinet_id = model.cabinets[row].id
                self.sig_cabinet_edit.emit(cabinet_id)
            # If the model has a method to get cabinet ID
            elif hasattr(model, "get_cabinet_id"):
                cabinet_id = model.get_cabinet_id(row)
                if cabinet_id:
                    self.sig_cabinet_edit.emit(cabinet_id)
            # Fallback: try to get from first column if it contains ID
            elif model.columnCount() > 0:
                id_index = model.index(row, 0)
                cabinet_id = model.data(id_index, Qt.UserRole)  # Try UserRole first
                if not cabinet_id:
                    cabinet_id = model.data(
                        id_index, Qt.DisplayRole
                    )  # Fallback to DisplayRole
                if cabinet_id and isinstance(cabinet_id, int):
                    self.sig_cabinet_edit.emit(cabinet_id)
        except Exception as e:
            # Log error but don't crash
            logger.exception("Error handling table double-click: %s", e)

    def _on_cabinet_updated(self, updated_cabinet: ProjectCabinet) -> None:
        """Handle cabinet update notification from controller."""
        # Update the specific card if it exists
        if updated_cabinet.id in self._cards_by_id:
            card = self._cards_by_id[updated_cabinet.id]
            card_data = self._cabinet_to_card_data(updated_cabinet)
            card.update_data(card_data)

    def _show_error(self, message: str) -> None:
        """Show error message in banner."""
        if hasattr(self, "banner_manager") and self.banner_manager:
            self.banner_manager.show_error(message)
        else:
            logger.error(f"Error (no banner manager): {message}")

    def _show_validation_error(self, message: str) -> None:
        """Show validation error message in banner."""
        if hasattr(self, "banner_manager") and self.banner_manager:
            self.banner_manager.show_warning(message)
        else:
            logger.warning(f"Validation error (no banner manager): {message}")

    def _handle_cabinet_edit(self, cabinet_id: int) -> None:
        """Handle cabinet edit request - opens the unified edit dialog."""
        from src.gui.cabinet_editor import CabinetEditorDialog

        try:
            # Find the cabinet
            cabinet = None
            for c in self.cabinets:
                if c.id == cabinet_id:
                    cabinet = c
                    break

            if not cabinet:
                self._show_error("Nie znaleziono szafki")
                return

            # Check if this is a custom cabinet (type_id=NULL)
            if cabinet.type_id is None:
                # This is a custom cabinet - handle it differently
                self._handle_custom_cabinet_edit(cabinet)
                return

            # Get the cabinet type for editing catalog cabinet
            cabinet_type = self.catalog_service.cabinet_type_service.get_template(
                cabinet.type_id
            )

            if not cabinet_type:
                self._show_error("Nie znaleziono typu szafki")
                return

            # Open unified editor dialog in instance mode for catalog cabinet
            editor = CabinetEditorDialog(
                catalog_service=self.catalog_service,
                project_service=getattr(self.controller, "project_service", None)
                if self.controller
                else None,
                color_service=self.color_service,
                parent=self,
            )
            editor.load_instance(cabinet_type, cabinet)

            # Connect save signal to refresh data immediately when changes are applied
            if self.controller:
                editor.sig_saved.connect(self.controller.load_data)

            dialog_result = editor.exec()

            if dialog_result == QDialog.DialogCode.Accepted:
                self._show_success("Szafka zaktualizowana")

            # Ensure data is refreshed regardless of how dialog was closed
            # (the sig_saved connection will handle real-time updates during editing)
            if self.controller:
                self.controller.load_data()

        except Exception as e:
            logger.exception("Error editing cabinet")
            self._show_error(f"Błąd podczas edycji szafki: {e}")

    def _handle_custom_cabinet_edit(self, cabinet: ProjectCabinet) -> None:
        """Handle editing a custom cabinet (type_id=NULL)."""
        from src.gui.cabinet_editor import CabinetEditorDialog

        try:
            # Open cabinet editor dialog for custom cabinet (no catalog type)
            editor = CabinetEditorDialog(
                catalog_service=self.catalog_service,
                project_service=getattr(self.controller, "project_service", None)
                if self.controller
                else None,
                color_service=self.color_service,
                parent=self,
            )

            # Load custom cabinet instance without catalog type
            editor.load_custom_instance(cabinet)

            # Connect save signal to refresh data immediately when changes are applied
            if self.controller:
                editor.sig_saved.connect(self.controller.load_data)

            dialog_result = editor.exec()

            if dialog_result == QDialog.DialogCode.Accepted:
                self._show_success("Niestandardowa szafka zaktualizowana")

            # Ensure data is refreshed regardless of how dialog was closed
            if self.controller:
                self.controller.load_data()

        except Exception as e:
            logger.exception("Error handling custom cabinet edit")
            self._show_error(f"Błąd podczas edycji niestandardowej szafki: {e}")

    def _show_success(self, message: str) -> None:
        """Show success message in banner."""
        if hasattr(self, "banner_manager") and self.banner_manager:
            self.banner_manager.show_success(message)
        else:
            logger.info(f"Success (no banner manager): {message}")

    def _initialize_viewport_tracking(self) -> None:
        """Initialize viewport tracking for responsive layout updates."""
        if hasattr(self, "card_scroll"):
            self.card_scroll.viewport().installEventFilter(self)

    def _clear_card_layout(self) -> None:
        """Clear all widgets from the card layout."""
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def _cabinet_to_card_data(self, cabinet: ProjectCabinet) -> Dict[str, Any]:
        """Convert ProjectCabinet to card data dict using snapshot data."""
        # Get dimensions from parts snapshot (works for both standard and custom cabinets)
        width = height = depth = None
        cabinet_name = "Niestandardowy"

        # Calculate dimensions from parts snapshot
        if hasattr(cabinet, "parts") and cabinet.parts:
            parts = cabinet.parts

            if len(parts) == 1:
                # Single part: use 2D dimensions (width and height)
                part = parts[0]
                if part.width_mm is not None:
                    width = int(part.width_mm)
                if part.height_mm is not None:
                    height = int(part.height_mm)
                # Don't set depth for single part

            elif len(parts) >= 2:
                # Multiple parts: analyze if we can determine 3D dimensions
                # Check which dimensions are consistent across parts
                widths = [int(p.width_mm) for p in parts if p.width_mm is not None]
                heights = [int(p.height_mm) for p in parts if p.height_mm is not None]

                # If widths are all the same, it's the cabinet width
                if widths and len(set(widths)) == 1:
                    width = widths[0]
                elif widths:
                    # Use the most common width or max
                    width = max(widths)

                # If heights are all the same, it's the cabinet height
                if heights and len(set(heights)) == 1:
                    height = heights[0]
                elif heights:
                    # Use the most common height or max
                    height = max(heights)

                # For depth: use the fact that different widths can indicate front/back parts
                # If there are different widths, the smaller one is likely the depth
                if widths and len(set(widths)) > 1:
                    sorted_widths = sorted(set(widths))
                    # The smallest width among parts is likely the cabinet depth
                    depth = sorted_widths[0]

            # Try to get name from calculation context (for custom cabinets)
            if not cabinet.cabinet_type and cabinet.parts:
                # Check if any part has calc_context_json with template_name
                for part in cabinet.parts:
                    if (
                        part.calc_context_json
                        and isinstance(part.calc_context_json, dict)
                        and "template_name" in part.calc_context_json
                    ):
                        template_name = part.calc_context_json["template_name"]
                        cabinet_name = f"{template_name} + niestandardowa"
                        break

        # Note: Do NOT set default dimensions if no parts found
        # This allows the card to hide dimension section when there are no parts
        # Do NOT set default depth - only display it when we can calculate it from parts

        # Get cabinet name (from template if standard, from context if custom)
        if cabinet.cabinet_type:
            cabinet_name = cabinet.cabinet_type.name

        return {
            "id": cabinet.id,
            "name": cabinet_name,
            "sequence": cabinet.sequence_number or 1,
            "quantity": cabinet.quantity or 1,
            "body_color": cabinet.body_color or "Biały",
            "front_color": cabinet.front_color or "Biały",
            "width_mm": width,
            "height_mm": height,
            "depth_mm": depth,
            "kitchen_type": cabinet.cabinet_type.kitchen_type
            if cabinet.cabinet_type
            else "CUSTOM",
        }

    def _update_header_info(self) -> None:
        """Update header bar with project information."""
        if not self.project:
            return

        # Get project information with fallbacks
        project_name = getattr(self.project, "name", "Projekt")
        order_number = getattr(self.project, "order_number", "")
        kitchen_type = getattr(self.project, "kitchen_type", "")

        created_date = ""
        if hasattr(self.project, "created_at") and self.project.created_at:
            created_date = self.project.created_at.strftime("%Y-%m-%d")

        self.header_bar.set_project_info(
            name=project_name,
            order_number=order_number,
            kitchen_type=kitchen_type,
            created_date=created_date,
        )

        # Update window title
        self.setWindowTitle(f"Szczegóły projektu: {project_name}")

    def _update_view_state(self) -> None:
        """Update view state based on data availability."""
        if self.cabinets:
            self.stacked_widget.setCurrentWidget(self.card_view_widget)
        else:
            self.stacked_widget.setCurrentWidget(self.empty_state)

    # Event handlers (stubs - implement as needed)
    def _on_close(self):
        """Handle dialog close."""
        self.accept()

    def _handle_add_from_catalog(self):
        """Handle add from catalog request."""
        try:
            # Check if we have the required components
            if not self.project:
                logger.warning("No project available for catalog dialog")
                self.sig_add_from_catalog.emit()
                return

            # Check if catalog service is available
            if not self.catalog_service:
                logger.warning("No catalog service available for catalog dialog")
                self.sig_add_from_catalog.emit()
                return

            # Create and show unified catalog window in "add" mode
            catalog_window = CatalogWindow(
                catalog_service=self.catalog_service,
                project_service=self.controller,
                initial_mode="add",
                target_project=self.project,
                parent=self,
            )

            # Connect signal to handle cabinet addition
            catalog_window.sig_added_to_project.connect(
                self._on_cabinet_added_from_catalog
            )

            # Show the catalog window
            catalog_window.exec()

        except Exception:
            logger.exception("Error opening catalog window")
            # Fallback to signal for now
            self.sig_add_from_catalog.emit()

    def _on_cabinet_added_from_catalog(
        self, cabinet_type_id: int, project_id: int, quantity: int, options: dict
    ):
        """Handle cabinet added from catalog."""
        try:
            # Defer refresh to next event loop iteration to avoid blocking
            def do_refresh():
                if self.controller:
                    self.controller.load_data()

            QTimer.singleShot(0, do_refresh)
        except Exception:
            logger.exception("Error refreshing after cabinet addition from catalog")

    def _handle_add_custom(self):
        """Handle add custom cabinet request."""
        try:
            # Create a custom cabinet dialog with formula service
            from src.gui.dialogs.custom_cabinet_dialog import CustomCabinetDialog
            from src.services.formula_service import FormulaService

            # Create formula service
            formula_service = FormulaService(self.controller.session)

            # Create and show the dialog
            dialog = CustomCabinetDialog(
                formula_service,
                self.controller.project_service,
                self.controller.project,
                parent=self,
            )

            if dialog.exec() == QDialog.Accepted:
                # CustomCabinetDialog already added the cabinet to database
                # Just refresh the view to show the new cabinet
                self.controller.load_data()

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Błąd", f"Nie udało się dodać niestandardowej szafki: {str(e)}"
            )

    def _handle_export(self):
        """Handle export request."""
        self.sig_export.emit()

    def _on_client_open_requested(self):
        """Handle client info request."""
        self.sig_client_open_requested.emit()

    def _on_view_mode_changed(self, mode: str):
        """Handle view mode change."""
        self._current_view_mode = mode

        # Actually switch the stacked widget to show the correct view
        if mode == VIEW_MODE_TABLE:
            self._populate_table_view()
            self.stacked_widget.setCurrentWidget(self.table_view)
        elif mode == VIEW_MODE_CARDS:
            # Only switch to cards if we have cabinets, otherwise show empty state
            if self.cabinets:
                self.stacked_widget.setCurrentWidget(self.card_view_widget)
            else:
                self.stacked_widget.setCurrentWidget(self.empty_state)

        # Persist the view mode choice
        self.ui_state.set_view_mode(mode)

        self.sig_view_mode_changed.emit(mode)

    def _populate_table_view(self):
        """Populate the table view with cabinet data."""
        if not self.cabinets:
            # Clear the table if no cabinets
            self.table_view.setModel(None)
            return

        try:
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QStandardItemModel, QStandardItem

            # Create a simple table model
            model = QStandardItemModel()
            headers = [
                "Sekwencja",
                "Nazwa",
                "Wymiary",
                "Kolor przód",
                "Kolor korpus",
                "Ilość",
            ]
            model.setHorizontalHeaderLabels(headers)

            # Add cabinet data to the model
            for cabinet in self.cabinets:
                row = []

                # Sequence
                seq_item = QStandardItem(str(cabinet.sequence_number or ""))
                seq_item.setData(
                    cabinet.id, Qt.ItemDataRole.UserRole
                )  # Store cabinet ID
                row.append(seq_item)

                # Name (from cabinet type)
                name = ""
                if hasattr(cabinet, "cabinet_type") and cabinet.cabinet_type:
                    name = getattr(cabinet.cabinet_type, "name", "") or str(
                        cabinet.cabinet_type.id
                    )
                name_item = QStandardItem(name)
                row.append(name_item)

                # Dimensions (calculated from cabinet template parts)
                dimensions = "Auto"  # Calculated from template parts
                dim_item = QStandardItem(dimensions)
                row.append(dim_item)

                # Front color
                front_color_item = QStandardItem(cabinet.front_color or "")
                row.append(front_color_item)

                # Body color
                body_color_item = QStandardItem(cabinet.body_color or "")
                row.append(body_color_item)

                # Quantity
                qty_item = QStandardItem(str(cabinet.quantity))
                row.append(qty_item)

                model.appendRow(row)

            # Set the model to the table view
            self.table_view.setModel(model)

            # Resize columns to content
            self.table_view.resizeColumnsToContents()

        except Exception as e:
            logger.exception("Error populating table view")
            self._show_error(f"Błąd podczas ładowania tabeli: {e}")

    def show_dialog(self) -> None:
        """Show the dialog in the appropriate mode."""
        # Ensure signals are unblocked and dialog can be shown
        self.blockSignals(False)
        self.setAttribute(Qt.WA_DontShowOnScreen, False)

        # Ensure proper sizing before showing
        if not self.size().isValid() or self.size().width() < 800:
            # Set a reasonable default size if not already set
            self.resize(1000, 700)

        # Center the dialog on parent or screen
        if self.parent():
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(max(0, x), max(0, y))

        if self.modal:
            self.exec()
        else:
            self.show()

    def _update_card_view(self) -> None:
        """Update the card view with current cabinet data."""
        # This method is now handled by apply_card_order from controller
        pass

    def showEvent(self, event):
        """Load data when dialog is actually shown to prevent flash."""
        super().showEvent(event)

        # Mark that first show is done to enable geometry operations
        if not getattr(self, "_first_show_done", False):
            self._first_show_done = True

        # Load data only once and only when we have a controller
        # Check if controller already has data to avoid duplicate loading
        if (
            not self._data_loaded
            and self.controller
            and not hasattr(self.controller, "cabinets")
            or not self.controller.cabinets
        ):
            self._data_loaded = True
            self.controller.load_data()
