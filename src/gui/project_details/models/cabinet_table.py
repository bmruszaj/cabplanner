"""
Cabinet Table Model for displaying cabinets in table view.

This module provides QAbstractTableModel implementation and proxy models
for filtering and sorting cabinet data.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, TYPE_CHECKING

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QStyledItemDelegate, QTableView

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from src.db_schema.orm_models import ProjectCabinet

logger = logging.getLogger(__name__)


class CabinetTableModel(QAbstractTableModel):
    """
    Table model for displaying project cabinets.

    Provides a tabular view of cabinet data with support for:
    - Displaying cabinet properties
    - Inline editing of quantity
    - Custom delegate support for color display
    - Sorting and filtering capabilities
    """

    # Signals
    cabinet_data_changed = Signal(
        int, str, object
    )  # cabinet_id, column_name, new_value

    def __init__(
        self,
        cabinets: List[ProjectCabinet],
        session: Optional[Session] = None,
        parent=None,
    ):
        """
        Initialize the cabinet table model.

        Args:
            cabinets: List of project cabinets
            session: Database session (for future use)
            parent: Parent object
        """
        super().__init__(parent)
        self.cabinets = cabinets or []
        self.session = session

        # Column definitions
        self.columns = [
            {"key": "sequence_number", "title": "Lp.", "editable": False},
            {"key": "type_name", "title": "Typ", "editable": False},
            {"key": "body_color", "title": "Kolor korpusu", "editable": False},
            {"key": "front_color", "title": "Kolor frontu", "editable": False},
            {"key": "handle_type", "title": "Rodzaj uchwytu", "editable": False},
            {"key": "quantity", "title": "Ilość", "editable": True},
            {"key": "is_custom", "title": "Niestandardowy", "editable": False},
        ]

        logger.debug(f"Initialized CabinetTableModel with {len(cabinets)} cabinets")

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows (cabinets)."""
        return len(self.cabinets)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns."""
        return len(self.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid() or index.row() >= len(self.cabinets):
            return None

        cabinet = self.cabinets[index.row()]
        column_info = self.columns[index.column()]
        column_key = column_info["key"]

        if role == Qt.DisplayRole:
            return self._get_display_value(cabinet, column_key)

        elif role == Qt.EditRole and column_info["editable"]:
            return self._get_edit_value(cabinet, column_key)

        elif role == Qt.TextAlignmentRole:
            if column_key in ("sequence_number", "quantity"):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.BackgroundRole:
            # Highlight custom cabinets
            if cabinet.type_id is None:  # Custom cabinet
                return QColor("#fff8dc")  # Light cream color

        elif role == Qt.ToolTipRole:
            return self._get_tooltip(cabinet, column_key)

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """Set data for the given index."""
        if not index.isValid() or index.row() >= len(self.cabinets):
            return False

        cabinet = self.cabinets[index.row()]
        column_info = self.columns[index.column()]

        if role == Qt.EditRole and column_info["editable"]:
            column_key = column_info["key"]

            if column_key == "quantity":
                try:
                    new_quantity = int(value)
                    if new_quantity < 1:
                        return False

                    old_quantity = cabinet.quantity
                    cabinet.quantity = new_quantity

                    # Emit change signal
                    self.cabinet_data_changed.emit(cabinet.id, "quantity", new_quantity)
                    self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])

                    logger.debug(
                        f"Updated cabinet {cabinet.id} quantity: {old_quantity} -> {new_quantity}"
                    )
                    return True

                except (ValueError, TypeError):
                    return False

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return item flags for the given index."""
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        column_info = self.columns[index.column()]
        if column_info["editable"]:
            flags |= Qt.ItemIsEditable

        return flags

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        """Return header data."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.columns):
                return self.columns[section]["title"]

        elif role == Qt.TextAlignmentRole and orientation == Qt.Horizontal:
            if section < len(self.columns):
                column_key = self.columns[section]["key"]
                if column_key in ("sequence_number", "quantity"):
                    return Qt.AlignCenter
                return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def _get_display_value(self, cabinet: ProjectCabinet, column_key: str) -> Any:
        """Get display value for a cabinet column."""
        if column_key == "sequence_number":
            return cabinet.sequence_number or 0

        elif column_key == "type_name":
            if cabinet.cabinet_type:
                return cabinet.cabinet_type.nazwa
            return "Niestandardowy"

        elif column_key == "body_color":
            return cabinet.body_color or "Nie określono"

        elif column_key == "front_color":
            return cabinet.front_color or "Nie określono"

        elif column_key == "handle_type":
            return cabinet.handle_type or "Nie określono"

        elif column_key == "quantity":
            return cabinet.quantity or 1

        elif column_key == "is_custom":
            return "Tak" if cabinet.type_id is None else "Nie"

        return None

    def _get_edit_value(self, cabinet: ProjectCabinet, column_key: str) -> Any:
        """Get edit value for a cabinet column."""
        if column_key == "quantity":
            return cabinet.quantity or 1

        return self._get_display_value(cabinet, column_key)

    def _get_tooltip(self, cabinet: ProjectCabinet, column_key: str) -> Optional[str]:
        """Get tooltip text for a cabinet column."""
        if column_key == "type_name" and cabinet.cabinet_type:
            # Include additional type information in tooltip
            tooltip_parts = [f"Typ: {cabinet.cabinet_type.nazwa}"]

            if hasattr(cabinet.cabinet_type, "opis") and cabinet.cabinet_type.opis:
                tooltip_parts.append(f"Opis: {cabinet.cabinet_type.opis}")

            return "\n".join(tooltip_parts)

        elif column_key == "is_custom" and cabinet.type_id is None:
            return "Ta szafka została dodana jako niestandardowa"

        return None

    def moveRows(
        self,
        sourceParent: QModelIndex,
        sourceRow: int,
        count: int,
        destinationParent: QModelIndex,
        destinationChild: int,
    ) -> bool:
        """
        Move rows for drag-and-drop reordering.
        Updates sequence numbers in-memory and emits dataChanged for the first column.

        Args:
            sourceParent: Source parent index (ignored for table)
            sourceRow: Starting row to move
            count: Number of rows to move
            destinationParent: Destination parent index (ignored for table)
            destinationChild: Destination row

        Returns:
            True if move was successful
        """
        if sourceRow < 0 or sourceRow + count > len(self.cabinets):
            return False
        if destinationChild < 0 or destinationChild > len(self.cabinets):
            return False
        if sourceRow == destinationChild or (
            sourceRow < destinationChild < sourceRow + count
        ):
            return False  # No-op or invalid move

        # Calculate actual destination after removal
        dest_row = destinationChild
        if sourceRow < destinationChild:
            dest_row -= count

        # Perform the move
        if not self.beginMoveRows(
            sourceParent,
            sourceRow,
            sourceRow + count - 1,
            destinationParent,
            destinationChild,
        ):
            return False

        # Move the cabinet objects
        moving_cabinets = self.cabinets[sourceRow : sourceRow + count]

        # Remove from source
        for i in range(count):
            self.cabinets.pop(sourceRow)

        # Insert at destination
        for i, cabinet in enumerate(moving_cabinets):
            self.cabinets.insert(dest_row + i, cabinet)

        self.endMoveRows()

        # Update sequence numbers for all cabinets
        self._update_sequence_numbers()

        # Emit dataChanged for the sequence number column (first column)
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self.cabinets) - 1, 0)
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

        logger.debug(f"Moved {count} row(s) from {sourceRow} to {destinationChild}")
        return True

    def _update_sequence_numbers(self) -> None:
        """Update sequence numbers for all cabinets (1-based)."""
        for i, cabinet in enumerate(self.cabinets):
            cabinet.sequence_number = i + 1

    def set_rows(self, cabinets: List[ProjectCabinet]) -> None:
        """
        Update the cabinet list (alias for set_cabinets).

        Args:
            cabinets: New list of cabinets
        """
        self.set_cabinets(cabinets)

    def get_row(self, row: int) -> Optional[ProjectCabinet]:
        """
        Get cabinet at the specified row (alias for get_cabinet).

        Args:
            row: Row index

        Returns:
            Cabinet object or None
        """
        return self.get_cabinet(row)

    def set_cabinets(self, cabinets: List[ProjectCabinet]) -> None:
        """
        Update the cabinet list.

        Args:
            cabinets: New list of cabinets
        """
        self.beginResetModel()
        self.cabinets = cabinets or []
        self.endResetModel()

        logger.debug(f"Updated cabinet list: {len(self.cabinets)} cabinets")

    def add_cabinet(self, cabinet: ProjectCabinet) -> None:
        """
        Add a new cabinet to the model.

        Args:
            cabinet: Cabinet to add
        """
        row = len(self.cabinets)
        self.beginInsertRows(QModelIndex(), row, row)
        self.cabinets.append(cabinet)
        self.endInsertRows()

        logger.debug(f"Added cabinet to model: {cabinet.id}")

    def remove_cabinet(self, cabinet_id: int) -> bool:
        """
        Remove a cabinet from the model.

        Args:
            cabinet_id: ID of cabinet to remove

        Returns:
            True if cabinet was removed
        """
        for i, cabinet in enumerate(self.cabinets):
            if cabinet.id == cabinet_id:
                self.beginRemoveRows(QModelIndex(), i, i)
                self.cabinets.pop(i)
                self.endRemoveRows()

                logger.debug(f"Removed cabinet from model: {cabinet_id}")
                return True

        return False

    def get_cabinet(self, row: int) -> Optional[ProjectCabinet]:
        """
        Get cabinet at the specified row.

        Args:
            row: Row index

        Returns:
            Cabinet object or None
        """
        if 0 <= row < len(self.cabinets):
            return self.cabinets[row]
        return None

    def find_cabinet_row(self, cabinet_id: int) -> int:
        """
        Find the row index for a cabinet ID.

        Args:
            cabinet_id: ID of cabinet to find

        Returns:
            Row index or -1 if not found
        """
        for i, cabinet in enumerate(self.cabinets):
            if cabinet.id == cabinet_id:
                return i
        return -1


class CabinetProxyModel(QSortFilterProxyModel):
    """
    Proxy model for filtering and sorting cabinets.

    Provides:
    - Search filtering by cabinet name, colors, etc.
    - Type filtering (standard vs custom)
    - Sorting by any column
    """

    def __init__(self, parent=None):
        """Initialize the proxy model."""
        super().__init__(parent)

        self._search_text = ""
        self._filter_type = "all"  # "all", "standard", "custom"
        self._color_filter = ""

        # Configure sorting
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Check if a row should be included in the filtered view."""
        source_model = self.sourceModel()
        if not source_model:
            return True

        cabinet = source_model.get_cabinet(source_row)
        if not cabinet:
            return True

        # Apply search filter
        if self._search_text and not self._matches_search(cabinet):
            return False

        # Apply type filter
        if not self._matches_type_filter(cabinet):
            return False

        # Apply color filter
        if self._color_filter and not self._matches_color_filter(cabinet):
            return False

        return True

    def _matches_search(self, cabinet: ProjectCabinet) -> bool:
        """Check if cabinet matches search criteria."""
        search_lower = self._search_text.lower()

        # Search in cabinet type name
        if cabinet.cabinet_type and search_lower in cabinet.cabinet_type.nazwa.lower():
            return True

        # Search in colors
        if cabinet.body_color and search_lower in cabinet.body_color.lower():
            return True
        if cabinet.front_color and search_lower in cabinet.front_color.lower():
            return True

        # Search in handle type
        if cabinet.handle_type and search_lower in cabinet.handle_type.lower():
            return True

        return False

    def _matches_type_filter(self, cabinet: ProjectCabinet) -> bool:
        """Check if cabinet matches type filter."""
        if self._filter_type == "all":
            return True
        elif self._filter_type == "standard":
            return cabinet.type_id is not None
        elif self._filter_type == "custom":
            return cabinet.type_id is None

        return True

    def _matches_color_filter(self, cabinet: ProjectCabinet) -> bool:
        """Check if cabinet matches color filter."""
        color_lower = self._color_filter.lower()

        if cabinet.body_color and color_lower in cabinet.body_color.lower():
            return True
        if cabinet.front_color and color_lower in cabinet.front_color.lower():
            return True

        return False

    def set_search_filter(self, search_text: str) -> None:
        """
        Set search filter text.

        Args:
            search_text: Text to search for
        """
        self._search_text = search_text.strip()
        self.invalidateFilter()

        logger.debug(f"Applied search filter: '{search_text}'")

    def set_type_filter(self, filter_type: str) -> None:
        """
        Set type filter.

        Args:
            filter_type: "all", "standard", or "custom"
        """
        self._filter_type = filter_type
        self.invalidateFilter()

        logger.debug(f"Applied type filter: {filter_type}")

    def set_color_filter(self, color: str) -> None:
        """
        Set color filter.

        Args:
            color: Color to filter by
        """
        self._color_filter = color.strip()
        self.invalidateFilter()

        logger.debug(f"Applied color filter: '{color}'")

    def clear_filters(self) -> None:
        """Clear all filters."""
        self._search_text = ""
        self._filter_type = "all"
        self._color_filter = ""
        self.invalidateFilter()

        logger.debug("Cleared all filters")

    def get_filtered_cabinet_count(self) -> int:
        """Get the number of cabinets after filtering."""
        return self.rowCount()


