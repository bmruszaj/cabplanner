"""
Catalog Dialog - Main cabinet catalog browser.

A modern 3-pane dialog for browsing and selecting cabinets from the catalog.
Features searching, filtering, sorting, and detailed configuration before adding.
"""

import logging
from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal, QTimer, QSettings
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QWidget,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QScrollArea,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QToolButton,
    QFrame,
    QMessageBox,
)
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from src.gui.resources.styles import get_theme
from src.gui.resources.resources import get_icon
from src.gui.common.layouts import ResponsiveFlowLayout
from src.services.settings_service import SettingsService
from .catalog_card import CatalogCard
from .catalog_service import CatalogService
from .catalog_models import CatalogItem

logger = logging.getLogger(__name__)


class CatalogDialog(QDialog):
    """
    Main catalog browser dialog.

    Features:
    - 3-pane layout: categories/filters, results grid, details/configuration
    - Search with Ctrl+F shortcut
    - Filtering by category, dimensions, type
    - Sorting by various fields
    - Pagination with lazy loading
    - Single/double click selection
    - Quick add and configured add
    """

    sig_cabinet_added = Signal(object)  # ProjectCabinet object
    sig_error = Signal(str)  # Error message

    def __init__(
        self,
        project,
        project_service,
        parent=None,
        session=None,
        catalog_service: CatalogService = None,
    ):
        super().__init__(parent)

        # Dependencies
        self.project = project
        self.project_service = project_service
        self.catalog = catalog_service or CatalogService(session)

        # State
        self._page = 1
        self._has_more = True
        self._selected_item: Optional[CatalogItem] = None
        self._selected_card: Optional[CatalogCard] = None
        self._cards: List[CatalogCard] = []
        self._selected_category_ids: set[int] = set()
        self.is_dark_mode = False
        if self.catalog and self.catalog.session:
            try:
                self.is_dark_mode = bool(
                    SettingsService(self.catalog.session).get_setting_value(
                        "dark_mode", False
                    )
                )
            except Exception:
                self.is_dark_mode = False

        # Settings for persistence
        self.settings = QSettings()

        self._setup_ui()
        self._setup_connections()
        self._setup_shortcuts()
        self._load_initial_data()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Katalog szafek")
        self.setModal(True)
        self.resize(1200, 800)
        self.setMinimumSize(1000, 600)

        # Apply theme
        self.setStyleSheet(get_theme(self.is_dark_mode))

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header: search + sort + view toggle
        self._create_header(main_layout)

        # 3-pane splitter
        self._create_main_content(main_layout)

        # Footer with global actions
        self._create_footer(main_layout)

    def _create_header(self, parent_layout: QVBoxLayout):
        """Create the header toolbar."""
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj w katalogu... (Ctrl+F)")
        self.search_input.setMinimumWidth(220)

        self.clear_search_btn = QToolButton()
        self.clear_search_btn.setIcon(get_icon("close"))
        self.clear_search_btn.setToolTip("Wyczyść wyszukiwanie")

        # Sort controls
        sort_label = QLabel("Sortuj:")
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Nazwa", "Kod", "Szerokość", "Wysokość", "Głębokość"])

        self.order_btn = QToolButton()
        self.order_btn.setIcon(get_icon("sort"))
        self.order_btn.setToolTip("Zmień kolejność sortowania")
        self.order_btn.setCheckable(True)

        # View mode toggle
        self.view_btn = QToolButton()
        self.view_btn.setIcon(get_icon("dashboard"))
        self.view_btn.setToolTip("Przełącz widok siatki/listy")
        self.view_btn.setCheckable(True)
        self.view_btn.setVisible(False)

        # Add to layout
        header_layout.addWidget(self.search_input, 1)
        header_layout.addWidget(self.clear_search_btn)
        header_layout.addWidget(sort_label)
        header_layout.addWidget(self.sort_combo)
        header_layout.addWidget(self.order_btn)
        header_layout.addStretch()
        header_layout.addWidget(self.view_btn)

        parent_layout.addLayout(header_layout)

    def _create_main_content(self, parent_layout: QVBoxLayout):
        """Create the main 3-pane content area."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: Categories and filters
        self._create_left_pane(splitter)

        # CENTER: Results grid
        self._create_center_pane(splitter)

        # RIGHT: Details and configuration
        self._create_right_pane(splitter)

        # Set splitter proportions
        splitter.setStretchFactor(0, 0)  # Fixed width for left
        splitter.setStretchFactor(1, 1)  # Flexible for center
        splitter.setStretchFactor(2, 0)  # Fixed width for right
        splitter.setSizes([280, 600, 320])

        parent_layout.addWidget(splitter, 1)

    def _create_left_pane(self, parent_splitter: QSplitter):
        """Create the left pane with categories and filters."""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Categories tree
        categories_label = QLabel("Kategorie")
        categories_label.setFont(QFont("Arial", 10, QFont.Weight.Medium))

        self.categories_tree = QTreeWidget()
        self.categories_tree.setHeaderHidden(True)
        self.categories_tree.setMinimumHeight(160)

        # Filters section
        filters_label = QLabel("Filtry")
        filters_label.setFont(QFont("Arial", 10, QFont.Weight.Medium))

        self.filters_widget = self._create_filters_panel()

        # Add to layout
        left_layout.addWidget(categories_label)
        left_layout.addWidget(self.categories_tree)
        left_layout.addWidget(filters_label)
        left_layout.addWidget(self.filters_widget)
        left_layout.addStretch()

        parent_splitter.addWidget(left_widget)

    def _create_filters_panel(self) -> QWidget:
        """Create the filters panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Width filter
        self.width_combo = QComboBox()
        self.width_combo.addItems(
            ["Szer.: dowolna", "300", "400", "450", "500", "600", "800", "900"]
        )

        # Type filter
        self.type_combo = QComboBox()
        self.type_combo.addItems(
            ["Typ: dowolny", "bazowa", "wisząca", "słupek", "szuflady"]
        )

        # Height filter
        self.height_combo = QComboBox()
        self.height_combo.addItems(
            ["Wys.: dowolna", "720", "900", "1200", "1800", "2000"]
        )

        # Clear filters button
        self.clear_filters_btn = QPushButton("Wyczyść filtry")
        self.clear_filters_btn.setProperty("class", "secondary")

        # Add to layout
        layout.addWidget(self.width_combo)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.height_combo)
        layout.addWidget(self.clear_filters_btn)

        return widget

    def _create_center_pane(self, parent_splitter: QSplitter):
        """Create the center pane with results grid."""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # Results scroll area
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.results_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Cards container with responsive layout
        self.cards_container = QWidget()
        self.cards_layout = ResponsiveFlowLayout(
            self.cards_container, margin=8, spacing=12
        )
        self.cards_container.setLayout(self.cards_layout)
        self.results_scroll.setWidget(self.cards_container)

        # Load more button
        self.load_more_btn = QPushButton("Załaduj więcej...")
        self.load_more_btn.setVisible(False)
        self.load_more_btn.setProperty("class", "secondary")

        # Add to layout
        center_layout.addWidget(self.results_scroll, 1)
        center_layout.addWidget(self.load_more_btn)

        parent_splitter.addWidget(center_widget)

    def _create_right_pane(self, parent_splitter: QSplitter):
        """Create the right pane with item details and configuration."""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        # Preview area
        self.preview_label = QLabel("Wybierz element z katalogu")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFrameShape(QFrame.Shape.StyledPanel)
        self.preview_label.setMinimumHeight(180)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 1px solid palette(mid);
                border-radius: 8px;
                color: palette(window-text);
                font-size: 14px;
            }
        """)

        # Configuration form
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(8)

        # Configuration controls
        self.variant_combo = QComboBox()
        self.body_color_combo = QComboBox()
        self.front_color_combo = QComboBox()
        self.handle_combo = QComboBox()

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setSuffix(" szt.")

        # Add form rows
        form_layout.addRow("Wariant:", self.variant_combo)
        form_layout.addRow("Kolor korpusu:", self.body_color_combo)
        form_layout.addRow("Kolor frontu:", self.front_color_combo)
        form_layout.addRow("Uchwyt:", self.handle_combo)
        form_layout.addRow("Ilość:", self.quantity_spin)

        # Options
        self.stay_open_checkbox = QCheckBox("Pozostań otwarte po dodaniu")

        # Action buttons
        self.add_btn = QPushButton("Dodaj do projektu")
        self.add_btn.setProperty("class", "primary")
        self.add_btn.setEnabled(False)

        # Add to layout
        right_layout.addWidget(self.preview_label)
        right_layout.addWidget(form_widget)
        right_layout.addStretch()
        right_layout.addWidget(self.stay_open_checkbox)
        right_layout.addWidget(self.add_btn)

        parent_splitter.addWidget(right_widget)

    def _create_footer(self, parent_layout: QVBoxLayout):
        """Create the footer with dialog buttons."""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.close_btn = QPushButton("Zamknij")
        self.close_btn.setProperty("class", "secondary")

        footer_layout.addWidget(self.close_btn)
        parent_layout.addLayout(footer_layout)

    def _setup_connections(self):
        """Set up signal connections."""
        # Header controls
        self.search_input.returnPressed.connect(self._reload_search)
        self.clear_search_btn.clicked.connect(lambda: self.search_input.setText(""))
        self.clear_search_btn.clicked.connect(self._reload_search)

        self.sort_combo.currentTextChanged.connect(self._reload_search)
        self.order_btn.clicked.connect(self._reload_search)

        # Left pane
        self.categories_tree.itemClicked.connect(self._on_category_selected)
        self.width_combo.currentTextChanged.connect(self._reload_search)
        self.type_combo.currentTextChanged.connect(self._reload_search)
        self.height_combo.currentTextChanged.connect(self._reload_search)
        self.clear_filters_btn.clicked.connect(self._clear_filters)

        # Center pane
        self.load_more_btn.clicked.connect(self._load_next_page)
        self.results_scroll.verticalScrollBar().valueChanged.connect(
            self._maybe_auto_load
        )

        # Right pane
        self.add_btn.clicked.connect(self._add_selected_item)

        # Footer
        self.close_btn.clicked.connect(self.reject)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Ctrl+F for search focus
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_input.setFocus)

        # Escape to close (store on self so it isn't garbage-collected)
        self.close_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.close_shortcut.activated.connect(self.reject)

    def _load_initial_data(self):
        """Load initial data (categories and first page of items)."""
        try:
            # Load categories
            self._populate_categories()

            # Load first page of items
            self._reload_search()

        except Exception as e:
            logger.exception("Error loading initial catalog data")
            self.sig_error.emit(f"Błąd podczas ładowania katalogu: {e}")

    def _populate_categories(self):
        """Populate the categories tree."""
        try:
            categories = self.catalog.get_categories()
            self.categories_tree.clear()

            # Build tree structure
            root_items = {}

            # First pass: create root items
            for category in categories:
                if category.parent_id is None:
                    item = QTreeWidgetItem([category.name])
                    item.setData(0, Qt.ItemDataRole.UserRole, category.id)
                    root_items[category.id] = item
                    self.categories_tree.addTopLevelItem(item)

            # Second pass: add children
            for category in categories:
                if category.parent_id is not None and category.parent_id in root_items:
                    child_item = QTreeWidgetItem([category.name])
                    child_item.setData(0, Qt.ItemDataRole.UserRole, category.id)
                    root_items[category.parent_id].addChild(child_item)

            # Expand all items
            self.categories_tree.expandAll()

        except Exception:
            logger.exception("Error populating categories")

    def _reload_search(self):
        """Reload search results from the beginning."""
        self._page = 1
        self._has_more = True
        self._clear_results()
        self._fetch_and_display_results()

    def _clear_results(self):
        """Clear current results."""
        # Clear cards
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        # Clear layout
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _fetch_and_display_results(self):
        """Fetch and display search results."""
        try:
            # Prepare search parameters
            query = self.search_input.text().strip()
            filters = self._get_current_filters()
            sort_field, sort_order = self._get_current_sort()

            # Fetch results
            items, has_more = self.catalog.search_items(
                query=query,
                filters=filters,
                sort=(sort_field, sort_order),
                page=self._page,
                page_size=20,
            )

            # Update state
            self._has_more = has_more

            # Create and add cards
            for item in items:
                card = CatalogCard(item)
                card.sig_select.connect(self._on_card_selected)
                card.sig_activate.connect(self._on_card_activated)

                self.cards_layout.addWidget(card)
                self._cards.append(card)

            # Update load more button
            self.load_more_btn.setVisible(self._has_more)

        except Exception as e:
            logger.exception("Error fetching catalog results")
            self.sig_error.emit(f"Błąd podczas wyszukiwania: {e}")

    def _get_current_filters(self) -> Dict[str, Any]:
        """Get current filter values."""
        filters = {
            "width": self.width_combo.currentText(),
            "kind": self.type_combo.currentText(),
            "height": self.height_combo.currentText(),
        }
        if self._selected_category_ids:
            filters["category_ids"] = list(self._selected_category_ids)
        return filters

    def _get_current_sort(self) -> tuple:
        """Get current sort field and order."""
        sort_map = {
            "Nazwa": "name",
            "Kod": "code",
            "Szerokość": "width",
            "Wysokość": "height",
            "Głębokość": "depth",
        }

        field = sort_map.get(self.sort_combo.currentText(), "name")
        order = "desc" if self.order_btn.isChecked() else "asc"

        return field, order

    def _load_next_page(self):
        """Load the next page of results."""
        if not self._has_more:
            return

        self._page += 1
        self._fetch_and_display_results()

    def _maybe_auto_load(self, value):
        """Auto-load more results when scrolling near bottom."""
        if not self._has_more:
            return

        scrollbar = self.results_scroll.verticalScrollBar()
        if value > scrollbar.maximum() - 150:  # Near bottom
            # Debounce with timer
            QTimer.singleShot(100, self._load_next_page)

    def _on_category_selected(self, item: QTreeWidgetItem):
        """Handle category selection."""
        self._selected_category_ids = set(self._collect_category_ids(item))
        self._reload_search()

    def _collect_category_ids(self, item: QTreeWidgetItem) -> List[int]:
        """Collect selected category id and all descendant ids."""
        category_ids: List[int] = []
        category_id = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(category_id, int):
            category_ids.append(category_id)
        for idx in range(item.childCount()):
            category_ids.extend(self._collect_category_ids(item.child(idx)))
        return category_ids

    def _clear_filters(self):
        """Clear all filters and reload."""
        self.width_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.height_combo.setCurrentIndex(0)
        self._selected_category_ids.clear()
        self.categories_tree.clearSelection()
        self._reload_search()

    def _toggle_view_mode(self):
        """View toggle is intentionally disabled until list mode is implemented."""
        return

    def _on_card_selected(self, item_id: int):
        """Handle card selection."""
        # Clear previous selection
        if self._selected_card:
            self._selected_card.set_selected(False)

        # Find and select new card
        for card in self._cards:
            if card.item_id == item_id:
                card.set_selected(True)
                self._selected_card = card
                break

        # Load item details
        self._selected_item = self.catalog.get_item(item_id)
        if self._selected_item:
            self._populate_item_details(self._selected_item)

    def _on_card_activated(self, item_id: int):
        """Handle card activation (double-click or quick add)."""
        item = self.catalog.get_item(item_id)
        if item:
            self._selected_item = item
            self._add_selected_item(quick=True)

    def _populate_item_details(self, item: CatalogItem):
        """Populate the right pane with item details."""
        # Update preview
        self.preview_label.setText(item.preview_label())

        # Update configuration options
        self.variant_combo.clear()
        if item.variants:
            self.variant_combo.addItems(item.variants)
        else:
            self.variant_combo.addItem("Standardowy")

        self.body_color_combo.clear()
        self.body_color_combo.addItems(item.body_colors)

        self.front_color_combo.clear()
        self.front_color_combo.addItems(item.front_colors)

        self.handle_combo.clear()
        self.handle_combo.addItems(item.handles)

        # Enable add button
        self.add_btn.setEnabled(True)

    def _add_selected_item(self, quick: bool = False):
        """Add the selected item to the project."""
        if not self._selected_item:
            if quick:
                # For quick add, try to get item from sender
                sender = self.sender()
                if hasattr(sender, "item_id"):
                    self._selected_item = self.catalog.get_item(sender.item_id)

            if not self._selected_item:
                QMessageBox.warning(self, "Błąd", "Nie wybrano elementu do dodania")
                return

        try:
            # Prepare parameters
            quantity = 1 if quick else self.quantity_spin.value()

            # Get configuration
            body_color = None
            front_color = None
            handle_type = None

            if not quick:
                body_color = (
                    self.body_color_combo.currentText()
                    if self.body_color_combo.count() > 0
                    else None
                )
                front_color = (
                    self.front_color_combo.currentText()
                    if self.front_color_combo.count() > 0
                    else None
                )
                handle_type = (
                    self.handle_combo.currentText()
                    if self.handle_combo.count() > 0
                    else None
                )

            # Get next sequence number
            next_sequence = self.project_service.get_next_cabinet_sequence(
                self.project.id
            )

            # Add cabinet to project
            cabinet = self.project_service.add_cabinet(
                project_id=self.project.id,
                sequence_number=next_sequence,
                type_id=self._selected_item.id,
                quantity=quantity,
                body_color=body_color or "Biały",
                front_color=front_color or "Biały",
                handle_type=handle_type or "Standardowy",
            )

            if cabinet:
                # Emit success signal
                self.sig_cabinet_added.emit(cabinet)

                # Show success message or close dialog
                if quick or not self.stay_open_checkbox.isChecked():
                    self.accept()
                else:
                    # Reset quantity for next addition
                    self.quantity_spin.setValue(1)
            else:
                QMessageBox.critical(
                    self, "Błąd", "Nie udało się dodać szafki do projektu"
                )

        except Exception as e:
            logger.exception("Error adding cabinet to project")
            error_msg = f"Błąd podczas dodawania szafki: {e}"
            QMessageBox.critical(self, "Błąd", error_msg)
            self.sig_error.emit(error_msg)
