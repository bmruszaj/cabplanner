# src/gui/main_window.py

import os
import logging
from typing import Optional, Literal

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QStatusBar,
    QToolBar,
    QMessageBox,
    QLineEdit,
    QComboBox,
    QStackedWidget,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QModelIndex, QSortFilterProxyModel, QSize
from PySide6.QtGui import QAction

from sqlalchemy.orm import Session

from src.gui.project_dialog import ProjectDialog
from src.constants import KITCHEN_TYPES
from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator
from src.services.settings_service import SettingsService
from src.gui.project_details import ProjectDetailsView
from src.gui.settings_dialog import SettingsDialog
from src.gui.cabinet_catalog import CabinetCatalogWindow
from src.gui.resources.styles import get_theme
from src.gui.resources.resources import get_icon

logger = logging.getLogger(__name__)

# --- Magic constants centralized ---
CARD_HEIGHT = 150
ICON_SIZE = QSize(24, 24)
CONTENT_MARGINS = (10, 10, 10, 10)
LAYOUT_SPACING = 10


class ProjectTableModel(QSortFilterProxyModel):
    def __init__(self, source_model, parent=None):
        super().__init__(parent)
        self.setSourceModel(source_model)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._type_filter = ""

    def setTypeFilter(self, kt: str):
        """Called when user picks from the combo."""
        self._type_filter = kt or ""
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        src = self.sourceModel()
        # 1) Type‐filter: if set, must match exactly
        if self._type_filter:
            idx_type = src.index(source_row, 2, source_parent)
            if src.data(idx_type) != self._type_filter:
                return False

        # 2) Text‐filter: empty = allow all
        pattern = self.filterRegularExpression().pattern().lower()
        if not pattern:
            return True

        # check project name & client columns
        for col in (1, 3):
            idx = src.index(source_row, col, source_parent)
            val = str(src.data(idx)).lower()
            if pattern in val:
                return True
        return False


class _RawProjectModel(QWidget):
    """Internal list model: wraps projects for QTableView"""

    from PySide6.QtCore import QAbstractTableModel, QModelIndex

    class Model(QAbstractTableModel):
        HEADERS = [
            "Numer zamówienia",
            "Nazwa",
            "Typ kuchni",
            "Klient",
            "Data utworzenia",
        ]

        def __init__(self, projects=None, parent=None):
            super().__init__(parent)
            self._projects = projects or []

        def rowCount(self, parent=QModelIndex()):
            return len(self._projects)

        def columnCount(self, parent=QModelIndex()):
            return len(self.HEADERS)

        def data(self, index, role=Qt.DisplayRole):
            if not index.isValid() or role != Qt.DisplayRole:
                return None
            proj = self._projects[index.row()]
            return [
                proj.order_number,
                proj.name,
                proj.kitchen_type,
                proj.client_name,
                proj.created_at.strftime("%Y-%m-%d %H:%M"),
            ][index.column()]

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return self.HEADERS[section]
            return None

        def update_projects(self, projects):
            self.beginResetModel()
            self._projects = projects
            self.endResetModel()

        def get_project_at_row(self, row):
            return self._projects[row] if 0 <= row < len(self._projects) else None


class SearchFilterBar(QWidget):
    """Search and filter bar for the projects view"""

    searchTextChanged = Signal(str)
    filterChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Szukaj projektów..."))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(
            lambda txt: self.searchTextChanged.emit(txt)
        )
        layout.addWidget(self.search_input, 3)

        # Kitchen-type filter
        self.filter_combo = QComboBox()
        self.filter_combo.addItem(self.tr("Wszystkie typy"), "")
        for kt in KITCHEN_TYPES:
            self.filter_combo.addItem(kt, kt)
        self.filter_combo.currentIndexChanged.connect(
            lambda _: self.filterChanged.emit(self.filter_combo.currentData())
        )
        layout.addWidget(self.filter_combo, 1)


