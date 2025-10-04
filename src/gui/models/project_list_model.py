# src/gui/models/project_list_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class ProjectListModel(QAbstractTableModel):
    """Internal list model: wraps projects for QTableView"""

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
