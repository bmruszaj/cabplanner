# src/gui/layouts/flow_layout.py
from PySide6.QtWidgets import QLayout, QSizePolicy
from PySide6.QtCore import Qt, QRect, QPoint, QSize

from ..constants import CARD_WIDTH


class FlowLayout(QLayout):
    """
    UX: Custom flow layout that wraps widgets based on available width.
    Based on Qt's FlowLayout example for smooth responsive behavior.
    """

    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

        self._item_list = []
        self._spacing = spacing

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        m = self.contentsMargins()
        w = CARD_WIDTH
        h = 0
        for it in self._item_list:
            wid = it.widget()
            if wid and wid.isVisible():
                sz = it.minimumSize()
                w = max(w, sz.width())
                h = max(h, sz.height())
        return QSize(w + m.left() + m.right(), h + m.top() + m.bottom())

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        line_h = 0
        sp = self.spacing()
        right = rect.x() + rect.width() - m.right()

        for item in self._item_list:
            w = item.widget()
            if not w or not w.isVisible():
                continue

            sz = item.sizeHint()  # fixed from card
            next_x = x + sz.width()
            if next_x > right and line_h > 0:
                # wrap
                x = rect.x() + m.left()
                y = y + line_h + sp
                next_x = x + sz.width()
                line_h = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), sz))

            x = next_x + sp
            line_h = max(line_h, sz.height())

        total_h = (y + line_h + m.bottom()) - rect.y()
        return total_h

    def spacing(self):
        if self._spacing >= 0:
            return self._spacing
        else:
            return (
                self.parent()
                .style()
                .layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
                )
            )

    def clear_layout(self):
        """Remove all items from layout without deleting widgets"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def addCard(self, card_widget):
        """Add a card widget to the layout."""
        self.addWidget(card_widget)

    def clear_cards(self):
        """Clear all cards from layout and delete them."""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                child.widget().deleteLater()

    def clear_layout_only(self):
        """Clear layout without deleting widgets."""
        # Store widgets temporarily to avoid Qt geometry issues
        widgets = []
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)  # Remove from layout without deleting
                widgets.append(widget)

        # Process events to ensure layout is cleared
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        return widgets
