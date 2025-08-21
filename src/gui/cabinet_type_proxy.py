"""Cabinet type proxy model for filtering and search."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QModelIndex, QObject, QSortFilterProxyModel, Qt

from src.gui.cabinet_type_model import CabinetTypeModel, Col


class CabinetTypeProxyModel(QSortFilterProxyModel):
    """Proxy that handles text search across name/type."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._search_text: str = ""

    def set_search_text(self, text: str) -> None:
        """Set the search text and invalidate the filter."""
        self._search_text = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # type: ignore[override]
        """Check if a row should be included based on the search text."""
        if not self._search_text:
            return True
        m: CabinetTypeModel = self.sourceModel()  # type: ignore[assignment]
        name_idx = m.index(source_row, Col.NAZWA)
        type_idx = m.index(source_row, Col.TYP)
        name = (m.data(name_idx, Qt.DisplayRole) or "").lower()
        typ = (m.data(type_idx, Qt.DisplayRole) or "").lower()
        return self._search_text in name or self._search_text in typ
