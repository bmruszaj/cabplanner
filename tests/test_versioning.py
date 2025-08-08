"""Unit tests for versioning module."""

import pytest
from packaging.version import InvalidVersion

from src.app.update.versioning import parse_version, is_newer_version


class TestVersioning:
    """Test version parsing and comparison functionality."""

    def test_parse_version_valid_versions(self):
        """Test parsing of valid version strings."""
        # Basic semantic versions
        assert str(parse_version("1.0.0")) == "1.0.0"
        assert str(parse_version("2.1.3")) == "2.1.3"
        assert str(parse_version("10.20.30")) == "10.20.30"

        # Versions with pre-release tags
        assert str(parse_version("1.0.0-alpha")) == "1.0.0a0"
        assert str(parse_version("1.0.0-beta.1")) == "1.0.0b1"
        assert str(parse_version("2.0.0-rc.1")) == "2.0.0rc1"

    def test_parse_version_with_prefixes(self):
        """Test parsing versions with common prefixes."""
        # v prefix
        assert str(parse_version("v1.2.3")) == "1.2.3"
        assert str(parse_version("v2.0.0-beta")) == "2.0.0b0"

        # cabplanner- prefix
        assert str(parse_version("cabplanner-1.0.0")) == "1.0.0"
        assert str(parse_version("cabplanner-2.1.0")) == "2.1.0"

        # Combined prefixes - should strip both v and cabplanner-
        assert str(parse_version("vcabplanner-1.0.0")) == "1.0.0"

    def test_parse_version_whitespace(self):
        """Test parsing versions with whitespace."""
        assert str(parse_version("  1.0.0  ")) == "1.0.0"
        assert str(parse_version("\t2.1.0\n")) == "2.1.0"

    def test_parse_version_invalid(self):
        """Test parsing of invalid version strings."""
        with pytest.raises(InvalidVersion):
            parse_version("")

        with pytest.raises(InvalidVersion):
            parse_version("not.a.version")

        # Note: "1.2.3.4.5.6" might actually be valid in packaging.version
        # Let's test with something that's definitely invalid
        with pytest.raises(InvalidVersion):
            parse_version("completely-invalid-version-string")

    def test_is_newer_version_basic(self):
        """Test basic version comparison."""
        # Newer versions
        assert is_newer_version("1.0.0", "1.0.1") is True
        assert is_newer_version("1.0.0", "1.1.0") is True
        assert is_newer_version("1.0.0", "2.0.0") is True

        # Same versions
        assert is_newer_version("1.0.0", "1.0.0") is False

        # Older versions
        assert is_newer_version("1.1.0", "1.0.0") is False
        assert is_newer_version("2.0.0", "1.9.9") is False

    def test_is_newer_version_with_prefixes(self):
        """Test version comparison with prefixes."""
        assert is_newer_version("v1.0.0", "v1.0.1") is True
        assert is_newer_version("cabplanner-1.0.0", "cabplanner-1.1.0") is True
        assert is_newer_version("v1.0.0", "cabplanner-1.0.1") is True

    def test_is_newer_version_prerelease(self):
        """Test version comparison with pre-release versions."""
        # Stable vs pre-release
        assert is_newer_version("1.0.0-alpha", "1.0.0") is True
        assert is_newer_version("1.0.0-beta", "1.0.0") is True
        assert is_newer_version("1.0.0", "1.0.1-alpha") is True

        # Pre-release ordering
        assert is_newer_version("1.0.0-alpha", "1.0.0-beta") is True
        assert is_newer_version("1.0.0-beta", "1.0.0-rc") is True

    def test_is_newer_version_invalid_input(self):
        """Test version comparison with invalid input."""
        # Invalid versions should return False
        assert is_newer_version("invalid", "1.0.0") is False
        assert is_newer_version("1.0.0", "invalid") is False
        assert is_newer_version("invalid", "invalid") is False
