"""
Project Details View - UI-only dialog component.

This module contains the main ProjectDetailsView dialog which handles only UI concerns.
All business logic and data manipulation is delegated to controllers.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QWidget,
    QDialogButtonBox,
    QSplitter,
    QStackedWidget,
    QTableView,
)

from .widgets.header_bar import HeaderBar
from .widgets.toolbar import Toolbar
from .widgets.card_grid import CardGrid
from .widgets.client_sidebar import ClientSidebar
from .widgets.banners import BannerManager
from .constants import (
    HEADER_HEIGHT,
    TOOLBAR_HEIGHT,
    SIDEBAR_DEFAULT_WIDTH,
    CONTENT_MARGINS,
    VIEW_MODE_CARDS,
    VIEW_MODE_TABLE,
    SHORTCUTS,
    BUTTON_STYLESHEET,
    HEADER_STYLESHEET,
    SIDEBAR_STYLESHEET,
)

logger = logging.getLogger(__name__)


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

    # Signals for controller communication
    sig_search_changed = Signal(str)
    sig_view_mode_changed = Signal(str)  # 'cards' or 'table'
    sig_add_from_catalog = Signal()
    sig_add_custom = Signal()
    sig_export = Signal()
    sig_print = Signal()
    sig_client_save = Signal(dict)

    # Cabinet operation signals (relayed from widgets)
    sig_cabinet_qty_changed = Signal(int, int)  # cab_id, new_quantity
    sig_cabinet_edit = Signal(int)  # cab_id
    sig_cabinet_duplicate = Signal(int)  # cab_id
    sig_cabinet_delete = Signal(int)  # cab_id
    sig_cabinet_selected = Signal(int)  # cab_id

    def __init__(self, modal: bool = False, parent=None):
        """
        Initialize the project details view.

        Args:
            modal: Whether dialog should be modal
            parent: Parent widget
        """
        super().__init__(parent)
        self.modal = modal
        self.controller = None  # Will be set by controller.attach()
        self._current_view_mode = VIEW_MODE_CARDS

        self._setup_ui()
        self._setup_connections()
        self._setup_styling()

    def _setup_ui(self) -> None:
        """Set up the dialog UI components."""
        self.setWindowTitle("Szczegóły projektu")
        self.setMinimumSize(1200, 800)

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

        # Banner manager for notifications
        self.banner_manager = BannerManager()
        main_layout.addWidget(self.banner_manager)

        # Main content area with splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # Left side - central view area
        self._create_central_area()
        self.main_splitter.addWidget(self.central_widget)

        # Right side - client sidebar
        self.client_sidebar = ClientSidebar()
        self.client_sidebar.setMinimumWidth(SIDEBAR_DEFAULT_WIDTH)
        self.client_sidebar.setMaximumWidth(SIDEBAR_DEFAULT_WIDTH)
        self.main_splitter.addWidget(self.client_sidebar)

        # Set initial splitter sizes (central area takes most space)
        self.main_splitter.setSizes([800, SIDEBAR_DEFAULT_WIDTH])

        main_layout.addWidget(self.main_splitter)

        # Footer with dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.button(QDialogButtonBox.Close).setText("Zamknij")
        main_layout.addWidget(self.button_box)

    def _create_central_area(self) -> None:
        """Create the central stacked widget area."""
        self.central_widget = QWidget()
        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins(*CONTENT_MARGINS)
        central_layout.setSpacing(0)

        # Stacked widget for different view modes
        self.stacked_widget = QStackedWidget()

        # Card grid view
        self.card_grid = CardGrid()
        self.stacked_widget.addWidget(self.card_grid)

        # Table view placeholder (will be set by controller)
        self.table_view = None

        central_layout.addWidget(self.stacked_widget)

    def _setup_connections(self) -> None:
        """Set up signal connections."""
        # Dialog button
        self.button_box.rejected.connect(self._on_close)

        # Header bar signals
        self.header_bar.sig_export.connect(self._on_export)
        self.header_bar.sig_print.connect(self._on_print)

        # Toolbar signals
        self.toolbar.sig_add_from_catalog.connect(self._on_add_from_catalog)
        self.toolbar.sig_add_custom.connect(self._on_add_custom)
        self.toolbar.sig_search_changed.connect(self._on_search_changed)
        self.toolbar.sig_view_mode_changed.connect(self._on_view_mode_changed)

        # Client sidebar signals
        self.client_sidebar.sig_save.connect(self._on_client_data_changed)

        # Card grid signals (relay to controller)
        self.card_grid.sig_qty_changed.connect(self.sig_cabinet_qty_changed)
        self.card_grid.sig_edit.connect(self.sig_cabinet_edit)
        self.card_grid.sig_duplicate.connect(self.sig_cabinet_duplicate)
        self.card_grid.sig_delete.connect(self.sig_cabinet_delete)
        self.card_grid.sig_card_selected.connect(self.sig_cabinet_selected)

    def _setup_styling(self) -> None:
        """Apply modern styling with themes and button stylesheets."""
        # Apply main dialog styling
        self.setProperty("class", "dialog")

        # Apply component-specific stylesheets from constants
        combined_stylesheet = f"""
        {BUTTON_STYLESHEET}
        {HEADER_STYLESHEET}
        {SIDEBAR_STYLESHEET}
        """
        self.setStyleSheet(combined_stylesheet)

        # Set property classes for individual components
        self.header_bar.setProperty("class", "card")
        self.toolbar.setProperty("class", "toolbar")
        self.client_sidebar.setProperty("class", "card")

    def _on_close(self) -> None:
        """Handle dialog close."""
        if self.modal:
            self.reject()
        else:
            self.close()

    def _on_export(self, format_type: str) -> None:
        """Handle export request."""
        self.sig_export.emit()

    def _on_print(self) -> None:
        """Handle print request."""
        self.sig_print.emit()

    def _on_add_from_catalog(self) -> None:
        """Handle add from catalog request."""
        self.sig_add_from_catalog.emit()

    def _on_add_custom(self) -> None:
        """Handle add custom cabinet request."""
        self.sig_add_custom.emit()

    def _on_search_changed(self, search_text: str) -> None:
        """Handle search text change."""
        self.sig_search_changed.emit(search_text)

    def _on_view_mode_changed(self, mode: str) -> None:
        """Handle view mode change between cards and table."""
        self._current_view_mode = mode

        if mode == VIEW_MODE_CARDS:
            self.stacked_widget.setCurrentWidget(self.card_grid)
        elif mode == VIEW_MODE_TABLE and self.table_view:
            self.stacked_widget.setCurrentWidget(self.table_view)

        self.sig_view_mode_changed.emit(mode)
        logger.debug(f"View mode changed to: {mode}")

    def _on_client_data_changed(self, client_data: dict) -> None:
        """Handle client data changes."""
        self.sig_client_save.emit(client_data)
        logger.debug("Client data changed")

    # Public interface methods for controller
    def set_header_info(
        self, project_name: str, order_number: str, kitchen_type: str
    ) -> None:
        """
        Set header information.

        Args:
            project_name: Name of the project
            order_number: Project order number
            kitchen_type: Type of kitchen
        """
        self.setWindowTitle(f"Szczegóły projektu: {project_name}")
        # Update header bar with project info
        if hasattr(self, "header_bar") and self.header_bar:
            self.header_bar.set_project_info(
                title=project_name, order_number=order_number, kitchen_type=kitchen_type
            )
        logger.debug(f"Set header info: {project_name}, {order_number}, {kitchen_type}")

    def set_banner(self, message: str, banner_type: str = "info") -> None:
        """
        Show a banner message.

        Args:
            message: Message to display
            banner_type: Type of banner ("success", "info", "warning", "error")
        """
        if banner_type == "success":
            self.banner_manager.show_success(message)
        elif banner_type == "warning":
            self.banner_manager.show_warning(message)
        elif banner_type == "error":
            self.banner_manager.show_error(message)
        else:
            self.banner_manager.show_info(message)

    def set_view_mode(self, mode: str) -> None:
        """
        Set the current view mode.

        Args:
            mode: "cards" or "table"
        """
        if mode in (VIEW_MODE_CARDS, VIEW_MODE_TABLE):
            self.toolbar.set_view_mode(mode)
            self._on_view_mode_changed(mode)

    def stack_table_widget(self, table_view: QTableView) -> None:
        """
        Add a table view to the stacked widget with keyboard shortcuts.

        Args:
            table_view: Table view widget to add
        """
        if self.table_view:
            # Remove existing table view
            self.stacked_widget.removeWidget(self.table_view)
            self.table_view.setParent(None)

        self.table_view = table_view
        self.stacked_widget.addWidget(table_view)

        # Add keyboard shortcuts for table actions (preserved from legacy)
        from PySide6.QtGui import QShortcut, QKeySequence

        # Delete key for deleting selected rows
        delete_shortcut = QShortcut(QKeySequence(SHORTCUTS["delete"]), table_view)
        delete_shortcut.activated.connect(
            lambda: self.sig_cabinet_delete.emit(-1)
        )  # -1 for selected

        # F2 key for editing selected row
        edit_shortcut = QShortcut(QKeySequence(SHORTCUTS["edit"]), table_view)
        edit_shortcut.activated.connect(
            lambda: self.sig_cabinet_edit.emit(-1)
        )  # -1 for selected

        # Enter key for accepting/confirming actions
        enter_shortcut = QShortcut(QKeySequence(SHORTCUTS["accept"]), table_view)
        enter_shortcut.activated.connect(lambda: self.sig_cabinet_edit.emit(-1))

        # Switch to table view if current mode is table
        if self._current_view_mode == VIEW_MODE_TABLE:
            self.stacked_widget.setCurrentWidget(table_view)

        logger.debug("Stacked table widget with keyboard shortcuts")

    def set_client_info(self, client_name: str, project_info: str) -> None:
        """Update the client information in the sidebar."""
        self.client_sidebar.set_client_info(client_name, project_info)

    def get_current_view_mode(self) -> str:
        """Get the current view mode (grid or table)."""
        return self._current_view_mode

    def get_available_view_modes(self) -> list[str]:
        """Get list of available view modes."""
        return [VIEW_MODE_CARDS, VIEW_MODE_TABLE]

    def get_card_grid(self) -> CardGrid:
        """Get the card grid widget."""
        return self.card_grid

    def get_table_view(self) -> QTableView:
        """Get the table view widget."""
        return self.table_view

    def get_client_sidebar(self) -> ClientSidebar:
        """Get the client sidebar widget."""
        return self.client_sidebar

    def get_toolbar(self) -> Toolbar:
        """Get the toolbar widget."""
        return self.toolbar

    def get_header_bar(self) -> HeaderBar:
        """Get the header bar widget."""
        return self.header_bar

    def get_banner_manager(self) -> BannerManager:
        """Get the banner manager widget."""
        return self.banner_manager

    # Banner convenience methods for controllers
    def show_success_banner(self, message: str, timeout_ms: int = 2500) -> None:
        """Show a success banner."""
        self.banner_manager.show_success(message, timeout_ms)

    def show_info_banner(self, message: str, timeout_ms: int = 2500) -> None:
        """Show an info banner."""
        self.banner_manager.show_info(message, timeout_ms)

    def show_warning_banner(self, message: str, timeout_ms: int = 3500) -> None:
        """Show a warning banner."""
        self.banner_manager.show_warning(message, timeout_ms)

    def show_error_banner(self, message: str, timeout_ms: int = 0) -> None:
        """Show an error banner (no auto-hide by default)."""
        self.banner_manager.show_error(message, timeout_ms)

    def clear_banners(self) -> None:
        """Clear all banners."""
        self.banner_manager.clear_all()

    def show_dialog(self) -> None:
        """Show the dialog in the appropriate mode."""
        if self.modal:
            self.exec()
        else:
            self.show()

    def restore_geometry(self) -> None:
        """Restore dialog geometry from settings."""
        settings = QSettings()
        geometry = settings.value("project_details/geometry")
        if geometry:
            self.restoreGeometry(geometry)

        splitter_state = settings.value("project_details/splitter_state")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)

    def save_geometry(self) -> None:
        """Save dialog geometry to settings."""
        settings = QSettings()
        settings.setValue("project_details/geometry", self.saveGeometry())
        settings.setValue(
            "project_details/splitter_state", self.main_splitter.saveState()
        )

    def clear_cabinet_cards(self) -> None:
        """Clear all cabinet cards from the view."""
        if hasattr(self, "card_grid") and self.card_grid:
            self.card_grid.clear_cards()

    def add_cabinet_card(self, card_data: dict) -> None:
        """Add a cabinet card to the view."""
        if hasattr(self, "card_grid") and self.card_grid:
            self.card_grid.add_card(card_data)

    def set_table_model(self, model) -> None:
        """Set the table model for the table view."""
        if hasattr(self, "table_view") and self.table_view:
            self.table_view.setModel(model)

    def get_main_splitter(self):
        """Get the main splitter widget."""
        return getattr(self, "main_splitter", None)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.save_geometry()
        event.accept()