def create_cabinet_proxy_model(base_model: CabinetTableModel) -> CabinetProxyModel:
    """
    Helper function to create a configured proxy model.

    Args:
        base_model: The base cabinet table model

    Returns:
        Configured proxy model
    """
    proxy = CabinetProxyModel()
    proxy.setSourceModel(base_model)
    return proxy


def make_proxy(model: CabinetTableModel) -> QSortFilterProxyModel:
    """
    Create a proxy model with case-insensitive, all-columns filtering.

    Args:
        model: The base cabinet table model

    Returns:
        Configured proxy model for sorting and filtering
    """
    return create_cabinet_proxy_model(model)


class ColorChipDelegate(QStyledItemDelegate):
    """
    Custom delegate for displaying color values as color chips.

    This delegate renders color columns with visual color chips
    similar to the ColorChip widget used in card view.
    """

    def __init__(self, parent=None):
        """Initialize the color chip delegate."""
        super().__init__(parent)

    def paint(self, painter, option, index):
        """Paint the color chip representation."""
        # For now, use default painting - could be enhanced with actual color chips
        # The ColorChip widget from widgets package could be used as reference
        super().paint(painter, option, index)

        # TODO: Implement custom color chip painting
        # - Parse color value from display text
        # - Draw color rectangle with border
        # - Add color name text


def setup_color_chip_delegate(table_view: QTableView, model: CabinetTableModel) -> None:
    """
    Helper function to register ColorChipDelegate for color columns.

    Args:
        table_view: The table view to apply delegates to
        model: The cabinet table model to determine color columns
    """
    if not table_view or not model:
        return

    delegate = ColorChipDelegate(table_view)

    # Find color columns and apply delegate
    for col_idx, column_info in enumerate(model.columns):
        if column_info["key"] in ("body_color", "front_color"):
            table_view.setItemDelegateForColumn(col_idx, delegate)

    logger.debug("Applied ColorChipDelegate to color columns")
