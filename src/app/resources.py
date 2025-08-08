import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon


def _base_path() -> Path:
    """Return base dir for assets (exe dir in frozen; project root in dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent  # onedir layout
    return Path(__file__).resolve().parents[2]


def set_app_icon(app: QApplication) -> None:
    """Set the application icon from the filesystem."""
    try:
        base = _base_path()
        candidates = [
            base / "icon.ico",
            base / "_internal" / "icon.ico",
            Path(__file__).resolve().parents[2] / "icon.ico",
        ]
        for p in candidates:
            if p.exists():
                app.setWindowIcon(QIcon(str(p)))
                return
    except Exception:
        pass
