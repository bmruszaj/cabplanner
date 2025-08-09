from __future__ import annotations

import logging
from enum import IntEnum
from typing import Any, List, Optional

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    Signal,
    QSortFilterProxyModel,
    QSettings,
    QSize, QObject,
)
from PySide6.QtGui import QAction, QColor, QKeySequence, QPainter, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QDoubleSpinBox,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
    QFrame,
    QSizePolicy, QCheckBox, QComboBox,
)

from sqlalchemy.orm import Session

from src.services.cabinet_type_service import CabinetTypeService
from src.gui.resources.resources import get_icon

# Configure logging
logger = logging.getLogger(__name__)


# ---------------------------
# Helpers / small utilities
# ---------------------------

class Col(IntEnum):
    ID = 0
    NAZWA = 1
    TYP = 2
    HDF = 3
    LISTWA = 4
    WIENIEC = 5
    BOK = 6
    FRONT = 7
    POLKA = 8


def dot(color: QColor, diameter: int = 10) -> QPixmap:
    """Small colored dot pixmap used as a status chip."""
    pm = QPixmap(diameter, diameter)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(color)
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, diameter, diameter)
    painter.end()
    return pm


# ---------------------------
# Models
# ---------------------------

class CabinetTypeModel(QAbstractTableModel):
    """Model for displaying cabinet types in a table view"""

    headers: List[str] = [
        "ID",
        "Nazwa",
        "Typ kuchni",
        "Plecy HDF",
        "Listwy",
        "Wieńce",
        "Boki",
        "Fronty",
        "Półki",
    ]

    def __init__(self, cabinet_types: List[Any], parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.cabinet_types: List[Any] = cabinet_types

    # --- Required overrides ---

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return len(self.cabinet_types)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None

        ct = self.cabinet_types[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == Col.ID:
                return int(ct.id)
            elif col == Col.NAZWA:
                return ct.nazwa
            elif col == Col.TYP:
                return ct.kitchen_type
            elif col == Col.HDF:
                return "Tak" if bool(ct.hdf_plecy) else "Nie"
            elif col == Col.LISTWA:
                return int(ct.listwa_count)
            elif col == Col.WIENIEC:
                return int(ct.wieniec_count)
            elif col == Col.BOK:
                return int(ct.bok_count)
            elif col == Col.FRONT:
                return int(ct.front_count)
            elif col == Col.POLKA:
                return int(ct.polka_count)

        # Use UserRole for **sorting correctness** across columns
        if role == Qt.UserRole:
            if col == Col.ID:
                return int(ct.id)
            elif col == Col.NAZWA:
                return str(ct.nazwa).lower()
            elif col == Col.TYP:
                return str(ct.kitchen_type).lower()
            elif col == Col.HDF:
                return bool(ct.hdf_plecy)
            elif col == Col.LISTWA:
                return int(ct.listwa_count)
            elif col == Col.WIENIEC:
                return int(ct.wieniec_count)
            elif col == Col.BOK:
                return int(ct.bok_count)
            elif col == Col.FRONT:
                return int(ct.front_count)
            elif col == Col.POLKA:
                return int(ct.polka_count)

        # Cute status chip for HDF
        if role == Qt.DecorationRole and col == Col.HDF:
            return dot(QColor("#2ecc71") if ct.hdf_plecy else QColor("#e74c3c"))

        if role == Qt.TextAlignmentRole:
            if col in (Col.ID, Col.LISTWA, Col.WIENIEC, Col.BOK, Col.FRONT, Col.POLKA):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:  # type: ignore[override]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore[override]
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    # --- helpers ---

    def update_cabinet_types(self, cabinet_types: List[Any]) -> None:
        self.beginResetModel()
        self.cabinet_types = cabinet_types
        self.endResetModel()

    def get_cabinet_type_at_row(self, row: int) -> Optional[Any]:
        if 0 <= row < len(self.cabinet_types):
            return self.cabinet_types[row]
        return None


class CabinetTypeProxyModel(QSortFilterProxyModel):
    """Proxy that handles text search across name/type."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._search_text: str = ""

    def set_search_text(self, text: str) -> None:
        self._search_text = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # type: ignore[override]
        if not self._search_text:
            return True
        m: CabinetTypeModel = self.sourceModel()  # type: ignore[assignment]
        name_idx = m.index(source_row, Col.NAZWA)
        type_idx = m.index(source_row, Col.TYP)
        name = (m.data(name_idx, Qt.DisplayRole) or "").lower()
        typ = (m.data(type_idx, Qt.DisplayRole) or "").lower()
        return self._search_text in name or self._search_text in typ


# ---------------------------
# Dialog
# ---------------------------

class CabinetTypeDialog(QDialog):
    """Dialog for creating or editing a cabinet type"""

    def __init__(
        self,
        db_session: Session,
        cabinet_type_id: Optional[int] = None,
        parent: Optional[QWidget] = None,
        prefill_cabinet: Optional[Any] = None,  # If provided and id is None, we prefill for "Duplicate"
    ) -> None:
        super().__init__(parent)

        self.session: Session = db_session
        self.cabinet_type_service = CabinetTypeService(self.session)

        self.cabinet_type_id: Optional[int] = cabinet_type_id
        self.cabinet_type: Optional[Any] = None

        if cabinet_type_id:
            self.cabinet_type = self.cabinet_type_service.get_cabinet_type(cabinet_type_id)

        self._build_ui()

        if self.cabinet_type:
            self.setWindowTitle("Edytuj typ szafki")
            self._load_cabinet_type_data(self.cabinet_type)
        elif prefill_cabinet is not None:
            self.setWindowTitle(f"Nowy typ szafki (na podstawie: {prefill_cabinet.nazwa})")
            self._load_cabinet_type_data(prefill_cabinet, is_prefill=True)
        else:
            self.setWindowTitle("Nowy typ szafki")

        # Shortcut: Ctrl+Enter to save
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.accept)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self.accept)

    def _build_part_group(
        self, title: str
    ) -> tuple[QGroupBox, QSpinBox, QDoubleSpinBox, QDoubleSpinBox]:
        group = QGroupBox(title)
        lay = QFormLayout(group)
        count = QSpinBox()
        count.setRange(0, 10)
        w = QDoubleSpinBox()
        h = QDoubleSpinBox()
        for spin in (w, h):
            spin.setRange(0, 5000)
            spin.setDecimals(0)
            spin.setSingleStep(1)
            spin.setSuffix(" mm")
        lay.addRow("Ilość:", count)
        lay.addRow("Szerokość:", w)
        lay.addRow("Wysokość:", h)
        return group, count, w, h

    def _bind_count(self, count_spin: QSpinBox, w_spin: QDoubleSpinBox, h_spin: QDoubleSpinBox) -> None:
        def toggle(v: int) -> None:
            on = v > 0
            w_spin.setEnabled(on)
            h_spin.setEnabled(on)
            if not on:
                w_spin.setValue(0)
                h_spin.setValue(0)

        count_spin.valueChanged.connect(toggle)
        toggle(count_spin.value())

    def _build_ui(self) -> None:
        self.resize(640, 720)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Scrollable area
        content = QWidget()
        form_v = QVBoxLayout(content)
        form_v.setSpacing(16)

        # Basic info
        basic_group = QGroupBox("Podstawowe informacje")
        basic_l = QFormLayout(basic_group)
        self.nazwa_edit = QLineEdit()
        basic_l.addRow("Nazwa:", self.nazwa_edit)

        self.kitchen_type_combo = QComboBox()
        # Kitchen types will be injected by the caller (fallback kept in window)
        basic_l.addRow("Typ kuchni:", self.kitchen_type_combo)

        self.hdf_plecy_check = QCheckBox()
        basic_l.addRow("Plecy HDF:", self.hdf_plecy_check)

        form_v.addWidget(basic_group)

        # Parts
        self.listwa_group, self.listwa_count_spin, self.listwa_w_spin, self.listwa_h_spin = self._build_part_group(
            "Listwy"
        )
        form_v.addWidget(self.listwa_group)

        self.wieniec_group, self.wieniec_count_spin, self.wieniec_w_spin, self.wieniec_h_spin = self._build_part_group(
            "Wieńce"
        )
        form_v.addWidget(self.wieniec_group)

        self.bok_group, self.bok_count_spin, self.bok_w_spin, self.bok_h_spin = self._build_part_group(
            "Boki"
        )
        form_v.addWidget(self.bok_group)

        self.front_group, self.front_count_spin, self.front_w_spin, self.front_h_spin = self._build_part_group(
            "Fronty"
        )
        form_v.addWidget(self.front_group)

        self.polka_group, self.polka_count_spin, self.polka_w_spin, self.polka_h_spin = self._build_part_group(
            "Półki"
        )
        form_v.addWidget(self.polka_group)

        # Live summary
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        form_v.addWidget(self.summary_label)

        # Scroll wrapper
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Save).setDefault(True)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        # Bind enables and live summary
        for s in (
            (self.listwa_count_spin, self.listwa_w_spin, self.listwa_h_spin),
            (self.wieniec_count_spin, self.wieniec_w_spin, self.wieniec_h_spin),
            (self.bok_count_spin, self.bok_w_spin, self.bok_h_spin),
            (self.front_count_spin, self.front_w_spin, self.front_h_spin),
            (self.polka_count_spin, self.polka_w_spin, self.polka_h_spin),
        ):
            self._bind_count(*s)

        def update_summary() -> None:
            parts = [
                f"Boki x{self.bok_count_spin.value()}",
                f"Wieńce x{self.wieniec_count_spin.value()}",
                f"Półki x{self.polka_count_spin.value()}",
                f"Fronty x{self.front_count_spin.value()}",
                f"Listwy x{self.listwa_count_spin.value()}",
            ]
            self.summary_label.setText("Podsumowanie: " + ", ".join(parts))

        for w in (
            self.listwa_count_spin,
            self.wieniec_count_spin,
            self.bok_count_spin,
            self.front_count_spin,
            self.polka_count_spin,
        ):
            w.valueChanged.connect(update_summary)
        update_summary()

    def inject_kitchen_types(self, types: List[str]) -> None:
        self.kitchen_type_combo.clear()
        self.kitchen_type_combo.addItems(types)

    def _load_cabinet_type_data(self, source: Any, is_prefill: bool = False) -> None:
        self.nazwa_edit.setText("" if is_prefill else str(source.nazwa))

        idx = self.kitchen_type_combo.findText(str(source.kitchen_type))
        if idx >= 0:
            self.kitchen_type_combo.setCurrentIndex(idx)

        self.hdf_plecy_check.setChecked(bool(source.hdf_plecy))

        self.listwa_count_spin.setValue(int(source.listwa_count))
        if source.listwa_w_mm:
            self.listwa_w_spin.setValue(float(source.listwa_w_mm))
        if source.listwa_h_mm:
            self.listwa_h_spin.setValue(float(source.listwa_h_mm))

        self.wieniec_count_spin.setValue(int(source.wieniec_count))
        if source.wieniec_w_mm:
            self.wieniec_w_spin.setValue(float(source.wieniec_w_mm))
        if source.wieniec_h_mm:
            self.wieniec_h_spin.setValue(float(source.wieniec_h_mm))

        self.bok_count_spin.setValue(int(source.bok_count))
        if source.bok_w_mm:
            self.bok_w_spin.setValue(float(source.bok_w_mm))
        if source.bok_h_mm:
            self.bok_h_spin.setValue(float(source.bok_h_mm))

        self.front_count_spin.setValue(int(source.front_count))
        if source.front_w_mm:
            self.front_w_spin.setValue(float(source.front_w_mm))
        if source.front_h_mm:
            self.front_h_spin.setValue(float(source.front_h_mm))

        self.polka_count_spin.setValue(int(source.polka_count))
        if source.polka_w_mm:
            self.polka_w_spin.setValue(float(source.polka_w_mm))
        if source.polka_h_mm:
            self.polka_h_spin.setValue(float(source.polka_h_mm))

    # --- Save ---

    def accept(self) -> None:  # type: ignore[override]
        nazwa = self.nazwa_edit.text().strip()
        if not nazwa:
            QMessageBox.warning(self, "Błąd", "Nazwa szafki jest wymagana.")
            self.nazwa_edit.setFocus()
            return

        kitchen_type = self.kitchen_type_combo.currentText()
        hdf_plecy = self.hdf_plecy_check.isChecked()

        # measurements with None if count==0
        def mm_or_none(count: int, w: float, h: float) -> tuple[Optional[float], Optional[float]]:
            return (w if count > 0 else None, h if count > 0 else None)

        listwa_count = self.listwa_count_spin.value()
        listwa_w_mm, listwa_h_mm = mm_or_none(listwa_count, self.listwa_w_spin.value(), self.listwa_h_spin.value())

        wieniec_count = self.wieniec_count_spin.value()
        wieniec_w_mm, wieniec_h_mm = mm_or_none(
            wieniec_count, self.wieniec_w_spin.value(), self.wieniec_h_spin.value()
        )

        bok_count = self.bok_count_spin.value()
        bok_w_mm, bok_h_mm = mm_or_none(bok_count, self.bok_w_spin.value(), self.bok_h_spin.value())

        front_count = self.front_count_spin.value()
        front_w_mm, front_h_mm = mm_or_none(front_count, self.front_w_spin.value(), self.front_h_spin.value())

        polka_count = self.polka_count_spin.value()
        polka_w_mm, polka_h_mm = mm_or_none(polka_count, self.polka_w_spin.value(), self.polka_h_spin.value())

        try:
            cabinet_data = {
                "nazwa": nazwa,
                "kitchen_type": kitchen_type,
                "hdf_plecy": hdf_plecy,
                "listwa_count": listwa_count,
                "listwa_w_mm": listwa_w_mm,
                "listwa_h_mm": listwa_h_mm,
                "wieniec_count": wieniec_count,
                "wieniec_w_mm": wieniec_w_mm,
                "wieniec_h_mm": wieniec_h_mm,
                "bok_count": bok_count,
                "bok_w_mm": bok_w_mm,
                "bok_h_mm": bok_h_mm,
                "front_count": front_count,
                "front_w_mm": front_w_mm,
                "front_h_mm": front_h_mm,
                "polka_count": polka_count,
                "polka_w_mm": polka_w_mm,
                "polka_h_mm": polka_h_mm,
            }

            if self.cabinet_type_id:
                self.cabinet_type_service.update_cabinet_type(self.cabinet_type_id, **cabinet_data)
                logger.info(f"Updated cabinet type ID: {self.cabinet_type_id}")
            else:
                new_cabinet = self.cabinet_type_service.create_cabinet_type(**cabinet_data)
                logger.info(f"Created new cabinet type ID: {new_cabinet.id}")

            super().accept()

        except Exception as e:
            logger.error(f"Error saving cabinet type: {e}")
            msg = QMessageBox(QMessageBox.Critical, "Błąd", "Nie udało się zapisać typu szafki.", QMessageBox.Ok, self)
            msg.setDetailedText(str(e))
            msg.exec()


# ---------------------------
# Card
# ---------------------------

class CabinetTypeCard(QFrame):
    """A card widget displaying cabinet type information"""

    clicked = Signal(object)  # Signal emits the cabinet type object

    def __init__(self, cabinet_type: Any, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.cabinet_type = cabinet_type
        self.setObjectName("cabinetTypeCard")
        self.setProperty("class", "card")
        self.setFixedHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAccessibleName(f"Typ szafki {self.cabinet_type.nazwa}")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        name_label = QLabel(f"<b>{self.cabinet_type.nazwa}</b>")
        name_label.setStyleSheet("font-size: 14pt;")
        header_layout.addWidget(name_label)

        kitchen_type_label = QLabel(self.cabinet_type.kitchen_type)
        kitchen_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(kitchen_type_label)
        layout.addLayout(header_layout)

        details_layout = QFormLayout()
        details_layout.setHorizontalSpacing(20)
        details_layout.setVerticalSpacing(5)

        components_label = QLabel(
            f"Boki: {self.cabinet_type.bok_count}, "
            f"Wieńce: {self.cabinet_type.wieniec_count}, "
            f"Półki: {self.cabinet_type.polka_count}, "
            f"Fronty: {self.cabinet_type.front_count}, "
            f"Listwy: {self.cabinet_type.listwa_count}"
        )
        components_label.setWordWrap(True)
        details_layout.addRow("Komponenty:", components_label)

        hdf_value = "Tak" if self.cabinet_type.hdf_plecy else "Nie"
        hdf_label = QLabel(hdf_value)
        hdf_label.setPixmap(dot(QColor("#2ecc71") if self.cabinet_type.hdf_plecy else QColor("#e74c3c")))
        details_layout.addRow("Plecy HDF:", hdf_label)

        layout.addLayout(details_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        edit_btn = QPushButton("Edytuj")
        edit_btn.setProperty("class", "secondary")
        edit_btn.setIcon(get_icon("edit"))
        edit_btn.clicked.connect(lambda: self.clicked.emit(self.cabinet_type))
        button_layout.addWidget(edit_btn)
        layout.addLayout(button_layout)

        layout.addStretch()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        super().mousePressEvent(event)
        self.clicked.emit(self.cabinet_type)


# ---------------------------
# Main window
# ---------------------------

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
        self.duplicate_btn.setIcon(get_icon("copy"))
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
        super().resizeEvent(event)
        if self.current_view_mode == "cards":
            self._refresh_card_grid()

    def _calc_card_cols(self) -> int:
        # crude responsive: ~320px per card incl. spacing
        w = max(1, self.card_scroll.viewport().width())
        return max(1, w // 320)

    def _clear_card_layout(self) -> None:
        while self.card_layout.count() > 0:
            item = self.card_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _refresh_card_grid(self) -> None:
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
        text = self.filter_kitchen_combo.currentText()
        if text and text != "Wszystkie":
            return text
        return None

    def apply_filters(self) -> None:
        """Apply selected filters and refresh the table (DB-level for kitchen type)."""
        self.load_cabinet_types()

    def _on_search_text(self, text: str) -> None:
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
        has_sel = self._selected_cabinet_type() is not None
        self.edit_btn.setEnabled(has_sel)
        self.delete_btn.setEnabled(has_sel)
        self.duplicate_btn.setEnabled(has_sel)

    # --- Context menu ---

    def _show_table_context_menu(self, pos) -> None:
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
