"""Cabinet type table model with proper sorting and display."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, List, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QObject
from PySide6.QtGui import QColor

from src.gui.utils.ui_bits import dot


class Col(IntEnum):
    """Column indices for the cabinet type table."""
    ID = 0
    NAZWA = 1
    TYP = 2
    HDF = 3
    LISTWA = 4
    WIENIEC = 5
    BOK = 6
    FRONT = 7
    POLKA = 8


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
        """Update the model with new cabinet types data."""
        self.beginResetModel()
        self.cabinet_types = cabinet_types
        self.endResetModel()

    def get_cabinet_type_at_row(self, row: int) -> Optional[Any]:
        """Get the cabinet type at the specified row."""
        if 0 <= row < len(self.cabinet_types):
            return self.cabinet_types[row]
        return None
