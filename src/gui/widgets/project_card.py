# src/gui/widgets/project_card.py
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMenu,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from ..constants import CARD_WIDTH, CARD_HEIGHT
from ..resources.resources import get_icon


class ProjectCard(QFrame):
    """A card widget displaying project information"""

    clicked = Signal(object)
    doubleClicked = Signal(object)
    # UX: Add context menu signals for card actions
    editRequested = Signal(object)
    exportRequested = Signal(object)
    printRequested = Signal(object)
    deleteRequested = Signal(object)

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setObjectName("projectCard")
        self.setProperty("class", "card")
        # UX: Fixed width with minimum height to allow text wrapping without clipping
        self.setFixedWidth(CARD_WIDTH)
        self.setMinimumHeight(CARD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header with project name and order number
        hdr = QHBoxLayout()
        lbl_name = QLabel(f"<b>{self.project.name}</b>")
        lbl_name.setWordWrap(True)
        hdr.addWidget(lbl_name, 1)

        lbl_order = QLabel(f"#{self.project.order_number}")
        lbl_order.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_order.setStyleSheet("color: gray; font-size: 12px;")
        hdr.addWidget(lbl_order)
        layout.addLayout(hdr)

        # Info lines - more compact display
        client_line = QLabel(
            f"<b>{self.tr('Klient')}:</b> {self.project.client_name or self.tr('Brak')}"
        )
        client_line.setWordWrap(True)
        layout.addWidget(client_line)

        type_line = QLabel(f"<b>{self.tr('Typ')}:</b> {self.project.kitchen_type}")
        layout.addWidget(type_line)

        date_line = QLabel(
            f"<b>{self.tr('Data')}:</b> {self.project.created_at.strftime('%Y-%m-%d')}"
        )
        date_line.setStyleSheet("font-size: 11px; color: gray;")
        layout.addWidget(date_line)

        layout.addStretch()

        # UX: Compact button bar with icon buttons and tooltips
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        # Edit button (primary action)
        btn_edit = QPushButton()
        btn_edit.setIcon(get_icon("edit"))
        btn_edit.setToolTip(self.tr("Edytuj projekt"))
        btn_edit.setFixedSize(24, 24)
        btn_edit.clicked.connect(lambda: self.editRequested.emit(self.project))
        btn_bar.addWidget(btn_edit)

        # Export button
        btn_export = QPushButton()
        btn_export.setIcon(get_icon("export"))
        btn_export.setToolTip(self.tr("Eksportuj do Word"))
        btn_export.setFixedSize(24, 24)
        btn_export.clicked.connect(lambda: self.exportRequested.emit(self.project))
        btn_bar.addWidget(btn_export)

        # Print button
        btn_print = QPushButton()
        btn_print.setIcon(get_icon("print"))
        btn_print.setToolTip(self.tr("Drukuj"))
        btn_print.setFixedSize(24, 24)
        btn_print.clicked.connect(lambda: self.printRequested.emit(self.project))
        btn_bar.addWidget(btn_print)

        layout.addLayout(btn_bar)

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        if ev.button() == Qt.LeftButton:
            self.clicked.emit(self)

    def mouseDoubleClickEvent(self, ev):
        super().mouseDoubleClickEvent(ev)
        if ev.button() == Qt.LeftButton:
            self.doubleClicked.emit(self)

    def _show_context_menu(self, position):
        """UX: Context menu for card actions"""
        menu = QMenu(self)

        menu.addAction(
            get_icon("edit"), self.tr("Otwórz"), lambda: self.doubleClicked.emit(self)
        )
        menu.addSeparator()
        menu.addAction(
            get_icon("export"),
            self.tr("Eksportuj"),
            lambda: self.exportRequested.emit(self.project),
        )
        menu.addAction(
            get_icon("print"),
            self.tr("Drukuj"),
            lambda: self.printRequested.emit(self.project),
        )
        menu.addSeparator()
        menu.addAction(
            get_icon("delete"),
            self.tr("Usuń"),
            lambda: self.deleteRequested.emit(self.project),
        )

        menu.exec(self.mapToGlobal(position))

    def set_selected(self, selected: bool):
        """UX: Clear visual selection state management"""
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
