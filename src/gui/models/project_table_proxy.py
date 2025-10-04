# src/gui/models/project_table_proxy.py
from PySide6.QtCore import QSortFilterProxyModel, Qt


class ProjectTableModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting projects in table view."""

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

        # UX: Enhanced search - check project name, client, and kitchen type columns
        for col in (1, 2, 3):  # name, kitchen_type, client
            idx = src.index(source_row, col, source_parent)
            val = str(src.data(idx) or "").lower()
            if pattern in val:
                return True
        return False
