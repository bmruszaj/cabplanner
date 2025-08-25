"""
Cabinet Proxy Model

QSortFilterProxyModel implementation for filtering and sorting cabinet data.
Provides search functionality and sorting capabilities for the cabinet table.
"""

from PySide6.QtCore import QSortFilterProxyModel, Qt


class CabinetProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering and sorting cabinets."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_filter = ""

    def set_search_filter(self, text: str):
        """Set the search filter text and invalidate the filter."""
        self._search_filter = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        """Determine if a row should be included based on the search filter."""
        if not self._search_filter:
            return True

        model = self.sourceModel()
        for col in range(model.columnCount()):
            index = model.index(source_row, col, source_parent)
            data = model.data(index, Qt.DisplayRole)
            if data and self._search_filter in str(data).lower():
                return True

        return False
