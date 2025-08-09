"""Runtime detection and path utilities."""
import sys
import tempfile
from pathlib import Path


def is_frozen() -> bool:
    """Check if the application is running as a frozen executable."""
    return getattr(sys, "frozen", False)


def install_dir() -> Path:
    """Get the installation directory of the application."""
    if is_frozen():
        return Path(sys.executable).parent
    else:
        # For development, return the project root
        return Path(__file__).parent.parent.parent.parent


def tempdir() -> Path:
    """Get a temporary directory for updates."""
    return Path(tempfile.mkdtemp(prefix="cabplanner_update_"))
