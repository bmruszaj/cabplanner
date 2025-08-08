import sys
from pathlib import Path


def get_base_path() -> Path:
    """Get the base path for the application (frozen vs. dev mode)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parents[2]


def get_project_root() -> Path:
    """Get the project root directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parents[2]
