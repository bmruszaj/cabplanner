# src/gui/main_window.py
import os
import logging
import time
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QStatusBar,
    QToolBar,
    QMessageBox,
    QStackedWidget,
    QFrame,
    QScrollArea,
    QToolButton,
    QButtonGroup,
    QMenu,
)
from PySide6.QtCore import Qt, QModelIndex, QTimer
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from sqlalchemy.orm import Session

from src.gui.project_dialog import ProjectDialog
from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator
from src.services.settings_service import SettingsService
from src.gui.project_details.widget import ProjectDetailsWidget
from src.gui.settings_dialog import SettingsDialog

from src.services.catalog_service import CatalogService
from src.gui.resources.styles import get_theme
from src.gui.resources.resources import get_icon
from src.services.updater_service import UpdaterService

# Import refactored components
from .constants import CARD_WIDTH, CONTENT_MARGINS, LAYOUT_SPACING, ICON_SIZE
from .layouts.flow_layout import FlowLayout
from .widgets.project_card import ProjectCard
from .widgets.search_filter_bar import SearchFilterBar
from .widgets.empty_state import EmptyStateWidget
from .widgets.loading_overlay import LoadingOverlay
from .models.project_list_model import ProjectListModel
from .models.project_table_proxy import ProjectTableModel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main window of the Cabplanner application"""

    def __init__(self, db_session: Session):
        super().__init__()
        self.session = db_session
        self._last_clicked_project: Optional[object] = None
        self._selected_card_widget: Optional[ProjectCard] = None
        self._loading_overlay: Optional[LoadingOverlay] = None
        self._current_search_text = ""  # UX: Persist search text
        self._current_filter_type = ""  # UX: Persist filter type

        self.project_service = ProjectService(db_session)
        self.catalog_service = CatalogService(db_session)
        self.report_generator = ReportGenerator(db_session=db_session)
        self.settings_service = SettingsService(db_session)
        self.updater_service = UpdaterService(parent=self)
        self.is_dark_mode = self.settings_service.get_setting_value("dark_mode", False)

        # UX: Search debounce timer for better performance
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._apply_search_filter)

        self._build_main_window()
        self._setup_shortcuts()
        self.setup_connections()

        # UX: Initialize viewport width tracking
        QTimer.singleShot(0, self._initialize_viewport_tracking)

        self.load_projects()
        self._setup_update_check()

    def _initialize_viewport_tracking(self):
        """Initialize viewport width tracking after UI is fully constructed"""
        self._last_viewport_width = self.card_scroll.viewport().width()

    def _build_main_window(self):
        self.setWindowTitle(self.tr("Cabplanner"))
        # UX: Set minimum width to ensure at least one card column is visible
        # CARD_WIDTH (350) + margins + scrollbar + some padding
        min_width = CARD_WIDTH + 100  # 450px minimum
        self.setMinimumSize(min_width, 700)
        self._apply_theme()

        # Central widget and main layout
        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(*CONTENT_MARGINS)
        self._main_layout.setSpacing(LAYOUT_SPACING)

        # Build UI components
        self._build_header_area()
        self._build_divider()
        self._build_filter_area()
        self._build_divider()
        self._build_project_views()

        # Build window chrome
        self._build_menu_bar()
        self._build_toolbar()
        self._build_status_bar()

    def _build_header_area(self):
        """UX: Compact header bar with app title, project count, and update status"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # App title (left side)
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)

        app_title = QLabel("<h2>Cabplanner</h2>")
        app_title.setObjectName("appTitle")
        title_layout.addWidget(app_title)

        subtitle = QLabel(self.tr("System zarządzania projektami szafek kuchennych"))
        subtitle.setObjectName("appSubtitle")
        subtitle.setStyleSheet("color: gray; font-size: 12px;")
        title_layout.addWidget(subtitle)

        header_layout.addWidget(title_widget, 1)

        # Stats and status (right side)
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(8, 8, 8, 8)
        stats_layout.setSpacing(4)

        self.project_count_label = QLabel(f"0 {self.tr('projektów')}")
        self.project_count_label.setAlignment(Qt.AlignRight)
        self.project_count_label.setObjectName("projectCount")
        stats_layout.addWidget(self.project_count_label)

        self.update_status_label = QLabel(self.tr("Sprawdzanie aktualizacji..."))
        self.update_status_label.setAlignment(Qt.AlignRight)
        self.update_status_label.setObjectName("updateStatus")
        self.update_status_label.setStyleSheet("font-size: 11px; color: gray;")
        stats_layout.addWidget(self.update_status_label)

        stats_widget.setObjectName("headerStats")
        stats_widget.setProperty("class", "card")
        header_layout.addWidget(stats_widget)

        self._main_layout.addWidget(header)

    def _build_divider(self):
        """UX: Subtle visual divider between sections"""
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setObjectName("sectionDivider")
        self._main_layout.addWidget(divider)

    def _build_filter_area(self):
        """UX: Enhanced search and filter area with responsive layout"""
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)

        # Search and filter bar
        self.search_filter = SearchFilterBar()
        filter_layout.addWidget(self.search_filter, 1)  # Give search area flex space

        # UX: View toggle buttons - keep them grouped together without stretching
        view_toggle_widget = QWidget()
        view_toggle_layout = QHBoxLayout(view_toggle_widget)
        view_toggle_layout.setContentsMargins(8, 0, 0, 0)
        view_toggle_layout.setSpacing(2)  # Minimal spacing between buttons

        # UX: Professional toggle buttons with icons - fixed size
        self.btn_cards = QToolButton()
        self.btn_cards.setText(self.tr("Karty"))
        self.btn_cards.setIcon(get_icon("dashboard"))  # Use available dashboard icon
        self.btn_cards.setToolTip(self.tr("Przełącz na widok kart (Ctrl+1)"))
        self.btn_cards.setCheckable(True)
        self.btn_cards.setChecked(True)
        self.btn_cards.setAutoRaise(True)
        self.btn_cards.setMinimumWidth(60)  # Fixed minimum width
        self.btn_cards.setMaximumWidth(80)  # Fixed maximum width
        view_toggle_layout.addWidget(self.btn_cards)

        self.btn_table = QToolButton()
        self.btn_table.setText(self.tr("Tabela"))
        self.btn_table.setIcon(
            get_icon("filter")
        )  # Use available filter icon for table
        self.btn_table.setToolTip(self.tr("Przełącz na widok tabeli (Ctrl+2)"))
        self.btn_table.setCheckable(True)
        self.btn_table.setAutoRaise(True)
        self.btn_table.setMinimumWidth(60)  # Fixed minimum width
        self.btn_table.setMaximumWidth(80)  # Fixed maximum width
        view_toggle_layout.addWidget(self.btn_table)

        # UX: Button group for exclusive toggling between card and table views
        self.view_button_group = QButtonGroup(self)
        self.view_button_group.setExclusive(True)
        self.view_button_group.addButton(self.btn_cards)
        self.view_button_group.addButton(self.btn_table)
        self.btn_cards.setChecked(True)

        # Back button for project details view (initially hidden)
        self.btn_back = QToolButton()
        self.btn_back.setText(self.tr("Powrót"))
        self.btn_back.setIcon(get_icon("arrow_left"))
        self.btn_back.setToolTip(self.tr("Powrót do listy projektów"))
        self.btn_back.setAutoRaise(True)
        self.btn_back.setMinimumWidth(60)
        self.btn_back.setMaximumWidth(100)
        self.btn_back.setVisible(False)  # Hidden by default
        view_toggle_layout.addWidget(self.btn_back)

        # Add the toggle widget without stretch factor (0) to prevent expansion
        filter_layout.addWidget(view_toggle_widget, 0)
        self._main_layout.addWidget(filter_container)

    def _build_project_views(self):
        """UX: Enhanced project views with responsive cards and improved table"""
        # Container for stacked widget and empty state
        self.view_container = QWidget()
        container_layout = QVBoxLayout(self.view_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget for views
        self.stack = QStackedWidget()

        # UX: Responsive card view with flow layout
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.card_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.card_container = QWidget()
        # UX: Use FlowLayout for smooth responsive behavior
        self.card_layout = FlowLayout(self.card_container, margin=8, spacing=12)
        self.card_container.setLayout(self.card_layout)

        self.card_scroll.setWidget(self.card_container)
        self.stack.addWidget(self.card_scroll)

        # Table view
        raw_model = ProjectListModel([])
        self.table = QTableView()
        # UX: Enhanced table with sorting, alternating rows, better styling
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Order number
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Kitchen type
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Client
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Date

        proxy = ProjectTableModel(raw_model)
        self.table.setModel(proxy)

        # UX: Add context menu for table
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_table_context_menu)

        self.stack.addWidget(self.table)

        # Project details view (in-window)
        self.project_details_widget = None
        self.current_project_for_details = None

        # UX: Empty state widget
        self.empty_state = EmptyStateWidget()
        self.empty_state.newProjectRequested.connect(self._handle_empty_state_action)
        self.empty_state.hide()

        container_layout.addWidget(self.stack)
        container_layout.addWidget(self.empty_state)
        self._main_layout.addWidget(self.view_container)

        # UX: Store existing cards to avoid recreation
        self._project_cards = {}  # project.id -> ProjectCard

    def _build_menu_bar(self):
        """Enhanced menu bar with all required shortcuts"""
        mb = self.menuBar()

        # File menu
        fm = mb.addMenu(self.tr("Plik"))
        self._make_action(
            fm, self.tr("Nowy projekt"), "Ctrl+N", self.on_new_project, "new_project"
        )
        fm.addSeparator()
        self._make_action(
            fm, self.tr("Eksportuj do Word"), "Ctrl+E", self.on_export_project, "export"
        )

        fm.addSeparator()
        self._make_action(fm, self.tr("Zamknij"), "Alt+F4", self.close)

        # Edit menu
        em = mb.addMenu(self.tr("Edycja"))
        self._make_action(
            em, self.tr("Usuń projekt"), "Del", self.on_delete_project, "delete"
        )
        em.addSeparator()
        self._make_action(
            em, self.tr("Ustawienia"), "Ctrl+,", self.on_open_settings, "settings"
        )

        # View menu
        vm = mb.addMenu(self.tr("Widok"))
        self._make_action(
            vm, self.tr("Karty"), "Ctrl+1", lambda: self.on_switch_view(0), "dashboard"
        )
        self._make_action(
            vm, self.tr("Tabela"), "Ctrl+2", lambda: self.on_switch_view(1), "filter"
        )
        vm.addSeparator()
        self._make_action(
            vm, self.tr("Przełącz motyw (jasny/ciemny)"), "Ctrl+T", self.on_toggle_theme
        )

        # Tools menu
        tm = mb.addMenu(self.tr("Narzędzia"))
        self._make_action(
            tm, self.tr("Katalog szafek"), "Ctrl+K", self.on_open_catalog, "catalog"
        )

        # Help menu
        hm = mb.addMenu(self.tr("Pomoc"))
        self._make_action(hm, self.tr("O programie"), None, self.on_show_about)

    def _build_toolbar(self):
        """UX: Enhanced toolbar with tooltips and status tips"""
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(ICON_SIZE)
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(tb)

        toolbar_actions = [
            (
                "new_project",
                self.tr("Nowy projekt"),
                self.tr("Utwórz nowy projekt"),
                self.on_new_project,
            ),
            (
                "export",
                self.tr("Eksportuj"),
                self.tr("Eksportuj wybrany projekt do Word"),
                self.on_export_project,
            ),
            (
                "delete",
                self.tr("Usuń"),
                self.tr("Usuń wybrany projekt"),
                self.on_delete_project,
            ),
            (None, None, None, None),  # Separator
            (
                "catalog",
                self.tr("Katalog"),
                self.tr("Otwórz katalog szafek"),
                self.on_open_catalog,
            ),
            (
                "settings",
                self.tr("Ustawienia"),
                self.tr("Otwórz ustawienia aplikacji"),
                self.on_open_settings,
            ),
        ]

        for icon, text, tooltip, slot in toolbar_actions:
            if icon is None:
                tb.addSeparator()
            else:
                act = QAction(get_icon(icon), text, self)
                act.setToolTip(tooltip)
                act.setStatusTip(tooltip)
                act.triggered.connect(slot)
                tb.addAction(act)

    def _build_status_bar(self):
        """UX: Status bar for non-blocking feedback"""
        self.status = QStatusBar()
        self.status.showMessage(self.tr("Gotowy"))
        self.setStatusBar(self.status)

    def _setup_shortcuts(self):
        """UX: Additional keyboard shortcuts for better accessibility"""
        # Focus search shortcut
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_filter.focus_search)

    def _make_action(self, menu, text, shortcut=None, slot=None, icon=None):
        """UX: Helper to create menu actions with consistent styling"""
        action = QAction(text, self)
        if icon:
            action.setIcon(get_icon(icon))
        if shortcut:
            action.setShortcut(shortcut)
        if slot:
            action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def setup_connections(self):
        """Wire up dynamic signals"""
        # Search and filter
        self.search_filter.searchTextChanged.connect(self._on_search_text_changed)
        self.search_filter.filterChanged.connect(self.on_filter_type)

        # View toggle
        self.btn_cards.clicked.connect(lambda: self.on_switch_view(0))
        self.btn_table.clicked.connect(lambda: self.on_switch_view(1))
        self.btn_back.clicked.connect(self.on_back_to_list)

        # Table events
        sel_model = self.table.selectionModel()
        sel_model.selectionChanged.connect(self._on_table_selection_changed)
        self.table.doubleClicked.connect(self._on_table_double_click)

        # UX: Keyboard navigation for table
        self.table.installEventFilter(self)

    def eventFilter(self, obj, event):
        """UX: Handle keyboard events for table navigation"""
        if obj == self.table and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self._on_table_double_click(self.table.currentIndex())
                return True
            elif event.key() == Qt.Key_Delete:
                self.on_delete_project()
                return True
        return super().eventFilter(obj, event)

    def _on_search_text_changed(self, text: str):
        """UX: Debounced search for better performance"""
        self._current_search_text = text
        self._search_timer.stop()
        self._search_timer.start()

    def _apply_search_filter(self):
        """Apply the actual search filter after debounce delay"""
        self.on_filter_text(self._current_search_text)

    def _show_loading(self, show: bool):
        """UX: Show/hide loading overlay"""
        if show:
            if not self._loading_overlay:
                self._loading_overlay = LoadingOverlay(self.view_container)
            self._loading_overlay.show()
            self._loading_overlay.raise_()
        else:
            if self._loading_overlay:
                self._loading_overlay.hide()

    def _show_empty_state(self, show: bool, is_search_result=False):
        """UX: Show/hide empty state based on context"""
        if show:
            if is_search_result:
                self.empty_state.set_no_results_state()
            else:
                self.empty_state.set_empty_projects_state()
            self.empty_state.show()
            self.stack.hide()
        else:
            self.empty_state.hide()
            self.stack.show()

    def _handle_empty_state_action(self):
        """Handle empty state action button click"""
        # Check if it's "clear filters" or "new project"
        if self._current_search_text or self._current_filter_type:
            # Clear filters
            self.search_filter.search_input.clear()
            self.search_filter.filter_combo.setCurrentIndex(0)
        else:
            # New project
            self.on_new_project()

    def _get_visible_card_count(self) -> int:
        """Count visible cards in the layout"""
        count = 0
        for i in range(self.card_layout.count()):
            item = self.card_layout.itemAt(i)
            if item and item.widget() and item.widget().isVisible():
                count += 1
        return count

    def _update_card_grid_layout(self):
        """UX: Update card visibility based on filters without recreating widgets"""
        # Get projects from model
        model = self.table.model().sourceModel()
        projects = model._projects

        # Filter projects based on current filters
        filtered_projects = []
        for project in projects:
            if self._should_show_project(project):
                filtered_projects.append(project)

        if not filtered_projects:
            self._show_empty_state(
                True, bool(self._current_search_text or self._current_filter_type)
            )
            return
        else:
            self._show_empty_state(False)

        # Update existing cards and create new ones as needed
        self._sync_cards_with_projects(filtered_projects)

        # Performance: invalidate layout to trigger re-layout in next event cycle
        self.card_layout.invalidate()

        # Clear selection if selected project is no longer visible
        self._after_cards_refreshed()

    def _after_cards_refreshed(self):
        """Clear selection if the selected project isn't visible due to filtering"""
        if self._last_clicked_project:
            pid = self._last_clicked_project.id
            card = self._project_cards.get(pid)
            if not (card and card.isVisible()):
                self._last_clicked_project = None
                if self._selected_card_widget:
                    self._selected_card_widget.set_selected(False)
                    self._selected_card_widget = None
                self.status.clearMessage()

    def _update_counts(self):
        """Update project count display based on current filters"""
        model = self.table.model().sourceModel()
        projects = model._projects
        visible_count = len([p for p in projects if self._should_show_project(p)])
        total_count = len(projects)

        if visible_count == total_count:
            count_text = f"{total_count} {self.tr('projektów')}"
        else:
            count_text = f"{visible_count} / {total_count} {self.tr('projektów')}"
        self.project_count_label.setText(count_text)

    def _sync_cards_with_projects(self, projects):
        """UX: Synchronize cards with project list without unnecessary recreation"""
        # Visible subset - projects that should be shown based on current filters
        visible_ids = {p.id for p in projects}

        # Performance optimization: only toggle cards that change state
        current_visible = {
            pid for pid, c in self._project_cards.items() if c.isVisible()
        }

        # Show cards that should be visible but aren't
        for pid in visible_ids - current_visible:
            if pid in self._project_cards:
                self._project_cards[pid].show()

        # Hide cards that are visible but shouldn't be
        for pid in current_visible - visible_ids:
            self._project_cards[pid].hide()

        # Create missing cards for visible projects that don't have cards yet
        # and update existing cards with fresh data
        for project in projects:
            if project.id not in self._project_cards:
                card = self._create_project_card(project)
                self._project_cards[project.id] = card
                self.card_layout.addWidget(card)
            else:
                # Update existing card with fresh data from database
                self._project_cards[project.id].update_project_data(project)

        # Remove cards only for projects that truly disappeared from the DB
        # (not just filtered out)
        all_project_ids = {p.id for p in self.table.model().sourceModel()._projects}
        stale_project_ids = [
            pid
            for pid in list(self._project_cards.keys())
            if pid not in all_project_ids
        ]

        for project_id in stale_project_ids:
            card = self._project_cards.pop(project_id)
            self.card_layout.removeWidget(card)
            card.setParent(None)

    def _create_project_card(self, project) -> ProjectCard:
        """UX: Factory method to create a project card with all connections"""
        card = ProjectCard(project)
        card.clicked.connect(lambda c, w=card: self._on_card_clicked(w))
        card.doubleClicked.connect(
            lambda c, w=card: self.open_project_in_window(w.project)
        )
        card.editRequested.connect(lambda p: self.on_edit_project(p))
        card.exportRequested.connect(lambda p: self._perform_report_action(p, "open"))

        card.deleteRequested.connect(lambda p: self._delete_specific_project(p))
        card.openInNewWindowRequested.connect(lambda p: self.on_open_details(p))
        return card

    def _should_show_project(self, project) -> bool:
        """Check if project should be visible based on current filters"""
        # Type filter
        if (
            self._current_filter_type
            and project.kitchen_type != self._current_filter_type
        ):
            return False

        # Text filter
        if self._current_search_text:
            search_text = self._current_search_text.lower()
            return (
                search_text in project.name.lower()
                or (project.client_name and search_text in project.client_name.lower())
                or search_text in project.kitchen_type.lower()
            )

        return True

    def load_projects(self):
        """Enhanced project loading with loading state and responsive updates"""
        logger.debug("load_projects() called")
        self._show_loading(True)

        try:
            projects = self.project_service.list_projects()
            logger.debug(f"Loaded {len(projects)} projects from database")

            # Update table model
            raw_model = self.table.model().sourceModel()
            raw_model.update_projects(projects)
            logger.debug("Table model updated")

            # Update card layout (this will handle filtering and visibility)
            self._update_card_grid_layout()
            logger.debug("Card grid layout updated")

            # Update stats
            self._update_counts()
            logger.debug("Counts updated")

            # Update status
            if not projects:
                self._show_empty_state(True, False)
                self.status.showMessage(self.tr("Brak projektów"))
            else:
                self._show_empty_state(False)
                self.status.showMessage(
                    self.tr("Załadowano {0} projektów").format(len(projects))
                )

        except Exception as e:
            logger.error(f"Error loading projects: {e}")
            self.status.showMessage(self.tr("Błąd podczas ładowania projektów"))
        finally:
            self._show_loading(False)

    def _clear_card_layout(self):
        """Clear all widgets from card layout"""
        # UX: Clear layout without destroying widgets (for reuse)
        self.card_layout.clear_layout()
        # Clear the project cards dict when doing a full clear
        for card in self._project_cards.values():
            card.setParent(None)
        self._project_cards.clear()

    def _get_current_project(self) -> Optional[object]:
        """Get currently selected project from active view"""
        if self.stack.currentIndex() == 0:  # Card view
            return self._last_clicked_project
        else:  # Table view
            rows = self.table.selectionModel().selectedRows()
            if not rows:
                return None
            src_idx = self.table.model().mapToSource(rows[0])
            return self.table.model().sourceModel().get_project_at_row(src_idx.row())

    def _sync_selection_to_cards(self, project):
        """UX: Synchronize selection to card view"""
        for project_id, card in self._project_cards.items():
            if card.isVisible():
                is_selected = card.project == project
                card.set_selected(is_selected)
                if is_selected:
                    self._selected_card_widget = card

    def _sync_selection_to_table(self, project):
        """UX: Synchronize selection to table view"""
        if not project:
            return

        model = self.table.model()
        source_model = model.sourceModel()

        for row in range(source_model.rowCount()):
            if source_model.get_project_at_row(row) == project:
                source_index = source_model.index(row, 0)
                proxy_index = model.mapFromSource(source_index)
                if proxy_index.isValid():
                    self.table.selectRow(proxy_index.row())
                    self.table.scrollTo(proxy_index)
                break

    def _show_table_context_menu(self, position):
        """UX: Context menu for table view"""
        index = self.table.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu(self)
        project = self._get_current_project()

        if project:
            menu.addAction(
                get_icon("edit"),
                self.tr("Otwórz szczegóły"),
                lambda: self.open_project_in_window(project),
            )
            menu.addAction(
                get_icon("project"),
                self.tr("Otwórz w nowym oknie"),
                lambda: self.on_open_details(project),
            )
            menu.addAction(
                get_icon("edit"),
                self.tr("Edytuj projekt"),
                lambda: self.on_edit_project(project),
            )
            menu.addSeparator()
            menu.addAction(
                get_icon("export"),
                self.tr("Eksportuj"),
                lambda: self._perform_report_action(project, "open"),
            )

            menu.addSeparator()
            menu.addAction(
                get_icon("delete"),
                self.tr("Usuń"),
                lambda: self._delete_specific_project(project),
            )

        menu.exec(self.table.mapToGlobal(position))

    def _perform_report_action(self, project, action: str):
        """UX: Enhanced report action with better user feedback"""
        if not project:
            self.status.showMessage(self.tr("Wybierz projekt aby wykonać akcję"))
            return

        try:
            self.status.showMessage(self.tr("Generowanie raportu..."))

            # Get default project path from settings
            default_path = self.settings_service.get_setting_value(
                "default_project_path",
                os.path.join(os.path.expanduser("~"), "Documents", "CabPlanner"),
            )
            output_dir = os.path.join(default_path, "reports")

            path = self.report_generator.generate(project, output_dir=output_dir)

            os.startfile(path)
            # UX: Non-blocking status message instead of modal dialog
            self.status.showMessage(
                self.tr("Eksport zakończony: {0}").format(os.path.basename(path)),
                3000,
            )

        except Exception as e:
            logger.error(
                f"Error performing report action ({action}): {e}", exc_info=True
            )
            QMessageBox.critical(
                self,
                self.tr("Błąd"),
                self.tr("Nie udało się wykonać akcji raportu: {0}").format(str(e)),
            )
            self.status.showMessage(self.tr("Błąd podczas generowania raportu"))

    def _delete_specific_project(self, project):
        """Delete a specific project with confirmation"""
        if not project:
            return

        reply = QMessageBox.question(
            self,
            self.tr("Usuń projekt"),
            self.tr("Czy na pewno chcesz usunąć projekt '{0}'?").format(project.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                self.project_service.delete_project(project.id)
                self.load_projects()
                self.status.showMessage(
                    self.tr("Projekt '{0}' został usunięty").format(project.name)
                )
                # Clear selection
                self._last_clicked_project = None
                self._selected_card_widget = None
            except Exception as e:
                logger.error(f"Error deleting project: {e}")
                QMessageBox.critical(
                    self,
                    self.tr("Błąd"),
                    self.tr("Nie udało się usunąć projektu: {0}").format(str(e)),
                )

    def _on_card_clicked(self, card_widget: ProjectCard):
        """UX: Enhanced card selection with visual feedback and sync"""
        project = card_widget.project
        self._last_clicked_project = project

        # Clear previous selection
        if self._selected_card_widget and self._selected_card_widget != card_widget:
            self._selected_card_widget.set_selected(False)

        # Set new selection
        card_widget.set_selected(True)
        self._selected_card_widget = card_widget

        # Sync to table if in table view later
        self._sync_selection_to_table(project)

        # Update status
        self.status.showMessage(self.tr("Wybrano projekt: {0}").format(project.name))

    def _on_table_selection_changed(self, selected, deselected):
        """UX: Enhanced table selection with card sync"""
        project = self._get_current_project()
        if project:
            self._last_clicked_project = project
            self._sync_selection_to_cards(project)
            self.status.showMessage(
                self.tr("Wybrano projekt: {0}").format(project.name)
            )
        else:
            self.status.clearMessage()

    def _on_table_double_click(self, index: QModelIndex):
        """Handle table double-click to open project details"""
        if not index.isValid():
            return
        src = self.table.model().mapToSource(index)
        project = self.table.model().sourceModel().get_project_at_row(src.row())
        if project:
            self.open_project_in_window(project)

    # --- Action Handlers ---

    def on_new_project(self):
        """UX: Enhanced new project creation with better feedback"""
        try:
            dlg = ProjectDialog(self.session, parent=self)
            if dlg.exec():
                self.load_projects()
                self.status.showMessage(self.tr("Utworzono nowy projekt"), 3000)
        except Exception as e:
            logger.error(f"Error creating new project: {e}")
            QMessageBox.critical(
                self,
                self.tr("Błąd"),
                self.tr("Nie udało się utworzyć nowego projektu: {0}").format(str(e)),
            )

    def on_delete_project(self):
        """Delete currently selected project (only works from project list view)"""
        # Check if we're in the project details view - if so, don't delete the project
        # The Delete key in project details should delete the selected cabinet instead
        if (
            self.project_details_widget is not None
            and self.stack.currentWidget() == self.project_details_widget
        ):
            # We're in project details view - delegate to cabinet deletion
            if hasattr(self.project_details_widget, "details_view"):
                view = self.project_details_widget.details_view
                if hasattr(view, "_delete_selected_cabinet"):
                    view._delete_selected_cabinet()
            return

        project = self._get_current_project()
        if not project:
            self.status.showMessage(self.tr("Wybierz projekt do usunięcia"))
            return
        self._delete_specific_project(project)

    def on_export_project(self):
        """Export currently selected project"""
        project = self._get_current_project()
        if not project:
            self.status.showMessage(self.tr("Wybierz projekt do eksportu"))
            return
        self._perform_report_action(project, "open")

    def on_edit_project(self, project):
        """Open project dialog in edit mode"""
        if not project:
            self.status.showMessage(self.tr("Wybierz projekt do edycji"))
            return

        try:
            logger.debug(f"Opening edit dialog for project: {project.id}")
            dlg = ProjectDialog(self.session, project_id=project.id, parent=self)
            result = dlg.exec()
            logger.debug(f"Dialog result: {result}")
            if result:
                logger.debug("Dialog accepted, reloading projects...")
                self.load_projects()
                self.status.showMessage(self.tr("Projekt zaktualizowany"), 2000)
            else:
                logger.debug("Dialog was cancelled")
        except Exception as e:
            logger.error(f"Error editing project: {e}")
            QMessageBox.critical(
                self,
                self.tr("Błąd"),
                self.tr("Nie udało się otworzyć edycji projektu: {0}").format(str(e)),
            )

    def on_open_details(self, project):
        """Open project details in separate window using widget-based approach"""
        if not project:
            self.status.showMessage(self.tr("Wybierz projekt do otwarcia"))
            return

        try:
            # Create project details widget (not dialog)
            details_widget = ProjectDetailsWidget(
                session=self.session, project=project, parent=self
            )

            # Set it up as a separate window
            details_widget.setWindowFlags(
                Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint
            )
            details_widget.resize(1000, 700)

            # Center on parent
            if self.geometry():
                parent_geometry = self.geometry()
                x = (
                    parent_geometry.x()
                    + (parent_geometry.width() - details_widget.width()) // 2
                )
                y = (
                    parent_geometry.y()
                    + (parent_geometry.height() - details_widget.height()) // 2
                )
                details_widget.move(max(0, x), max(0, y))

            # Show the window
            details_widget.show()
            details_widget.raise_()
            details_widget.activateWindow()

            # Connect close signal to refresh projects
            details_widget.closed.connect(self.load_projects)

        except Exception as e:
            logger.error(f"Error opening project details: {e}")
            QMessageBox.critical(
                self,
                self.tr("Błąd"),
                self.tr("Nie udało się otworzyć szczegółów projektu: {0}").format(
                    str(e)
                ),
            )

    def open_project_in_window(self, project):
        """Open project details in the same window (replace main view)"""
        if not project:
            self.status.showMessage(self.tr("Wybierz projekt do otwarcia"))
            return

        try:
            # Remove existing project details widget if any
            if self.project_details_widget:
                self.stack.removeWidget(self.project_details_widget)
                self.project_details_widget.deleteLater()
                self.project_details_widget = None

            # Start a per-operation debug timer
            _dbg_start_time = time.perf_counter()

            def _dbg(msg: str):
                print(
                    f"[DEBUG][{(time.perf_counter() - _dbg_start_time) * 1000:.1f}ms] {msg}"
                )

            _dbg(f"Loading data for project: {project.name}")
            # Load data FIRST before creating widget
            # This prevents any flash since widget will have data when shown
            project_service = ProjectService(self.session)
            cabinets = project_service.list_cabinets(project.id)
            _dbg(f"Loaded {len(cabinets)} cabinets")

            _dbg("Creating ProjectDetailsWidget...")
            # Create project details widget (widget-based, no dialog)
            self.project_details_widget = ProjectDetailsWidget(
                session=self.session, project=project, parent=self
            )

            # Connect export signal once the details_view is available
            self._connect_project_details_signals()

            _dbg("Widget created")

            # CRITICAL: Hide the widget completely before any operations
            self.project_details_widget.setVisible(False)
            self.project_details_widget.hide()

            # Also hide the embedded view to prevent any flashing
            if (
                hasattr(self.project_details_widget, "details_view")
                and self.project_details_widget.details_view is not None
            ):
                self.project_details_widget.details_view.setVisible(False)
                self.project_details_widget.details_view.hide()

            self.current_project_for_details = project

            _dbg("Adding to stack...")
            # Add to stack while still hidden
            self.stack.addWidget(self.project_details_widget)

            _dbg("Setting current widget...")
            # Switch to the widget (it's still hidden)
            self.stack.setCurrentWidget(self.project_details_widget)

            _dbg("Keeping widget hidden until data is applied to avoid flash")

            # NOW load data asynchronously to populate the visible widget
            _dbg("Scheduling data loading...")
            from PySide6.QtCore import QTimer

            def load_data_deferred():
                _dbg("Loading data asynchronously...")
                try:
                    # Wait for heavy UI setup to complete
                    if (
                        not hasattr(self.project_details_widget, "details_view")
                        or not self.project_details_widget.details_view
                    ):
                        # UI not ready yet, try again in a bit
                        QTimer.singleShot(20, load_data_deferred)
                        return

                    # Pre-load the data into the widget
                    if hasattr(self.project_details_widget, "details_view") and hasattr(
                        self.project_details_widget.details_view, "controller"
                    ):
                        controller = self.project_details_widget.details_view.controller
                        view = self.project_details_widget.details_view
                        controller.cabinets = cabinets

                        # Temporarily disconnect signals to prevent async updates
                        try:
                            controller.data_loaded.disconnect(view.apply_card_order)
                        except Exception:
                            pass  # Signal might not be connected yet

                        # Apply data directly to view synchronously (bypass signals)
                        from src.domain.sorting import sort_cabinets

                        ordered_cabinets = sort_cabinets(cabinets)

                        # Call apply_card_order directly instead of emitting signal
                        view.apply_card_order(ordered_cabinets)
                        # Mark data as loaded to prevent duplicate loading
                        view._data_loaded = True

                        # Reconnect signals for future updates
                        controller.data_loaded.connect(view.apply_card_order)

                        # Now that heavy UI exists and data has been applied, show the widget
                        try:
                            self.project_details_widget.setVisible(True)
                            if (
                                hasattr(self.project_details_widget, "details_view")
                                and self.project_details_widget.details_view is not None
                            ):
                                self.project_details_widget.details_view.setVisible(
                                    True
                                )
                            _dbg("Widget shown after data applied")
                        except Exception:
                            pass
                    _dbg("Data loading complete")
                except Exception as e:
                    _dbg(f"Error loading data: {e}")

            # Schedule data loading for after UI setup
            QTimer.singleShot(100, load_data_deferred)  # Give time for heavy UI setup
            _dbg("Data loading scheduled")

            # Show back button and hide view toggle buttons
            self.btn_back.setVisible(True)
            self.btn_cards.setVisible(False)
            self.btn_table.setVisible(False)

            # Hide the search/filter bar while viewing project details in-window
            try:
                if hasattr(self, "search_filter") and self.search_filter is not None:
                    self.search_filter.setVisible(False)
            except Exception:
                pass

            # Update status
            self.status.showMessage(
                self.tr("Szczegóły projektu: {0}").format(project.name)
            )
            _dbg("Project details loading complete")

        except Exception as e:
            logger.error(f"Error opening project details in window: {e}")
            QMessageBox.critical(
                self,
                self.tr("Błąd"),
                self.tr("Nie udało się otworzyć szczegółów projektu: {0}").format(
                    str(e)
                ),
            )

    def _connect_project_details_signals(self):
        """Connect signals from ProjectDetailsWidget to main window handlers"""
        if not self.project_details_widget:
            return

        # Use a timer to connect signals after details_view is created
        def connect_when_ready():
            if (
                hasattr(self.project_details_widget, "details_view")
                and self.project_details_widget.details_view is not None
            ):
                # Connect export signal to use default_project_path
                try:
                    self.project_details_widget.details_view.sig_export.connect(
                        lambda: self._perform_report_action(
                            self.current_project_for_details, "open"
                        )
                    )
                    logger.debug("Connected project details export signal")
                except Exception as e:
                    logger.error(f"Failed to connect export signal: {e}")
            else:
                # Try again in 50ms if details_view isn't ready yet
                QTimer.singleShot(50, connect_when_ready)

        QTimer.singleShot(50, connect_when_ready)

    def on_back_to_list(self):
        """Return from project details view to main list view"""
        try:
            # Clean up project details widget
            if self.project_details_widget:
                self.stack.removeWidget(self.project_details_widget)
                self.project_details_widget.deleteLater()
                self.project_details_widget = None
                self.current_project_for_details = None

            # Show view toggle buttons and hide back button
            self.btn_back.setVisible(False)
            self.btn_cards.setVisible(True)
            self.btn_table.setVisible(True)

            # Restore visibility of the search/filter bar when returning to list
            try:
                if hasattr(self, "search_filter") and self.search_filter is not None:
                    self.search_filter.setVisible(True)
            except Exception:
                pass

            # Return to the previously selected view (cards or table)
            if self.btn_cards.isChecked():
                self.stack.setCurrentIndex(0)
            else:
                self.stack.setCurrentIndex(1)

            # Refresh projects to reflect any changes made in details view
            self.load_projects()

            # Update status
            self.status.showMessage(self.tr("Powrót do listy projektów"))

        except Exception as e:
            logger.error(f"Error returning to list view: {e}")

    def on_filter_text(self, text: str):
        """UX: Enhanced text filtering with table and card sync"""
        self._current_search_text = text

        # Update table filter
        proxy: ProjectTableModel = self.table.model()
        proxy.setFilterKeyColumn(-1)  # Search all columns
        proxy.setFilterRegularExpression(text)

        # Update card visibility
        self._update_card_grid_layout()

        # Update project count
        self._update_counts()

    def on_filter_type(self, kitchen_type: str):
        """UX: Enhanced type filtering"""
        self._current_filter_type = kitchen_type

        # Update table filter
        proxy: ProjectTableModel = self.table.model()
        proxy.setTypeFilter(kitchen_type)

        # Update card layout
        self._update_card_grid_layout()

        # Update project count
        self._update_counts()

    def on_switch_view(self, idx: int):
        """UX: Enhanced view switching with selection preservation"""
        # If we're currently in project details view, go back to list first
        if (
            self.project_details_widget
            and self.stack.currentWidget() == self.project_details_widget
        ):
            self.on_back_to_list()

        current_project = self._get_current_project()

        self.stack.setCurrentIndex(idx)
        self.btn_cards.setChecked(idx == 0)
        self.btn_table.setChecked(idx == 1)

        # Preserve selection across views
        if current_project:
            if idx == 0:  # Switching to cards
                self._sync_selection_to_cards(current_project)
            else:  # Switching to table
                self._sync_selection_to_table(current_project)

        view_name = self.tr("karty") if idx == 0 else self.tr("tabela")
        self.status.showMessage(
            self.tr("Przełączono na widok: {0}").format(view_name), 2000
        )

    def on_toggle_theme(self):
        """Toggle between light and dark theme"""
        self.is_dark_mode = not self.is_dark_mode
        self.settings_service.set_setting("dark_mode", self.is_dark_mode)
        self._apply_theme()

        theme_name = self.tr("ciemny") if self.is_dark_mode else self.tr("jasny")
        self.status.showMessage(
            self.tr("Przełączono na motyw: {0}").format(theme_name), 2000
        )

    def on_open_settings(self):
        """Open application settings"""
        try:
            dlg = SettingsDialog(self.session, parent=self)
            if dlg.exec():
                # Refresh theme setting
                self.is_dark_mode = self.settings_service.get_setting_value(
                    "dark_mode", False
                )
                self._apply_theme()
                self.status.showMessage(self.tr("Ustawienia zapisane"), 3000)
        except Exception as e:
            logger.error(f"Error opening settings: {e}")
            QMessageBox.critical(
                self,
                self.tr("Błąd"),
                self.tr("Nie udało się otworzyć ustawień: {0}").format(str(e)),
            )

    def on_open_catalog(self):
        """Open cabinet catalog window"""
        try:
            # Use the new unified catalog in manage mode from main window
            from src.gui.cabinet_catalog.window import CatalogWindow

            win = CatalogWindow(
                catalog_service=self.catalog_service,
                project_service=self.project_service,
                initial_mode="manage",
                target_project=None,
                parent=self,
            )
            win.exec()
        except Exception as e:
            logger.error(f"Error opening catalog: {e}")
            QMessageBox.critical(
                self,
                self.tr("Błąd"),
                self.tr("Nie udało się otworzyć katalogu: {0}").format(str(e)),
            )

    def on_show_about(self):
        """Show about dialog"""
        try:
            from src.version import get_full_version_info

            QMessageBox.about(
                self,
                self.tr("O programie"),
                f"<h1>Cabplanner</h1><p>{get_full_version_info()}</p><p>© 2025 Cabplanner</p>",
            )
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}")

    def _apply_theme(self):
        """Apply current theme to the window"""
        self.setStyleSheet(get_theme(self.is_dark_mode))

    def resizeEvent(self, event):
        """Handle window resize for responsive card layout"""
        super().resizeEvent(event)
        # UX: Only update layout if card view is active and size changed significantly
        if self.stack.currentIndex() == 0 and hasattr(self, "_last_viewport_width"):
            current_width = self.card_scroll.viewport().width()

            # UX: Update on smaller threshold for narrow widths (better responsiveness)
            threshold = min(CARD_WIDTH // 3, 50)  # Smaller threshold for narrow windows
            if abs(current_width - self._last_viewport_width) > threshold:
                self._last_viewport_width = current_width
                # Debounce layout update to avoid excessive recomputation
                if hasattr(self, "_resize_timer"):
                    self._resize_timer.stop()
                else:
                    self._resize_timer = QTimer(self)
                    self._resize_timer.setSingleShot(True)
                    self._resize_timer.timeout.connect(self._on_resize_timeout)

                self._resize_timer.start(100)  # 100ms debounce
        elif not hasattr(self, "_last_viewport_width"):
            # Initialize viewport width tracking
            self._last_viewport_width = self.card_scroll.viewport().width()

    def _on_resize_timeout(self):
        """Handle debounced resize event"""
        # Performance: invalidate layout to trigger re-layout in next event cycle
        self.card_layout.invalidate()

    # --- Update System Integration ---

    def _setup_update_check(self):
        """UX: Non-blocking update check setup"""
        self.update_status_label.setText(self.tr("Sprawdzanie aktualizacji..."))
        QTimer.singleShot(1000, self._start_update_check)  # Slight delay for better UX

    def _start_update_check(self):
        """Start background update check"""
        try:
            if not self.updater_service.should_check_for_updates(self.settings_service):
                self.update_status_label.setText(self.tr("Sprawdzanie wyłączone"))
                return

            self.updater_service.update_check_complete.connect(
                self._on_update_check_complete
            )
            self.updater_service.check_for_updates(self.settings_service)

        except Exception as e:
            logger.exception("Error during startup update check: %s", e)
            self.update_status_label.setText(self.tr("Błąd sprawdzania"))

    def _on_update_check_complete(self, available: bool, current: str, latest: str):
        """UX: Enhanced update check completion with subtle notification"""
        try:
            if not available:
                self.update_status_label.setText(self.tr("Aktualna wersja"))
                self.status.showMessage(self.tr("Brak dostępnych aktualizacji"), 3000)
                return

            # UX: Subtle update indicator in header
            update_text = f"<a href='#' style='color: orange;'>{self.tr('Nowa wersja')} {latest}</a>"
            self.update_status_label.setText(update_text)
            self.update_status_label.setTextFormat(Qt.RichText)
            self.update_status_label.linkActivated.connect(self._show_update_dialog)

            # Status bar notification
            self.status.showMessage(
                self.tr("Dostępna nowa wersja: {0}").format(latest), 5000
            )

        except Exception as e:
            logger.exception("Error handling update check result: %s", e)
            self.update_status_label.setText(self.tr("Błąd aktualizacji"))

    def _show_update_dialog(self):
        """Show update dialog when user clicks update indicator"""
        try:
            from src.gui.update_dialog import UpdateDialog

            dialog = UpdateDialog(self.updater_service.current_version, parent=self)

            # Connect signals
            dialog.perform_update.connect(self.updater_service.perform_update)
            dialog.cancel_update.connect(self.updater_service.cancel_update)

            self.updater_service.update_progress.connect(dialog.on_update_progress)
            self.updater_service.update_complete.connect(dialog.on_update_complete)
            self.updater_service.update_failed.connect(dialog.on_update_failed)
            self.updater_service.update_check_failed.connect(dialog.update_check_failed)

            dialog.exec()

        except Exception as e:
            logger.exception("Error showing update dialog: %s", e)
