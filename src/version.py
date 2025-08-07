import logging
import re
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_VERSION = "1.0.0"
VERSION_FILE_PATH = Path(__file__).resolve().parents[1] / ".version"


def read_version_from_file() -> str:
    try:
        text = VERSION_FILE_PATH.read_text().strip()
        return text or DEFAULT_VERSION
    except Exception as e:
        log.warning(f"Could not read version file ({VERSION_FILE_PATH}): {e}")
        return DEFAULT_VERSION


def determine_channel(version: str) -> str:
    """
    Extracts the prerelease label from SemVer (after '-'),
    capitalizes it (e.g. 'beta' → 'Beta'), or returns 'Stable'.
    """
    match = re.match(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-([A-Za-z0-9\.]+))?$", version)
    if match and match.group(1):
        label = match.group(1).split(".")[0]
        return label.capitalize()
    return "Stable"


def determine_build_date() -> str:
    """
    Returns the modification date of the VERSION_FILE_PATH as 'YYYY-MM-DD'.
    Falls back to current UTC date if file is missing or unreadable.
    """
    try:
        mtime = VERSION_FILE_PATH.stat().st_mtime
        dt = datetime.fromtimestamp(mtime, timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        log.warning(f"Could not stat version file for build date: {e}")
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# read-once constants
VERSION = read_version_from_file()
VERSION_NAME = determine_channel(VERSION)
BUILD_DATE = determine_build_date()


def get_version_string() -> str:
    """Returns the short version string (e.g. 'v1.2.3 (Beta)')"""
    return f"v{VERSION} ({VERSION_NAME})"


def get_full_version_info() -> str:
    """Returns the full version info, including build date."""
    return f"CabPlanner {get_version_string()} (build: {BUILD_DATE})"
