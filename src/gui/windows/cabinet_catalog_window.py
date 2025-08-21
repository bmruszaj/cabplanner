import logging
from typing import Any, List, Optional

from PySide6.QtCore import QModelIndex, QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.orm import Session

from src.gui.cabinet_type_model import CabinetTypeModel, Col
from src.gui.cabinet_type_proxy import CabinetTypeProxyModel
from src.gui.dialogs.cabinet_type_dialog import CabinetTypeDialog
from src.gui.resources.resources import get_icon
from src.gui.widgets.cabinet_type_card import CabinetTypeCard
from src.services.cabinet_type_service import CabinetTypeService

# Configure logging
logger = logging.getLogger(__name__)


class CabinetCatalogWindow(QMainWindow):
    """Modern cabinet catalog window for the Cabplanner application"""

    def __init__(self, db_session: Session, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.session: Session = db_session
        self.cabinet_type_service = CabinetTypeService(self.session)

        self.current_view_mode: str = "table"  # Default to table view
        self._last_card_cols: int = 0  # for responsive grid

        self._init_ui()
        self._init_model()
        self.load_cabinet_types()

    # --- UI ---

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Katalog szafek")
        self.resize(1000, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Header
        header_frame = QFrame()
        header_frame.setProperty("class", "card")
        header_layout = QHBoxLayout(header_frame)

        title_label = QLabel("<h2>Katalog szafek</h2>")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj nazw/typów…")
        self.search_edit.setClearButtonEnabled(True)
        header_layout.addWidget(self.search_edit)

        # Kitchen filter (value used to restrict DB query)
        header_layout.addWidget(QLabel("Filtruj typ kuchni:"))
        self.filter_kitchen_combo = QComboBox()
        # Kitchen types will be injected below in _inject_kitchen_types()
        self.filter_kitchen_combo.currentIndexChanged.connect(self.apply_filters)
        header_layout.addWidget(self.filter_kitchen_combo)

        main_layout.addWidget(header_frame)

        # Toolbar
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Dodaj szafkę")
        self.add_btn.setIcon(get_icon("add"))
        self.add_btn.clicked.connect(self.add_cabinet_type)
        btn_layout.addWidget(self.add_btn)

        # Toggle view (exclusive)
        self.card_view_btn = QPushButton("Karty")
        self.card_view_btn.setCheckable(True)
        self.card_view_btn.clicked.connect(lambda: self.set_view_mode("cards"))
        btn_layout.addWidget(self.card_view_btn)

        self.table_view_btn = QPushButton("Tabela")
        self.table_view_btn.setCheckable(True)
        self.table_view_btn.setChecked(True)
        self.table_view_btn.clicked.connect(lambda: self.set_view_mode("table"))
        btn_layout.addWidget(self.table_view_btn)

        self.view_group = QButtonGroup(self)
        self.view_group.setExclusive(True)
        self.view_group.addButton(self.card_view_btn)
        self.view_group.addButton(self.table_view_btn)

        btn_layout.addStretch()

        self.edit_btn = QPushButton("Edytuj")
        self.edit_btn.setIcon(get_icon("edit"))
        self.edit_btn.setProperty("class", "secondary")
        self.edit_btn.clicked.connect(self.edit_cabinet_type)
        btn_layout.addWidget(self.edit_btn)

        self.duplicate_btn = QPushButton("Duplikuj")
        self.duplicate_btn.setIcon(get_icon("add"))  # Changed from "copy" to "add" since copy icon doesn't exist
        self.duplicate_btn.setProperty("class", "secondary")
        self.duplicate_btn.clicked.connect(self.duplicate_cabinet_type)
        btn_layout.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton("Usuń")
        self.delete_btn.setIcon(get_icon("delete"))
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_cabinet_type)
        btn_layout.addWidget(self.delete_btn)

        main_layout.addLayout(btn_layout)

        # Content area: views + empty state
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # View stack (table / cards)
        self.view_stack = QStackedWidget()
        self.content_stack.addWidget(self.view_stack)

        # Table view
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.doubleClicked.connect(self.edit_cabinet_type)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_table_context_menu)
        self.view_stack.addWidget(self.table_view)

        # Card view (scrollable grid of cabinet cards)
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_container = QWidget()
        self.card_layout = QGridLayout(self.card_container)
        self.card_layout.setHorizontalSpacing(12)
        self.card_layout.setVerticalSpacing(12)
        self.card_scroll.setWidget(self.card_container)
        self.view_stack.addWidget(self.card_scroll)

        # Empty state
        self.empty_state = QWidget()
        empty_l = QVBoxLayout(self.empty_state)
        empty_l.setAlignment(Qt.AlignCenter)
        empty_msg = QLabel("Brak typów szafek.\nDodaj pierwszy, aby rozpocząć.")
        empty_msg.setAlignment(Qt.AlignCenter)
        empty_msg.setStyleSheet("font-size: 14pt; color: gray;")
        empty_l.addWidget(empty_msg)
        cta = QPushButton("Dodaj szafkę")
        cta.setIcon(get_icon("add"))
        cta.clicked.connect(self.add_cabinet_type)
        empty_l.addWidget(cta)
        self.content_stack.addWidget(self.empty_state)

        # Default view mode
        self.set_view_mode("table")

        # Status bar
        self.statusBar().showMessage("Gotowy")

        # Keyboard shortcuts
        QShortcut(QKeySequence.New, self, activated=self.add_cabinet_type)        # Ctrl+N
        QShortcut(QKeySequence.Delete, self, activated=self.delete_cabinet_type)  # Delete
        QShortcut(QKeySequence.Find, self, activated=lambda: self.search_edit.setFocus())  # Ctrl+F
        QShortcut(QKeySequence(Qt.Key_Return), self, activated=self.edit_cabinet_type)
        QShortcut(QKeySequence(Qt.Key_Enter), self, activated=self.edit_cabinet_type)

        # Persist geometry + header
        s = QSettings("Cabplanner", "Cabplanner")
        geo = s.value("catalog_geometry")
        if geo:
            self.restoreGeometry(geo)
        # header will be restored after model is set

        # Wire search box (proxy hooked in _init_model)
        self.search_edit.textChanged.connect(self._on_search_text)

        # Inject kitchen types (fallback)
        self._inject_kitchen_types()

    def _init_model(self) -> None:
        """Initialize the table model and proxy."""
        # Init model + proxy; set on table
        self.model = CabinetTypeModel([])
        self.proxy = CabinetTypeProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setSortRole(Qt.UserRole)
        self.table_view.setModel(self.proxy)

        # Column sizes
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setSectionResizeMode(Col.NAZWA, QHeaderView.Stretch)

        # Restore header state if available
        s = QSettings("Cabplanner", "Cabplanner")
        header_state = s.value("catalog_header_state")
        if header_state:
            self.table_view.horizontalHeader().restoreState(header_state)

        # Update action buttons when selection changes
        self.table_view.selectionModel().selectionChanged.connect(self._update_actions_enabled)
        self._update_actions_enabled()

    def _inject_kitchen_types(self) -> None:
        """Load kitchen types dynamically if service provides them, else fallback."""
        options: List[str] = []
        try:
            if hasattr(self.cabinet_type_service, "list_kitchen_types"):
                options = list(self.cabinet_type_service.list_kitchen_types())  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning(f"Could not list kitchen types dynamically: {e}")
        if not options:
            options = ["Wszystkie", "LOFT", "PARIS", "WINO"]
        else:
            options = ["Wszystkie"] + options

        self.filter_kitchen_combo.clear()
        self.filter_kitchen_combo.addItems(options)

    # --- State persistence ---

    def closeEvent(self, e) -> None:  # type: ignore[override]
        """Save window state on close."""
        s = QSettings("Cabplanner", "Cabplanner")
        s.setValue("catalog_geometry", self.saveGeometry())
        s.setValue("catalog_header_state", self.table_view.horizontalHeader().saveState())
        super().closeEvent(e)

    # --- View toggling / resizing ---

    def set_view_mode(self, mode: str) -> None:
        """Switch between card and table view modes"""
        self.current_view_mode = mode
        if mode == "cards":
            self.view_stack.setCurrentIndex(1)
            self.card_view_btn.setChecked(True)
            self.table_view_btn.setChecked(False)
            # Re-layout grid if needed
            self._refresh_card_grid()
        else:
            self.view_stack.setCurrentIndex(0)
            self.table_view_btn.setChecked(True)
            self.card_view_btn.setChecked(False)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle window resize events to update card grid."""
        super().resizeEvent(event)
        if self.current_view_mode == "cards":
            self._refresh_card_grid()

    def _calc_card_cols(self) -> int:
        """Calculate number of columns for responsive card grid."""
        # crude responsive: ~320px per card incl. spacing
        w = max(1, self.card_scroll.viewport().width())
        return max(1, w // 320)

    def _clear_card_layout(self) -> None:
        """Clear all widgets from the card layout."""
        while self.card_layout.count() > 0:
            item = self.card_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _refresh_card_grid(self) -> None:
        """Refresh the card grid layout with current data."""
        cols = self._calc_card_cols()
        if cols == self._last_card_cols and self.card_layout.count() > 0:
            return
        # rebuild with current cols
        # (lightweight enough for our dataset; optimize if needed)
        cts = getattr(self.model, "cabinet_types", [])
        self._clear_card_layout()
        for i, ct in enumerate(cts):
            r, c = divmod(i, cols)
            card = CabinetTypeCard(ct)
            card.clicked.connect(self.on_card_clicked)
            self.card_layout.addWidget(card, r, c)
        self._last_card_cols = cols

    # --- Data loading / filters ---

    def _current_kitchen_filter(self) -> Optional[str]:
        """Get the current kitchen filter selection."""
        text = self.filter_kitchen_combo.currentText()
        if text and text != "Wszystkie":
            return text
        return None

    def apply_filters(self) -> None:
        """Apply selected filters and refresh the table (DB-level for kitchen type)."""
        # Guard against calling this before model is initialized
        if not hasattr(self, 'model') or self.model is None:
            return
        self.load_cabinet_types()

    def _on_search_text(self, text: str) -> None:
        """Handle search text changes."""
        self.proxy.set_search_text(text)

    def load_cabinet_types(self) -> None:
        """Load cabinet types from database with optional filtering"""
        kitchen_type = self._current_kitchen_filter()
        cabinet_types = self.cabinet_type_service.list_cabinet_types(kitchen_type=kitchen_type)

        # Update model (keeps proxy, header, selection signals intact)
        self.model.update_cabinet_types(cabinet_types)

        # Update table column widths (first time only)
        self.table_view.setColumnWidth(Col.ID, 60)
        for i in (Col.LISTWA, Col.WIENIEC, Col.BOK, Col.FRONT, Col.POLKA):
            self.table_view.setColumnWidth(int(i), 70)

        # Rebuild cards
        self._last_card_cols = 0  # force rebuild
        self._refresh_card_grid()

        # Empty state toggle
        if len(cabinet_types) == 0:
            self.content_stack.setCurrentWidget(self.empty_state)
        else:
            self.content_stack.setCurrentWidget(self.view_stack)

        # Update status bar
        self.statusBar().showMessage(f"Załadowano {len(cabinet_types)} typów szafek")

        # Update action buttons (selection may be stale after reload)
        self._update_actions_enabled()

    # --- Selection / actions enabled ---

    def _selected_cabinet_type(self) -> Optional[Any]:
        """Returns selected cabinet type from the table view (proxy-aware)."""
        if self.current_view_mode != "table":
            return None
        sel = self.table_view.selectionModel().selectedRows()
        if not sel:
            return None
        proxy_index: QModelIndex = sel[0]
        source_index = self.proxy.mapToSource(proxy_index)
        return self.model.get_cabinet_type_at_row(source_index.row())

    def _update_actions_enabled(self) -> None:
        """Update enabled state of action buttons based on selection."""
        has_sel = self._selected_cabinet_type() is not None
        self.edit_btn.setEnabled(has_sel)
        self.delete_btn.setEnabled(has_sel)
        self.duplicate_btn.setEnabled(has_sel)

    # --- Context menu ---

    def _show_table_context_menu(self, pos) -> None:
        """Show context menu for table view."""
        index = self.table_view.indexAt(pos)
        menu = QMenu(self)
        act_edit = QAction("Edytuj", self)
        act_dup = QAction("Duplikuj", self)
        act_del = QAction("Usuń", self)
        if index.isValid():
            self.table_view.selectRow(index.row())
            self._update_actions_enabled()
            menu.addAction(act_edit)
            menu.addAction(act_dup)
            menu.addSeparator()
            menu.addAction(act_del)
            chosen = menu.exec(self.table_view.viewport().mapToGlobal(pos))
            if chosen == act_edit:
                self.edit_cabinet_type()
            elif chosen == act_dup:
                self.duplicate_cabinet_type()
            elif chosen == act_del:
                self.delete_cabinet_type()

    # --- Events ---

    def on_card_clicked(self, cabinet_type: Any) -> None:
        """Handle cabinet card click event"""
        self.edit_cabinet_type(cabinet_type)

    # --- CRUD actions ---

    def add_cabinet_type(self) -> None:
        """Open dialog to add a new cabinet type"""
        dlg = CabinetTypeDialog(self.session, parent=self)
        dlg.inject_kitchen_types(self._available_kitchen_types_for_dialog())
        if dlg.exec():
            self.load_cabinet_types()

    def edit_cabinet_type(self, cabinet_type_or_index: Optional[Any] = None) -> None:
        """Open dialog to edit the selected cabinet type"""
        cabinet_type: Optional[Any] = None

        # If double-click provided a QModelIndex (from proxy), translate to source row
        if isinstance(cabinet_type_or_index, QModelIndex):
            source_index = self.proxy.mapToSource(cabinet_type_or_index)
            cabinet_type = self.model.get_cabinet_type_at_row(source_index.row())
        elif hasattr(cabinet_type_or_index, "id"):
            cabinet_type = cabinet_type_or_index
        else:
            cabinet_type = self._selected_cabinet_type()

        if not cabinet_type:
            QMessageBox.information(self, "Wybierz szafkę", "Proszę wybrać typ szafki do edycji.")
            return

        dlg = CabinetTypeDialog(self.session, cabinet_type.id, parent=self)
        dlg.inject_kitchen_types(self._available_kitchen_types_for_dialog())
        if dlg.exec():
            self.load_cabinet_types()

    def duplicate_cabinet_type(self) -> None:
        """Duplicate selected cabinet type (prefilled dialog, saved as new)."""
        source = self._selected_cabinet_type()
        if not source:
            QMessageBox.information(self, "Wybierz szafkę", "Proszę wybrać typ szafki do duplikacji.")
            return
        dlg = CabinetTypeDialog(self.session, parent=self, prefill_cabinet=source)
        dlg.inject_kitchen_types(self._available_kitchen_types_for_dialog())
        if dlg.exec():
            self.load_cabinet_types()

    def delete_cabinet_type(self) -> None:
        """Delete the selected cabinet type"""
        cabinet_type = self._selected_cabinet_type()
        if not cabinet_type:
            if self.current_view_mode == "table":
                QMessageBox.information(self, "Wybierz szafkę", "Proszę wybrać typ szafki do usunięcia.")
            else:
                QMessageBox.information(
                    self,
                    "Wybierz szafkę",
                    "Aby usunąć szafkę, wybierz ją w widoku tabeli lub przejdź do edycji.",
                )
            return

        reply = QMessageBox.question(
            self,
            "Potwierdzenie usunięcia",
            f"Czy na pewno chcesz usunąć typ szafki '{cabinet_type.nazwa}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                # Optional: check for references and block if used (requires service support)
                self.cabinet_type_service.delete_cabinet_type(cabinet_type.id)
                self.load_cabinet_types()
                self.statusBar().showMessage("Typ szafki został usunięty")
            except Exception as e:
                logger.error(f"Error deleting cabinet type: {e}")
                msg = QMessageBox(QMessageBox.Critical, "Błąd", "Nie udało się usunąć typu szafki.", QMessageBox.Ok, self)
                msg.setDetailedText(str(e))
                msg.exec()

    # --- Utils ---

    def _available_kitchen_types_for_dialog(self) -> List[str]:
        """Dialog should not include 'Wszystkie' option."""
        items = [self.filter_kitchen_combo.itemText(i) for i in range(self.filter_kitchen_combo.count())]
        return [x for x in items if x and x != "Wszystkie"]