class ProjectCard(QFrame):
    """A card widget displaying project information"""

    clicked = Signal(object)
    doubleClicked = Signal(object)

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setObjectName("projectCard")
        self.setProperty("class", "card")
        self.setFixedHeight(CARD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Header
        hdr = QHBoxLayout()
        lbl_name = QLabel(f"<b>{self.project.name}</b>")
        hdr.addWidget(lbl_name)
        lbl_order = QLabel(f"#{self.project.order_number}")
        lbl_order.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hdr.addWidget(lbl_order)
        layout.addLayout(hdr)

        # Info line
        info = QLabel(
            f"<b>{self.tr('Klient')}:</b> "
            f"{self.project.client_name or self.tr('Brak')} | "
            f"<b>{self.tr('Typ kuchni')}:</b> {self.project.kitchen_type} | "
            f"<b>{self.tr('Data utworzenia')}:</b> "
            f"{self.project.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Button bar
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_edit = QPushButton(self.tr("Edytuj"))
        btn_edit.setProperty("class", "secondary")
        btn_edit.setIcon(get_icon("edit"))
        btn_edit.clicked.connect(lambda: self.clicked.emit(self))
        btn_bar.addWidget(btn_edit)

        btn_export = QPushButton(self.tr("Eksportuj"))
        btn_export.clicked.connect(lambda: self._emit_export())
        btn_bar.addWidget(btn_export)

        layout.addLayout(btn_bar)

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self.clicked.emit(self)

    def mouseDoubleClickEvent(self, ev):
        super().mouseDoubleClickEvent(ev)
        self.doubleClicked.emit(self)

    def _emit_export(self):
        parent = self.window()
        if hasattr(parent, "_perform_report_action"):
            parent._perform_report_action(self.project, "open")


class MainWindow(QMainWindow):
    """Main window of the Cabplanner application"""

    def __init__(self, db_session: Session):
        super().__init__()
        self.session = db_session
        self._last_clicked_project: Optional[object] = None
        self._selected_card_widget: Optional[ProjectCard] = None

        self.project_service = ProjectService(db_session)
        self.report_generator = ReportGenerator(db_session=db_session)
        self.settings_service = SettingsService(db_session)
        self.is_dark_mode = self.settings_service.get_setting_value("dark_mode", False)

        self._build_main_window()
        self.setup_connections()
        self.load_projects()

    def _build_main_window(self):
        self.setWindowTitle(self.tr("Cabplanner"))
        self.setMinimumSize(1000, 700)
        self._apply_theme()

        # Central & child areas
        self._build_header_area()
        self._build_filter_area()
        self._build_view_toggle_area()
        self._build_project_views()

        # Menu/toolbar/status
        self._build_menu_bar()
        self._build_toolbar()
        self._build_status_bar()

    def _build_header_area(self):
        """Header with title and project count"""
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(*CONTENT_MARGINS)
        main_lay.setSpacing(LAYOUT_SPACING)

        hdr = QWidget()
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.addWidget(
            QLabel(
                "<h1>Cabplanner</h1>"
                "<p>System zarządzania projektami szafek kuchennych</p>"
            )
        )

        stats = QFrame()
        stats.setObjectName("dashboardWidget")
        stats.setProperty("class", "card")
        stats_lay = QHBoxLayout(stats)
        self.project_count_label = QLabel(f"0 {self.tr('projektów')}")
        stats_lay.addWidget(self.project_count_label)
        hdr_lay.addWidget(stats)

        main_lay.addWidget(hdr)
        self._central_layout = main_lay

    def _build_filter_area(self):
        """Search + kitchen-type filter"""
        self.search_filter = SearchFilterBar()
        self._central_layout.addWidget(self.search_filter)

    def _build_view_toggle_area(self):
        """Cards vs Table toggle buttons"""
        toggle = QHBoxLayout()
        self.btn_cards = QPushButton(self.tr("Karty"))
        self.btn_cards.setCheckable(True)
        self.btn_cards.setChecked(True)
        self.btn_table = QPushButton(self.tr("Tabela"))
        self.btn_table.setCheckable(True)
        toggle.addWidget(self.btn_cards)
        toggle.addWidget(self.btn_table)
        toggle.addStretch()
        self._central_layout.addLayout(toggle)

    def _build_project_views(self):
        """Stacked widget containing the card scroll area and the table view"""
        self.stack = QStackedWidget()

        # Card view
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.card_lay = QVBoxLayout(container)
        scroll.setWidget(container)
        self.stack.addWidget(scroll)

        # Table view
        raw_model = _RawProjectModel.Model([])
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        proxy = ProjectTableModel(raw_model)
        self.table.setModel(proxy)
        self.stack.addWidget(self.table)

        self._central_layout.addWidget(self.stack)

    def _build_menu_bar(self):
        mb = self.menuBar()
        # File menu
        fm = mb.addMenu(self.tr("Plik"))
        a = QAction(self.tr("Nowy projekt"), self)
        a.setShortcut("Ctrl+N")
        a.triggered.connect(self.on_new_project)
        fm.addAction(a)
        fm.addSeparator()
        a = QAction(self.tr("Eksportuj do Word"), self)
        a.setShortcut("Ctrl+E")
        a.triggered.connect(self.on_export_project)
        fm.addAction(a)
        a = QAction(self.tr("Drukuj"), self)
        a.setShortcut("Ctrl+P")
        a.triggered.connect(self.on_print_project)
        fm.addAction(a)
        fm.addSeparator()
        a = QAction(self.tr("Zamknij"), self)
        a.setShortcut("Alt+F4")
        a.triggered.connect(self.close)
        fm.addAction(a)

        # Edit menu
        em = mb.addMenu(self.tr("Edycja"))
        em.addAction(self.tr("Ustawienia"), self.on_open_settings)

        # View menu
        vm = mb.addMenu(self.tr("Widok"))
        vm.addAction(
            self.tr("Przełącz motyw (jasny/ciemny)"), self.on_toggle_theme
        ).setShortcut("Ctrl+T")

        # Tools menu
        tm = mb.addMenu(self.tr("Narzędzia"))
        tm.addAction(self.tr("Katalog szafek"), self.on_open_catalog)

        # Help menu
        hm = mb.addMenu(self.tr("Pomoc"))
        hm.addAction(self.tr("O programie"), self.on_show_about)

    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(ICON_SIZE)
        self.addToolBar(tb)

        for icon, tooltip, slot in [
            ("new_project", self.tr("Nowy projekt"), self.on_new_project),
            ("export", self.tr("Eksportuj"), self.on_export_project),
            ("print", self.tr("Drukuj"), self.on_print_project),
            ("delete", self.tr("Usuń projekt"), self.on_delete_project),
            ("catalog", self.tr("Katalog szafek"), self.on_open_catalog),
            ("settings", self.tr("Ustawienia"), self.on_open_settings),
        ]:
            act = QAction(get_icon(icon), tooltip, self)
            act.triggered.connect(slot)
            tb.addAction(act)
            tb.addSeparator()

    def _build_status_bar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def setup_connections(self):
        """Wire up dynamic signals."""
        self.search_filter.searchTextChanged.connect(self.on_filter_text)
        self.search_filter.filterChanged.connect(self.on_filter_type)
        self.btn_cards.clicked.connect(lambda: self.on_switch_view(0))
        self.btn_table.clicked.connect(lambda: self.on_switch_view(1))

        sel_model = self.table.selectionModel()
        sel_model.selectionChanged.connect(self._on_table_selection_changed)
        self.table.doubleClicked.connect(self._on_table_double_click)

    def load_projects(self):
        projects = self.project_service.list_projects()

        # Table
        raw_model = self.table.model().sourceModel()
        raw_model.update_projects(projects)

        # Cards
        self._clear_card_layout()
        for proj in projects:
            card = ProjectCard(proj)
            card.clicked.connect(lambda _, w=card: self._on_card_clicked(w))
            card.doubleClicked.connect(
                lambda _, w=card: self.on_open_details(w.project)
            )
            self.card_lay.addWidget(card)
        self.card_lay.addStretch()

        # Update stats
        self.project_count_label.setText(f"{len(projects)} {self.tr('projektów')}")
        self.status.showMessage(
            self.tr("Załadowano {0} projektów").format(len(projects))
        )

    def _clear_card_layout(self):
        while self.card_lay.count():
            item = self.card_lay.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def _get_current_project(self) -> Optional[object]:
        if self.stack.currentIndex() == 0:
            return self._last_clicked_project
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        src_idx = self.table.model().mapToSource(rows[0])
        return self.table.model().sourceModel().get_project_at_row(src_idx.row())

    def _perform_report_action(self, project, action: Literal["open", "print"]):
        """Generate and open/print a Word report, with error handling."""
        try:
            path = self.report_generator.generate(project)
            if action == "open":
                os.startfile(path)
                QMessageBox.information(
                    self,
                    self.tr("Eksport zakończony"),
                    self.tr("Raport zapisano:\n{0}").format(path),
                )
            else:
                os.startfile(path, "print")
                QMessageBox.information(
                    self, self.tr("Drukowanie"), self.tr("Projekt wysłany do drukarki")
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

    def _on_card_clicked(self, card_widget: ProjectCard):
        """Handle single-click on a project card: select & highlight."""
        proj = card_widget.project
        self._last_clicked_project = proj
        self.status.showMessage(self.tr("Wybrano projekt: {0}").format(proj.name))

        # Clear previously selected card
        if self._selected_card_widget and self._selected_card_widget is not card_widget:
            self._selected_card_widget.setProperty("selected", False)
            w = self._selected_card_widget
            w.style().unpolish(w)
            w.style().polish(w)

        # Highlight this card
        card_widget.setProperty("selected", True)
        w = card_widget
        w.style().unpolish(w)
        w.style().polish(w)
        self._selected_card_widget = card_widget

    def _on_table_selection_changed(self, selected, deselected):
        proj = self._get_current_project()
        if proj:
            self._last_clicked_project = proj
            self.status.showMessage(self.tr("Wybrano projekt: {0}").format(proj.name))
        else:
            self.status.clearMessage()

    def _on_table_double_click(self, index: QModelIndex):
        src = self.table.model().mapToSource(index)
        proj = self.table.model().sourceModel().get_project_at_row(src.row())
        self.on_open_details(proj)

    def on_new_project(self):
        dlg = ProjectDialog(self.session, parent=self)
        if dlg.exec():
            self.load_projects()
            self.status.showMessage(self.tr("Utworzono nowy projekt"))

    def on_delete_project(self):
        proj = self._get_current_project()
        if not proj:
            QMessageBox.information(
                self, self.tr("Brak projektu"), self.tr("Wybierz projekt.")
            )
            return
        if (
            QMessageBox.question(
                self,
                self.tr("Usuń projekt"),
                self.tr("Usunąć projekt '{0}'?").format(proj.name),
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            self.project_service.delete_project(proj.id)
            self.load_projects()

    def on_export_project(self):
        proj = self._get_current_project()
        if not proj:
            QMessageBox.information(
                self, self.tr("Brak projektu"), self.tr("Wybierz projekt.")
            )
            return
        self._perform_report_action(proj, "open")

    def on_print_project(self):
        proj = self._get_current_project()
        if not proj:
            QMessageBox.information(
                self, self.tr("Brak projektu"), self.tr("Wybierz projekt.")
            )
            return
        self._perform_report_action(proj, "print")

    def on_open_details(self, project):
        if not project:
            QMessageBox.information(
                self, self.tr("Brak projektu"), self.tr("Wybierz projekt.")
            )
            return
        dlg = ProjectDetailsView(self.session, project, parent=self)
        if dlg.exec():
            self.load_projects()

    def on_filter_text(self, text: str):
        proxy: ProjectTableModel = self.table.model()
        proxy.setFilterKeyColumn(-1)  # <-- search all columns
        proxy.setFilterRegularExpression(text)

        term = text.lower()
        for i in range(self.card_lay.count()):
            w = self.card_lay.itemAt(i).widget()
            if isinstance(w, ProjectCard):
                p = w.project
                match = (
                    term in p.name.lower()
                    or (p.client_name and term in p.client_name.lower())
                    or term in p.kitchen_type.lower()
                )
                w.setVisible(match)

    def on_filter_type(self, kt: str):
        proxy: ProjectTableModel = self.table.model()
        if kt:
            proxy.setFilterKeyColumn(2)  # kitchen_type column
            proxy.setFilterFixedString(kt)
        else:
            proxy.setFilterKeyColumn(-1)  # back to all columns
            proxy.setFilterRegularExpression("")  # clear type filter

        self.on_filter_text(self.search_filter.search_input.text())

    def on_switch_view(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.btn_cards.setChecked(idx == 0)
        self.btn_table.setChecked(idx == 1)

    def on_toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings_service.set_setting("dark_mode", self.is_dark_mode)
        self._apply_theme()

    def on_open_settings(self):
        dlg = SettingsDialog(self.session, parent=self)
        if dlg.exec():
            self.is_dark_mode = self.settings_service.get_setting_value(
                "dark_mode", False
            )
            self._apply_theme()
            self.status.showMessage(self.tr("Ustawienia zapisane"))

    def on_open_catalog(self):
        win = CabinetCatalogWindow(self.session, parent=self)
        win.show()

    def on_show_about(self):
        from src.version import get_full_version_info

        QMessageBox.about(
            self,
            self.tr("O programie"),
            f"<h1>Cabplanner</h1><p>{get_full_version_info()}</p><p>© 2025 Cabplanner</p>",
        )

    def _apply_theme(self):
        self.setStyleSheet(get_theme(self.is_dark_mode))
