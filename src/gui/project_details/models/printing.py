"""
Print Helper for cross-platform print and open operations.

This module provides cross-platform functionality for opening and printing files,
with Windows-specific printing support.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from typing import Optional

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def open_or_print(path: str, action: str = "open") -> bool:
    """
    Open or print a file using platform-appropriate methods.

    Args:
        path: Path to the file to open/print
        action: "open" to open file, "print" to print file

    Returns:
        True if operation was initiated successfully

    Notes:
        - Works cross-platform for "open"
        - "print" uses Windows verb when on Windows, otherwise opens file
        - On Windows: uses os.startfile() with appropriate verb
        - Non-Windows: uses QDesktopServices.openUrl() for both actions
    """
    if not os.path.exists(path):
        logger.error(f"File does not exist: {path}")
        return False

    try:
        if sys.platform.startswith("win"):
            # Windows: use os.startfile with appropriate verb
            if action == "print":
                os.startfile(path, "print")
                logger.debug(f"Initiated Windows print for: {path}")
            else:
                os.startfile(path)
                logger.debug(f"Opened file on Windows: {path}")
        else:
            # Non-Windows: use QDesktopServices for both actions
            file_url = QUrl.fromLocalFile(path)
            success = QDesktopServices.openUrl(file_url)
            if success:
                action_name = "print" if action == "print" else "open"
                logger.debug(f"Used QDesktopServices to {action_name}: {path}")
            else:
                logger.error(f"QDesktopServices failed to open: {path}")
                return False

        return True

    except Exception as e:
        logger.error(f"Failed to {action} file {path}: {e}")
        return False


class PrintHelper(QObject):
    """
    Helper class for printing operations on Windows.

    Provides methods for:
    - Printing documents using Windows shell
    - Opening print dialogs
    - Managing temporary print files
    - Print status feedback
    """

    # Signals
    print_started = Signal(str)  # file_path
    print_completed = Signal(str)  # file_path
    print_failed = Signal(str, str)  # file_path, error_message

    def __init__(self, parent=None):
        """Initialize the print helper."""
        super().__init__(parent)
        self._temp_files = []  # Track temporary files for cleanup

        logger.debug("Initialized PrintHelper")

    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return sys.platform.startswith("win")

    def can_print(self) -> bool:
        """Check if printing is available on this platform."""
        return self.is_windows()

    def print_file(self, file_path: str, show_dialog: bool = True) -> bool:
        """
        Print a file using Windows shell.

        Args:
            file_path: Path to file to print
            show_dialog: Whether to show print dialog

        Returns:
            True if print was initiated successfully
        """
        if not self.can_print():
            error_msg = "Drukowanie jest dostępne tylko w systemie Windows"
            logger.error(error_msg)
            self.print_failed.emit(file_path, error_msg)
            return False

        if not os.path.exists(file_path):
            error_msg = f"Plik nie istnieje: {file_path}"
            logger.error(error_msg)
            self.print_failed.emit(file_path, error_msg)
            return False

        try:
            logger.debug(f"Printing file: {file_path}")
            self.print_started.emit(file_path)

            if show_dialog:
                # Use shell verb to show print dialog
                os.startfile(file_path, "print")
            else:
                # Direct print without dialog
                os.startfile(file_path, "printto")

            self.print_completed.emit(file_path)
            logger.debug(f"Print initiated successfully: {file_path}")
            return True

        except Exception as e:
            error_msg = f"Błąd podczas drukowania: {e}"
            logger.error(error_msg)
            self.print_failed.emit(file_path, error_msg)
            return False

    def print_pdf_content(
        self, pdf_content: bytes, filename: str = "document.pdf"
    ) -> bool:
        """
        Print PDF content by creating temporary file.

        Args:
            pdf_content: PDF file content as bytes
            filename: Filename for temporary file

        Returns:
            True if print was initiated successfully
        """
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"cabplanner_print_{filename}")

            # Write PDF content
            with open(temp_path, "wb") as f:
                f.write(pdf_content)

            # Track for cleanup
            self._temp_files.append(temp_path)

            # Print the file
            success = self.print_file(temp_path)

            if success:
                logger.debug(f"Created and printed temporary PDF: {temp_path}")

            return success

        except Exception as e:
            error_msg = f"Błąd podczas tworzenia pliku PDF do druku: {e}"
            logger.error(error_msg)
            self.print_failed.emit(filename, error_msg)
            return False

    def print_html_content(
        self, html_content: str, filename: str = "document.html"
    ) -> bool:
        """
        Print HTML content by creating temporary file.

        Args:
            html_content: HTML content as string
            filename: Filename for temporary file

        Returns:
            True if print was initiated successfully
        """
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"cabplanner_print_{filename}")

            # Write HTML content
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Track for cleanup
            self._temp_files.append(temp_path)

            # Print the file
            success = self.print_file(temp_path)

            if success:
                logger.debug(f"Created and printed temporary HTML: {temp_path}")

            return success

        except Exception as e:
            error_msg = f"Błąd podczas tworzenia pliku HTML do druku: {e}"
            logger.error(error_msg)
            self.print_failed.emit(filename, error_msg)
            return False

    def show_print_preview(self, file_path: str) -> bool:
        """
        Show print preview for a file.

        Args:
            file_path: Path to file to preview

        Returns:
            True if preview was opened successfully
        """
        if not self.can_print():
            return False

        if not os.path.exists(file_path):
            logger.error(f"File does not exist: {file_path}")
            return False

        try:
            # Open file with default application (usually shows preview)
            os.startfile(file_path)
            logger.debug(f"Opened print preview: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error opening print preview: {e}")
            return False

    def get_default_printer(self) -> Optional[str]:
        """
        Get the name of the default printer.

        Returns:
            Default printer name or None if not available
        """
        if not self.is_windows():
            return None

        try:
            import winreg

            # Query registry for default printer
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows NT\CurrentVersion\Windows",
            ) as key:
                default_printer, _ = winreg.QueryValueEx(key, "Device")

                # Extract printer name (before first comma)
                printer_name = default_printer.split(",")[0]
                logger.debug(f"Default printer: {printer_name}")
                return printer_name

        except Exception as e:
            logger.warning(f"Could not get default printer: {e}")
            return None

    def list_available_printers(self) -> list[str]:
        """
        Get list of available printers.

        Returns:
            List of printer names
        """
        if not self.is_windows():
            return []

        try:
            import win32print

            printers = []
            printer_info = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )

            for printer in printer_info:
                printers.append(printer[2])  # Printer name

            logger.debug(f"Found {len(printers)} printers")
            return printers

        except ImportError:
            logger.warning("pywin32 not available, cannot list printers")
            return []
        except Exception as e:
            logger.error(f"Error listing printers: {e}")
            return []

    def cleanup_temp_files(self) -> None:
        """Clean up temporary print files."""
        cleaned = 0
        for temp_path in self._temp_files.copy():
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    cleaned += 1
                self._temp_files.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {temp_path}: {e}")

        if cleaned > 0:
            logger.debug(f"Cleaned up {cleaned} temporary print files")

    def show_not_supported_message(self, parent_widget=None) -> None:
        """Show message that printing is not supported on this platform."""
        QMessageBox.warning(
            parent_widget,
            "Drukowanie niedostępne",
            "Funkcja drukowania jest dostępna tylko w systemie Windows.",
            QMessageBox.Ok,
        )

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.cleanup_temp_files()


# Module-level convenience functions
def print_file(file_path: str, show_dialog: bool = True) -> bool:
    """
    Convenience function to print a file.

    Args:
        file_path: Path to file to print
        show_dialog: Whether to show print dialog

    Returns:
        True if print was initiated successfully
    """
    helper = PrintHelper()
    return helper.print_file(file_path, show_dialog)


def can_print() -> bool:
    """
    Check if printing is available on this platform.

    Returns:
        True if printing is available
    """
    helper = PrintHelper()
    return helper.can_print()


def get_default_printer() -> Optional[str]:
    """
    Get the default printer name.

    Returns:
        Default printer name or None
    """
    helper = PrintHelper()
    return helper.get_default_printer()


def print_pdf_bytes(pdf_content: bytes, filename: str = "document.pdf") -> bool:
    """
    Print PDF content from bytes.

    Args:
        pdf_content: PDF content as bytes
        filename: Filename for temporary file

    Returns:
        True if print was successful
    """
    helper = PrintHelper()
    return helper.print_pdf_content(pdf_content, filename)


def print_html_string(html_content: str, filename: str = "document.html") -> bool:
    """
    Print HTML content from string.

    Args:
        html_content: HTML content as string
        filename: Filename for temporary file

    Returns:
        True if print was successful
    """
    helper = PrintHelper()
    return helper.print_html_content(html_content, filename)
