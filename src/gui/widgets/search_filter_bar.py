# src/gui/widgets/search_filter_bar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox
from PySide6.QtCore import Signal

from src.constants import KITCHEN_TYPES


class SearchFilterBar(QWidget):
    """Search and filter bar for the projects view"""

    searchTextChanged = Signal(str)
    filterChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # UX: Enhanced search input with better placeholder and tooltip
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.tr("Szukaj projektów po nazwie, kliencie lub typie...")
        )
        self.search_input.setToolTip(
            self.tr(
                "Wpisz tekst aby przeszukać projekty po nazwie, kliencie lub typie kuchni"
            )
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(
            lambda txt: self.searchTextChanged.emit(txt)
        )
        layout.addWidget(self.search_input, 3)

        # Kitchen-type filter
        self.filter_combo = QComboBox()
        self.filter_combo.setToolTip(self.tr("Filtruj projekty według typu kuchni"))
        self.filter_combo.addItem(self.tr("Wszystkie typy"), "")
        for kt in KITCHEN_TYPES:
            self.filter_combo.addItem(kt, kt)
        self.filter_combo.currentIndexChanged.connect(
            lambda _: self.filterChanged.emit(self.filter_combo.currentData())
        )
        layout.addWidget(self.filter_combo, 1)

    def focus_search(self):
        """UX: Helper method to focus search input via shortcut"""
        self.search_input.setFocus()
        self.search_input.selectAll()
