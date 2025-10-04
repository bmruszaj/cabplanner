"""
Common layouts for GUI components.
Shared layouts that can be used across different modules.
"""

import logging
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtWidgets import QLayout, QSizePolicy, QApplication

logger = logging.getLogger(__name__)

# Default card width constant
CARD_WIDTH = 320


class ResponsiveFlowLayout(QLayout):
    """
    Responsive flow layout that wraps widgets based on available width.
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
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def spacing(self):
        if self._spacing >= 0:
            return self._spacing
        else:
            return self.smartSpacing(
                QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal
            )

    def smartSpacing(self, pm, orientation):
        parent = self.parent()
        if not parent:
            return -1
        if parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(+left, +top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            widget = item.widget()
            space_x = self.spacing()
            if space_x == -1:
                space_x = widget.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Horizontal,
                )
            space_y = self.spacing()
            if space_y == -1:
                space_y = widget.style().layoutSpacing(
                    QSizePolicy.ControlType.PushButton,
                    QSizePolicy.ControlType.PushButton,
                    Qt.Orientation.Vertical,
                )

            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom

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
        QApplication.processEvents()
        return widgets

    def activate(self):
        """Force layout to recalculate."""
        try:
            super().activate()
        except Exception:
            logger.exception("Failed to activate layout")
            # Fall back to update if activation fails
            if hasattr(self, "update"):
                self.update()
