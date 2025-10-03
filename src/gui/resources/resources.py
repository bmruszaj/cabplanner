"""
Resource manager for the Cabplanner application.
This module provides access to icons and other resources.
"""

from pathlib import Path
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap, QImage

# Base resource directories
RESOURCE_DIR = Path(__file__).resolve().parent
ICON_DIR = RESOURCE_DIR / "icons"

# Ensure directories exist
ICON_DIR.mkdir(exist_ok=True)

# Dictionary mapping icon names to their paths
# These should be created/downloaded and placed in the icons folder
ICON_PATHS = {
    # Main toolbar icons
    "new_project": ICON_DIR / "new_project.png",
    "open_project": ICON_DIR / "open_project.png",
    "save": ICON_DIR / "save.png",
    "delete": ICON_DIR / "delete.png",
    "export": ICON_DIR / "export.png",
    "print": ICON_DIR / "print.png",
    "settings": ICON_DIR / "settings.png",
    "cabinet": ICON_DIR / "cabinet.png",
    "catalog": ICON_DIR / "catalog.png",
    "dashboard": ICON_DIR / "dashboard.png",
    # Action icons
    "add": ICON_DIR / "add.png",
    "edit": ICON_DIR / "edit.png",
    "edit_white": ICON_DIR / "edit_white.png",
    "export_white": ICON_DIR / "export_white.png",
    "duplicate": ICON_DIR / "edit.png",  # Use edit icon for duplicate
    "remove": ICON_DIR / "remove.png",
    "search": ICON_DIR / "search.png",
    "filter": ICON_DIR / "filter.png",
    "menu": ICON_DIR / "menu.png",
    "table": ICON_DIR / "menu.png",  # Use menu icon for table view
    "close": ICON_DIR / "close.png",
    "help": ICON_DIR / "help.png",
    "arrow_left": ICON_DIR / "arrow_left.png",
    "arrow_right": ICON_DIR / "arrow_right.png",
    "image": ICON_DIR / "image.png",
    "project": ICON_DIR / "project.png",
    "refresh": ICON_DIR / "refresh.png",
    "cancel": ICON_DIR / "cancel.png",
    "parts": ICON_DIR / "parts.png",
    "accessories": ICON_DIR / "accessories.png",
    # Status icons
    "success": ICON_DIR / "success.png",
    "warning": ICON_DIR / "warning.png",
    "error": ICON_DIR / "error.png",
    "info": ICON_DIR / "info.png",
    # Misc
    "logo": ICON_DIR / "logo.png",
    "check": ICON_DIR / "check.png",
    "check_white": ICON_DIR / "check_white.png",
}


def get_icon(name, size=None):
    """
    Get an icon by name.

    Args:
        name: The name of the icon
        size: Optional QSize for the icon

    Returns:
        QIcon: The requested icon
    """
    path = ICON_PATHS.get(name)
    if not path or not path.exists():
        print(f"Warning: Icon {name} not found at {path}")
        return QIcon()

    icon = QIcon(str(path))

    if size and isinstance(size, QSize):
        pixmap = icon.pixmap(size)
        icon = QIcon(pixmap)

    return icon


def get_image(name):
    """
    Get an image by name.

    Args:
        name: The name of the image

    Returns:
        QImage: The requested image
    """
    path = ICON_PATHS.get(name)
    if not path or not path.exists():
        print(f"Warning: Image {name} not found at {path}")
        return QImage()

    return QImage(str(path))


def get_pixmap(name):
    """
    Get a pixmap by name.

    Args:
        name: The name of the image

    Returns:
        QPixmap: The requested pixmap
    """
    path = ICON_PATHS.get(name)
    if not path or not path.exists():
        print(f"Warning: Image {name} not found at {path}")
        return QPixmap()

    return QPixmap(str(path))
