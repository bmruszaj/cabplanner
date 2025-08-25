"""
Utility functions for project details UI.
"""

import logging
import os
import platform
import subprocess

logger = logging.getLogger(__name__)


def open_or_print(file_path: str, action: str = "open") -> bool:
    """Open or print a file using OS default application."""
    try:
        if action == "print":
            if platform.system() == "Windows":
                os.startfile(file_path, "print")
            else:
                # For non-Windows, show unsupported message
                return False
        else:  # action == "open"
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux and others
                subprocess.run(["xdg-open", file_path])
        return True
    except (OSError, subprocess.SubprocessError):
        logger.exception(f"Failed to {action} file {file_path}")
        return False
