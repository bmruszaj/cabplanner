"""
Browser widget for catalog items.

Provides search, filtering, and display of catalog items in list/grid view.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QLabel,
    QFrame,
)
from PySide6.QtCore import (
    Qt,
    Signal,
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
)
from PySide6.QtGui import QFont

from src.gui.resources.styles import get_theme, PRIMARY
from src.services.catalog_service import CatalogService, CatalogCabinetType


class CatalogTableModel(QAbstractTableModel):
    """Table model for catalog items."""

    COLUMNS = ["Nazwa", "SKU", "Typ kuchni", "Wymiary", "Opis"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: list[CatalogCabinetType] = []

    def set_items(self, items: list[CatalogCabinetType]):
        """Set items to display."""
        self.beginResetModel()
        self.items = items
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int):
        if not index.isValid() or index.row() >= len(self.items):
            return None

        item = self.items[index.row()]
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if column == 0:  # Name
                return item.name
            elif column == 1:  # SKU
                return item.sku or ""
            elif column == 2:  # Kitchen Type
                return item.kitchen_type
            elif column == 3:  # Dimensions
                if item.width_mm and item.height_mm and item.depth_mm:
                    return f"{item.width_mm}×{item.height_mm}×{item.depth_mm} mm"
                return ""
            elif column == 4:  # Description
                return item.description

        elif role == Qt.ItemDataRole.UserRole:
            return item.id

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self.COLUMNS[section]
        return None

    def get_item(self, index: QModelIndex) -> Optional[CatalogCabinetType]:
        """Get item at index."""
        if not index.isValid() or index.row() >= len(self.items):
            return None
        return self.items[index.row()]


class CatalogBrowserWidget(QWidget):
    """Widget for browsing catalog items."""

    # Signals
    sig_item_activated = Signal(int)  # cabinet_type_id
    sig_selection_changed = Signal(bool)  # has_selection

    def __init__(self, catalog_service: CatalogService, parent=None):
        super().__init__(parent)
        self.catalog_service = catalog_service
        self._current_query = ""
        self._current_filters = {}

        self._setup_ui()
        self._setup_connections()
        self._apply_styles()
        self.refresh()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search header
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 8, 8, 0)

        search_label = QLabel("Szukaj:")
        search_label.setFixedWidth(50)
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj według nazwy lub typu kuchni...")
        search_layout.addWidget(self.search_edit)

        layout.addLayout(search_layout)

        # Results info
        self.results_label = QLabel("0 elementów")
        self.results_label.setObjectName("resultsLabel")
        layout.addWidget(self.results_label)

        # Table view
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_view.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)

        # Setup model
        self.model = CatalogTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.table_view.setModel(self.proxy_model)

        # Configure headers
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # SKU
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )  # Kitchen Type
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )  # Dimensions
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Description

        layout.addWidget(self.table_view)

        # Optional details panel (placeholder for future)
        details_frame = QFrame()
        details_frame.setFixedHeight(80)
        details_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)

        self.details_label = QLabel("Wybierz element, aby wyświetlić szczegóły")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setFont(QFont("Segoe UI", 9))
        details_layout.addWidget(self.details_label)

        layout.addWidget(details_frame)

    def _setup_connections(self):
        """Setup signal connections."""
        self.search_edit.textChanged.connect(self._on_search_changed)
        self.table_view.doubleClicked.connect(self._on_item_activated)
        self.table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

    def _apply_styles(self):
        """Apply styling to the widget."""
        self.setStyleSheet(
            get_theme()
            + f"""
            QLineEdit {{
                padding: 6px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border-color: {PRIMARY};
            }}
            QLabel#resultsLabel {{
                color: #666666;
                font-size: 9pt;
                padding: 4px 8px;
            }}
            QTableView {{
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                selection-background-color: {PRIMARY};
                selection-color: white;
            }}
            QTableView::item {{
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QTableView::item:selected {{
                background-color: {PRIMARY};
                color: white;
            }}
            QTableView::item:hover {{
                background-color: #F5F5F5;
            }}
            QHeaderView::section {{
                background-color: #F8F9FA;
                padding: 8px;
                border: none;
                border-right: 1px solid #E0E0E0;
                font-weight: bold;
            }}
            QFrame {{
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
            }}
        """
        )

    def set_query(self, text: str):
        """Set search query."""
        self._current_query = text
        self.search_edit.setText(text)
        self.refresh()

    def set_filters(self, filters: dict):
        """Set filters."""
        self._current_filters = filters
        self.refresh()

    def refresh(self):
        """Refresh the displayed items."""
        try:
            items = self.catalog_service.list_types(
                query=self._current_query, filters=self._current_filters
            )
            self.model.set_items(items)

            # Update results label
            count = len(items)
            if count == 1:
                self.results_label.setText("1 element")
            else:
                self.results_label.setText(f"{count} elementów")

        except Exception as e:
            print(f"Error refreshing catalog browser: {e}")
            self.model.set_items([])
            self.results_label.setText("Błąd ładowania elementów")

    def current_item_id(self) -> int | None:
        """Get current selected item ID."""
        selection = self.table_view.selectionModel().currentIndex()
        if not selection.isValid():
            return None

        source_index = self.proxy_model.mapToSource(selection)
        item = self.model.get_item(source_index)
        return item.id if item else None

    def current_item(self) -> Optional[CatalogCabinetType]:
        """Get current selected item."""
        selection = self.table_view.selectionModel().currentIndex()
        if not selection.isValid():
            return None

        source_index = self.proxy_model.mapToSource(selection)
        return self.model.get_item(source_index)

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self._current_query = text
        self.refresh()

    def _on_item_activated(self, index: QModelIndex):
        """Handle item activation (double-click)."""
        source_index = self.proxy_model.mapToSource(index)
        item = self.model.get_item(source_index)
        if item:
            self.sig_item_activated.emit(item.id)

    def _on_selection_changed(self):
        """Handle selection change."""
        has_selection = self.table_view.selectionModel().hasSelection()
        self.sig_selection_changed.emit(has_selection)

        # Update details panel
        item = self.current_item()
        if item:
            dims = ""
            if item.width_mm and item.height_mm and item.depth_mm:
                dims = f" • {item.width_mm}×{item.height_mm}×{item.depth_mm} mm"
            self.details_label.setText(f"{item.name} ({item.kitchen_type}){dims}")
        else:
            self.details_label.setText("Wybierz element, aby wyświetlić szczegóły")
