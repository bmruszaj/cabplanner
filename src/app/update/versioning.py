"""Version parsing and comparison utilities."""

import logging
from packaging.version import Version, InvalidVersion

logger = logging.getLogger(__name__)


def parse_version(version_str: str) -> Version:
    """
    Parse a version string into a Version object for proper comparison.

    Args:
        version_str: Version string to parse (e.g., "1.2.3", "v1.2.3", "cabplanner-1.2.3")

    Returns:
        Version object for comparison

    Raises:
        InvalidVersion: If the version string cannot be parsed
    """
    if not version_str:
        raise InvalidVersion("Empty version string")

    # Clean up common prefixes and suffixes
    cleaned = version_str.strip()
    if cleaned.startswith("v"):
        cleaned = cleaned[1:]
    if cleaned.startswith("cabplanner-"):
        cleaned = cleaned[11:]

    try:
        return Version(cleaned)
    except InvalidVersion:
        logger.warning("Could not parse version: %s", version_str)
        raise


def is_newer_version(current: str, latest: str) -> bool:
    """
    Check if the latest version is newer than the current version.

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        True if latest is newer than current
    """
    try:
        current_version = parse_version(current)
        latest_version = parse_version(latest)
        return latest_version > current_version
    except InvalidVersion as e:
        logger.error("Version comparison failed: %s", e)
        return False
