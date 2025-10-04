# src/gui/widgets/loading_overlay.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class LoadingOverlay(QWidget):
    """UX: Loading overlay for non-blocking feedback during operations"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("loadingOverlay")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(self.tr("Ładowanie projektów..."))
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("loadingLabel")
        layout.addWidget(label)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            self.resize(self.parent().size())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent():
            self.resize(self.parent().size())
