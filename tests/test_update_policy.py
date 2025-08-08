"""Unit tests for update frequency policy logic."""

from datetime import datetime, timezone, timedelta

from src.services.updater_service import LABEL_TO_FREQ, UpdateFrequency


class TestUpdateFrequencyPolicy:
    """Test update frequency policy and label mapping."""

    def test_label_to_freq_mapping(self):
        """Test that all Polish labels map to correct frequency enums."""
        expected_mappings = {
            "Przy uruchomieniu": UpdateFrequency.ON_LAUNCH,
            "Codziennie": UpdateFrequency.DAILY,
            "Co tydzień": UpdateFrequency.WEEKLY,
            "Co miesiąc": UpdateFrequency.MONTHLY,
            "Nigdy": UpdateFrequency.NEVER,
        }

        assert LABEL_TO_FREQ == expected_mappings

    def test_label_to_freq_completeness(self):
        """Test that all frequency enums have corresponding labels."""
        expected_frequencies = {
            UpdateFrequency.ON_LAUNCH,
            UpdateFrequency.DAILY,
            UpdateFrequency.WEEKLY,
            UpdateFrequency.MONTHLY,
            UpdateFrequency.NEVER,
        }

        mapped_frequencies = set(LABEL_TO_FREQ.values())
        assert mapped_frequencies == expected_frequencies

    def test_should_check_frequency_logic(self):
        """Test the frequency logic for determining when to check updates."""
        from src.services.updater_service import UpdaterService
        from unittest.mock import Mock

        # Create mock settings service
        settings_service = Mock()
        updater = UpdaterService()

        # Test disabled updates
        settings_service.get_setting_value.side_effect = lambda key, default: {
            "auto_update_enabled": False
        }.get(key, default)

        assert updater.should_check_for_updates(settings_service) is False

        # Test ON_LAUNCH frequency
        settings_service.get_setting_value.side_effect = lambda key, default: {
            "auto_update_enabled": True,
            "auto_update_frequency": "Przy uruchomieniu",
            "last_update_check": "",
        }.get(key, default)

        assert updater.should_check_for_updates(settings_service) is True

    def test_frequency_time_calculations(self):
        """Test time-based frequency calculations."""
        from src.services.updater_service import UpdaterService
        from unittest.mock import Mock

        updater = UpdaterService()
        settings_service = Mock()

        # Set up base settings
        now = datetime.now(timezone.utc)

        # Test DAILY frequency
        yesterday = now - timedelta(days=1, hours=1)
        settings_service.get_setting_value.side_effect = lambda key, default: {
            "auto_update_enabled": True,
            "auto_update_frequency": "Codziennie",
            "last_update_check": yesterday.isoformat(),
        }.get(key, default)

        assert updater.should_check_for_updates(settings_service) is True

        # Test WEEKLY frequency - recent check
        two_days_ago = now - timedelta(days=2)
        settings_service.get_setting_value.side_effect = lambda key, default: {
            "auto_update_enabled": True,
            "auto_update_frequency": "Co tydzień",
            "last_update_check": two_days_ago.isoformat(),
        }.get(key, default)

        assert updater.should_check_for_updates(settings_service) is False

        # Test WEEKLY frequency - old check
        eight_days_ago = now - timedelta(days=8)
        settings_service.get_setting_value.side_effect = lambda key, default: {
            "auto_update_enabled": True,
            "auto_update_frequency": "Co tydzień",
            "last_update_check": eight_days_ago.isoformat(),
        }.get(key, default)

        assert updater.should_check_for_updates(settings_service) is True

    def test_invalid_frequency_handling(self):
        """Test handling of invalid frequency labels."""
        from src.services.updater_service import UpdaterService
        from unittest.mock import Mock

        updater = UpdaterService()
        settings_service = Mock()

        # Test unknown frequency label - should default to WEEKLY
        settings_service.get_setting_value.side_effect = lambda key, default: {
            "auto_update_enabled": True,
            "auto_update_frequency": "Unknown Frequency",
            "last_update_check": "",
        }.get(key, default)

        # Should return True for first check regardless of frequency
        assert updater.should_check_for_updates(settings_service) is True
