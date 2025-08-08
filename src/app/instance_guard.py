import sys
from PySide6.QtCore import QSharedMemory
from PySide6.QtWidgets import QMessageBox


def enforce_single_instance(key: str = "CabplannerApp") -> None:
    """Enforce that only one instance of the application is running."""
    single = QSharedMemory(key)
    if not single.create(1):
        QMessageBox.warning(None, "Cabplanner", "Another instance is already running.")
        sys.exit(0)
