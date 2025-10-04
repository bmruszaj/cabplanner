"""
Test for the Settings Dialog validation logic (without GUI).
"""

import re


class TestSettingsValidation:
    """Test settings validation logic without creating GUI components."""

    def test_email_validation(self):
        """Test email validation logic."""
        # Valid emails
        assert self._is_valid_email("test@example.com")
        assert self._is_valid_email("user.name+tag@domain.co.uk")
        assert self._is_valid_email("123@test.org")

        # Invalid emails
        assert not self._is_valid_email("invalid-email")
        assert not self._is_valid_email("@domain.com")
        assert not self._is_valid_email("user@")
        assert not self._is_valid_email("")
        assert not self._is_valid_email("user@domain")
        assert not self._is_valid_email("user space@domain.com")

    def test_phone_validation(self):
        """Test phone validation logic."""
        # Valid phones
        assert self._is_valid_phone("123-456-7890")
        assert self._is_valid_phone("+1 234 567 8900")
        assert self._is_valid_phone("(123) 456-7890")
        assert self._is_valid_phone("1234567890")
        assert self._is_valid_phone("+48123456789")

        # Invalid phones
        assert not self._is_valid_phone("123")  # Too short
        assert not self._is_valid_phone("abc-def-ghij")  # Letters
        assert not self._is_valid_phone("123-456-78901234567890")  # Too long
        assert not self._is_valid_phone("")
        assert not self._is_valid_phone("++123456789")  # Double plus

    def _is_valid_email(self, email):
        """Email validation logic extracted from settings dialog."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _is_valid_phone(self, phone):
        """Phone validation logic extracted from settings dialog."""
        # Remove common separators and check if remaining are digits (with optional + at start)
        cleaned = re.sub(r"[\s\-\(\)]+", "", phone)
        pattern = r"^\+?[0-9]{7,15}$"
        return re.match(pattern, cleaned) is not None
