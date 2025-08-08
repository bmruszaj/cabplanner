"""Safe ZIP file operations with zip-slip protection."""

import zipfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class UnsafeZipError(Exception):
    """Exception raised when ZIP contains unsafe paths."""

    pass


def safe_extract(zip_path: Path, extract_to: Path) -> None:
    """
    Safely extract a ZIP file with zip-slip protection.

    Args:
        zip_path: Path to the ZIP file to extract
        extract_to: Directory to extract files to

    Raises:
        UnsafeZipError: If ZIP contains paths that would escape the target directory
        zipfile.BadZipFile: If ZIP file is corrupted
    """
    logger.debug("Extracting %s to %s", zip_path, extract_to)

    extract_to.mkdir(parents=True, exist_ok=True)
    resolved_extract_to = extract_to.resolve()

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Check all paths for safety before extracting
        for member in zip_ref.namelist():
            # Resolve the member path within the extraction directory
            member_path = (extract_to / member).resolve()

            # Ensure the resolved path is within the extraction directory
            if not str(member_path).startswith(str(resolved_extract_to)):
                raise UnsafeZipError(f"Unsafe path in ZIP: {member}")

        # If all paths are safe, extract everything
        zip_ref.extractall(path=extract_to)
        logger.debug("Successfully extracted %d files", len(zip_ref.namelist()))


def find_app_root(
    extract_dir: Path, exe_name: str = "cabplanner.exe"
) -> Optional[Path]:
    """
    Find the application root directory by locating the main executable.

    Args:
        extract_dir: Directory to search in
        exe_name: Name of the executable to find

    Returns:
        Path to the directory containing the executable, or None if not found
    """
    logger.debug("Searching for %s in %s", exe_name, extract_dir)

    # Search recursively for the executable
    exe_files = list(extract_dir.rglob(exe_name))

    if not exe_files:
        logger.error("Executable %s not found in extracted files", exe_name)
        return None

    if len(exe_files) > 1:
        logger.warning("Multiple %s files found, using first one", exe_name)
        for exe_file in exe_files:
            logger.warning("Found: %s", exe_file)

    app_root = exe_files[0].parent
    logger.debug("Found application root: %s", app_root)

    # Verify the executable is not empty
    if exe_files[0].stat().st_size == 0:
        logger.error("Executable %s is empty", exe_files[0])
        return None

    return app_root


def verify_onedir_structure(app_root: Path) -> bool:
    """
    Verify that the extracted directory has the expected onedir structure.

    Args:
        app_root: Path to the application root directory

    Returns:
        True if structure is valid (contains cabplanner.exe and _internal/)
    """
    exe_path = app_root / "cabplanner.exe"
    internal_dir = app_root / "_internal"

    if not exe_path.exists():
        logger.error("Missing cabplanner.exe in %s", app_root)
        return False

    if not internal_dir.exists() or not internal_dir.is_dir():
        logger.error("Missing _internal/ directory in %s", app_root)
        return False

    logger.debug("Verified onedir structure in %s", app_root)
    return True
