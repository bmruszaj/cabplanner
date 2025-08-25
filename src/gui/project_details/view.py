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
from .constants import *
from .layouts import ResponsiveFlowLayout
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
    sig_print = Signal()
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
        super().__init__(parent)
        self.session = session
        self.project = project
        self.modal = modal
        self._current_view_mode = VIEW_MODE_CARDS
        self.is_dark_mode = False  # Default value

        # Data management - no longer authoritative, just for UI
        self.cabinets = []  # Cached list for UI display
        self._cards_by_id = {}  # cabinet_id -> CabinetCard mapping

        # Initialize UI state persistence
        self.ui_state = UiState()

        # Initialize controller if session and project are provided
        self.controller = None
        if session and project:
            self.controller = ProjectDetailsController(session, project, self)
            self._setup_controller_connections()

        # Initialize services for compatibility (removed in favor of controller)
        if session and project:
            from src.services.report_generator import ReportGenerator

            self.report_generator = ReportGenerator(self.session)
        else:
            self.report_generator = None

        self._setup_ui()
        self._setup_connections()
        self._setup_styling()

        # Update header info if project is available
        if self.project:
            self._update_header_info()

        # Load initial data if controller is available
        if self.controller:
            self.controller.load_data()
            
        # Set initial view mode from saved settings
        saved_view_mode = self.ui_state.get_view_mode(VIEW_MODE_CARDS)
        self._on_view_mode_changed(saved_view_mode)
        
        # Update toolbar to reflect current view mode
        if hasattr(self.toolbar, 'set_view_mode'):
            self.toolbar.set_view_mode(saved_view_mode)

    def _setup_ui(self) -> None:
        """Set up the dialog UI components."""
        self.setWindowTitle("Szczegóły projektu")

        # Calculate minimum size based on card width (same as main window)
        minimum_width = CARD_WIDTH + 100  # Card width + margins/scrollbar
        self.setMinimumSize(minimum_width, 600)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar
        self.header_bar = HeaderBar()
        self.header_bar.setFixedHeight(HEADER_HEIGHT)
        main_layout.addWidget(self.header_bar)

        # Toolbar
        self.toolbar = Toolbar()
        self.toolbar.setFixedHeight(TOOLBAR_HEIGHT)
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
        self.central_widget = QWidget()
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(*CONTENT_MARGINS)
        central_layout.setSpacing(0)

        # Stacked widget for different view modes
        self.stacked_widget = QStackedWidget()

        # Card view with responsive layout (like main window)
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.card_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Card container with ResponsiveFlowLayout for proper responsive behavior
        self.card_container = QWidget()
        self.card_layout = ResponsiveFlowLayout(
            self.card_container, margin=8, spacing=12
        )
        self.card_container.setLayout(self.card_layout)

        self.card_scroll.setWidget(self.card_container)
        self.stacked_widget.addWidget(self.card_scroll)

        # Empty state widget for when no cabinets exist
        self.empty_state = EmptyStateWidget()
        self.empty_state.add_cabinet_requested.connect(self._handle_add_from_catalog)
        self.stacked_widget.addWidget(self.empty_state)

        # Table view with proper setup
        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setStyleSheet("""
            QTableView {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 8px;
                font-weight: 500;
            }
            QTableView::item {
                padding: 8px;
            }
            QTableView::item:alternate {
                background-color: #f9f9f9;
            }
        """)
        self.stacked_widget.addWidget(self.table_view)

        central_layout.addWidget(self.stacked_widget)

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
        self.header_bar.sig_print.connect(self._handle_print)
        self.header_bar.sig_client.connect(self._on_client_open_requested)

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

        # Cabinet edit signal - handle locally
        self.sig_cabinet_edit.connect(self._handle_cabinet_edit)

    def _setup_styling(self) -> None:
        """Apply modern styling with the main application theme."""
        # Apply main application theme to the dialog and all child widgets
        theme = get_theme(self.is_dark_mode)
        self.setStyleSheet(theme)

        # Set property classes for individual components for additional styling
        self.setProperty("class", "dialog")

        # Ensure theme is applied to all child widgets
        self._apply_theme_to_children()

    def _apply_theme_to_children(self) -> None:
        """Apply theme to all child widgets to ensure consistent styling."""
        try:
            theme = get_theme(self.is_dark_mode)

            # Apply theme to major components
            for widget in [self.header_bar, self.toolbar, self.central_widget]:
                if widget:
                    widget.setStyleSheet(theme)
        except Exception as e:
            logger.warning(f"Failed to apply theme to children: {e}")

    def apply_card_order(self, ordered_cabinets: List[ProjectCabinet]) -> None:
        """
        Apply the given cabinet order to the view.

        This method is called by the controller when data changes.
        It rebuilds the layout in the order provided by controller.

        Args:
            ordered_cabinets: List of cabinets in the desired display order
        """
        try:
            # Update cached cabinet list
            self.cabinets = ordered_cabinets

            # Update header info with project details
            self._update_header_info()

            # Check if we can avoid full rebuild by just reordering existing cards
            if self._can_reorder_existing_cards(ordered_cabinets):
                self._reorder_existing_cards(ordered_cabinets)
                return

            # Full rebuild needed
            self._rebuild_all_cards(ordered_cabinets)

        except Exception as e:
            logger.exception("Error applying card order")
            self._show_error(f"Błąd podczas odświeżania widoku: {e}")

    def _can_reorder_existing_cards(
        self, ordered_cabinets: List[ProjectCabinet]
    ) -> bool:
        """Check if we can reorder existing cards instead of rebuilding all."""
        if len(ordered_cabinets) != len(self._cards_by_id):
            return False  # Different number of cards

        # Check if all cabinets have existing cards
        for cabinet in ordered_cabinets:
            if cabinet.id not in self._cards_by_id:
                return False

        return True

    def _reorder_existing_cards(self, ordered_cabinets: List[ProjectCabinet]) -> None:
        """Reorder existing cards without rebuilding them."""
        # Clear layout without deleting widgets
        self._clear_flow_layout_without_deleting()

        # Re-add cards in the new order
        for cabinet in ordered_cabinets:
            if cabinet.id in self._cards_by_id:
                card = self._cards_by_id[cabinet.id]
                self.card_layout.addWidget(card)

        # Apply geometry
        if hasattr(self, "card_container"):
            self.card_layout.setGeometry(self.card_container.rect())

    def _rebuild_all_cards(self, ordered_cabinets: List[ProjectCabinet]) -> None:
        """Rebuild all cards from scratch."""
        # Clear existing cards
        self._clear_flow_layout_without_deleting()
        self._cards_by_id.clear()

        # Create cards in the provided order
        for cabinet in ordered_cabinets:
            card_data = self._cabinet_to_card_data(cabinet)
            card = CabinetCard(card_data)

            # Connect card signals
            self._connect_card_signals(card)

            self.card_layout.addWidget(card)
            self._cards_by_id[cabinet.id] = card

        # Update view state
        self._update_view_state()

        # Apply geometry
        if hasattr(self, "card_container"):
            self.card_layout.setGeometry(self.card_container.rect())

    def _clear_flow_layout_without_deleting(self) -> None:
        """Clear layout without deleting the widgets."""
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            # Don't delete the widget, just remove from layout

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

    def _on_sequence_changed_request(self, cabinet_id: int, new_sequence: int) -> None:
        """Handle sequence change request from card - delegate to controller."""
        if self.controller:
            self.controller.on_sequence_changed(cabinet_id, new_sequence)

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
            print(f"Error handling table double-click: {e}")

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
        """Handle cabinet edit request - opens the edit dialog."""
        from src.gui.add_cabinet_dialog import AddCabinetDialog

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

            # Open edit dialog with the cabinet ID
            dialog = AddCabinetDialog(
                db_session=self.session,
                project=self.project,
                cabinet_id=cabinet_id,
                parent=self,
            )

            if dialog.exec() == QDialog.Accepted:
                # Reload data to reflect changes
                if self.controller:
                    self.controller.load_data()
                self._show_success("Szafka zaktualizowana")

        except Exception as e:
            logger.exception("Error editing cabinet")
            self._show_error(f"Błąd podczas edycji szafki: {e}")

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
        """Convert ProjectCabinet to card data dict."""
        # Get dimensions from cabinet type or adhoc values
        width = height = depth = None

        if cabinet.cabinet_type:
            # Try to get dimensions from various components in order of preference
            # 1. Front panel (most representative for display)
            if cabinet.cabinet_type.front_w_mm and cabinet.cabinet_type.front_h_mm:
                width = cabinet.cabinet_type.front_w_mm
                height = cabinet.cabinet_type.front_h_mm
            # 2. Bok (side panel) if front not available
            elif cabinet.cabinet_type.bok_w_mm and cabinet.cabinet_type.bok_h_mm:
                width = cabinet.cabinet_type.bok_w_mm
                height = cabinet.cabinet_type.bok_h_mm
            # 3. Polka (shelf) as last resort
            elif cabinet.cabinet_type.polka_w_mm and cabinet.cabinet_type.polka_h_mm:
                width = cabinet.cabinet_type.polka_w_mm
                height = cabinet.cabinet_type.polka_h_mm

            # Set a reasonable default depth for kitchen cabinets
            if width and height:
                depth = 600.0  # Standard kitchen cabinet depth

        # Override with adhoc dimensions if available
        if cabinet.adhoc_width_mm:
            width = cabinet.adhoc_width_mm
        if cabinet.adhoc_height_mm:
            height = cabinet.adhoc_height_mm
        if cabinet.adhoc_depth_mm:
            depth = cabinet.adhoc_depth_mm

        return {
            "id": cabinet.id,
            "name": cabinet.cabinet_type.nazwa
            if cabinet.cabinet_type
            else "Niestandardowy",
            "sequence": cabinet.sequence_number or 1,
            "quantity": cabinet.quantity or 1,
            "body_color": cabinet.body_color or "#ffffff",
            "front_color": cabinet.front_color or "#ffffff",
            "width_mm": width,
            "height_mm": height,
            "depth_mm": depth,
            "kitchen_type": cabinet.cabinet_type.kitchen_type
            if cabinet.cabinet_type
            else None,
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
            self.stacked_widget.setCurrentWidget(self.card_scroll)
        else:
            self.stacked_widget.setCurrentWidget(self.empty_state)

    # Event handlers (stubs - implement as needed)
    def _on_close(self):
        """Handle dialog close."""
        self.accept()

    def _handle_add_from_catalog(self):
        """Handle add from catalog request."""
        self.sig_add_from_catalog.emit()

    def _handle_add_custom(self):
        """Handle add custom cabinet request."""
        self.sig_add_custom.emit()

    def _handle_export(self):
        """Handle export request."""
        self.sig_export.emit()

    def _handle_print(self):
        """Handle print request."""
        self.sig_print.emit()

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
                self.stacked_widget.setCurrentWidget(self.card_scroll)
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
            from PySide6.QtCore import QAbstractTableModel, Qt
            from PySide6.QtGui import QStandardItemModel, QStandardItem
            
            # Create a simple table model
            model = QStandardItemModel()
            headers = ["Sekwencja", "Nazwa", "Wymiary", "Kolor przód", "Kolor korpus", "Ilość"]
            model.setHorizontalHeaderLabels(headers)
            
            # Add cabinet data to the model
            for cabinet in self.cabinets:
                row = []
                
                # Sequence
                seq_item = QStandardItem(str(cabinet.sequence_number or ""))
                seq_item.setData(cabinet.id, Qt.ItemDataRole.UserRole)  # Store cabinet ID
                row.append(seq_item)
                
                # Name (from cabinet type)
                name = ""
                if hasattr(cabinet, 'cabinet_type') and cabinet.cabinet_type:
                    name = getattr(cabinet.cabinet_type, 'nazwa', '') or str(cabinet.cabinet_type.id)
                name_item = QStandardItem(name)
                row.append(name_item)
                
                # Dimensions (try different sources)
                dimensions = ""
                if cabinet.adhoc_width_mm and cabinet.adhoc_height_mm and cabinet.adhoc_depth_mm:
                    dimensions = f"{cabinet.adhoc_width_mm}×{cabinet.adhoc_height_mm}×{cabinet.adhoc_depth_mm}"
                else:
                    dimensions = "Auto"  # Calculated dimensions
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
