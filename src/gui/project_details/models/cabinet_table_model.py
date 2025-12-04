"""
Cabinet Table Model

QAbstractTableModel implementation for displaying cabinet data in table format.
Provides standard table model interface for ProjectCabinet objects.
"""

from typing import List
from PySide6.QtCore import QAbstractTableModel, Signal, Qt, QModelIndex

from src.db_schema.orm_models import ProjectCabinet


class CabinetTableModel(QAbstractTableModel):
    """Table model for cabinet data."""

    cabinet_data_changed = Signal(int, str, object)

    def __init__(self, cabinets: List[ProjectCabinet], parent=None):
        super().__init__(parent)
        self.cabinets = cabinets or []
        self.columns = ["Lp.", "Typ", "Korpus", "Front", "Uchwyt", "Ilość"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.cabinets)

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.cabinets):
            return None

        cabinet = self.cabinets[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return cabinet.sequence_number
            elif col == 1:
                return (
                    cabinet.cabinet_type.name
                    if cabinet.cabinet_type
                    else "Niestandardowy"
                )
            elif col == 2:
                return cabinet.body_color or "Nie określono"
            elif col == 3:
                return cabinet.front_color or "Nie określono"
            elif col == 4:
                return cabinet.handle_type or "Nie określono"
            elif col == 5:
                return cabinet.quantity

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns[section]
        return None

    def set_rows(self, cabinets: List[ProjectCabinet]):
        self.beginResetModel()
        self.cabinets = cabinets
        self.endResetModel()
