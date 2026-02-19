"""
Cabinet table model used by ProjectDetailsView.
"""

from typing import List
from PySide6.QtCore import QAbstractTableModel, Signal, Qt, QModelIndex

from src.db_schema.orm_models import ProjectCabinet


class CabinetTableModel(QAbstractTableModel):
    """Table model for cabinet data shown in ProjectDetailsView."""

    cabinet_data_changed = Signal(int, str, object)

    def __init__(self, cabinets: List[ProjectCabinet], parent=None):
        super().__init__(parent)
        self.cabinets = cabinets or []
        self.columns = [
            "Sekwencja",
            "Nazwa",
            "Wymiary",
            "Kolor przód",
            "Kolor korpus",
            "Ilość",
        ]

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.cabinets)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.cabinets):
            return None

        cabinet = self.cabinets[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.UserRole and col == 0:
            return cabinet.id

        if role == Qt.ItemDataRole.TextAlignmentRole and col in (0, 5):
            return int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

        if role == Qt.DisplayRole:
            if col == 0:
                return cabinet.sequence_number or ""
            if col == 1:
                return self._cabinet_name(cabinet)
            if col == 2:
                return self._cabinet_dimensions(cabinet)
            if col == 3:
                return cabinet.front_color or "Biały"
            if col == 4:
                return cabinet.body_color or "Biały"
            if col == 5:
                return cabinet.quantity or 1

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.DisplayRole
            and 0 <= section < len(self.columns)
        ):
            return self.columns[section]
        return None

    def set_rows(self, cabinets: List[ProjectCabinet]):
        self.beginResetModel()
        self.cabinets = cabinets or []
        self.endResetModel()

    def get_cabinet_id(self, row: int):
        """Return cabinet ID for a row."""
        if row < 0 or row >= len(self.cabinets):
            return None
        return self.cabinets[row].id

    def _cabinet_name(self, cabinet: ProjectCabinet) -> str:
        if getattr(cabinet, "cabinet_type", None) and cabinet.cabinet_type.name:
            return cabinet.cabinet_type.name

        parts = getattr(cabinet, "parts", None) or []
        for part in parts:
            ctx = getattr(part, "calc_context_json", None)
            if isinstance(ctx, dict) and ctx.get("template_name"):
                return f"{ctx['template_name']} + niestandardowa"

        return "Niestandardowy"

    def _cabinet_dimensions(self, cabinet: ProjectCabinet) -> str:
        width = height = depth = None
        parts = getattr(cabinet, "parts", None) or []

        if len(parts) == 1:
            part = parts[0]
            if self._is_positive_number(getattr(part, "width_mm", None)):
                width = int(part.width_mm)
            if self._is_positive_number(getattr(part, "height_mm", None)):
                height = int(part.height_mm)
        elif len(parts) >= 2:
            widths = [
                int(p.width_mm)
                for p in parts
                if self._is_positive_number(getattr(p, "width_mm", None))
            ]
            heights = [
                int(p.height_mm)
                for p in parts
                if self._is_positive_number(getattr(p, "height_mm", None))
            ]

            if widths:
                width = widths[0] if len(set(widths)) == 1 else max(widths)
            if heights:
                height = heights[0] if len(set(heights)) == 1 else max(heights)
            # Depth is intentionally not inferred from mixed parts.

        if width and height:
            dims = f"{width}x{height}"
            if depth:
                dims += f"x{depth}"
            return f"{dims} mm"

        return "brak wymiarów"

    @staticmethod
    def _is_positive_number(value) -> bool:
        return isinstance(value, (int, float)) and value > 0
