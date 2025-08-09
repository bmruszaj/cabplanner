"""Essential integration tests for UpdaterService.

This file contains only high-level integration tests that are not covered
by the more focused component tests in other test files.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from src.services.updater_service import UpdaterService, get_current_version


class TestUpdaterServiceIntegration:
    """Essential integration tests for UpdaterService."""

    @pytest.fixture
    def mock_settings_service(self):
        """Create a mock settings service for testing."""
        mock_service = Mock()
        mock_service.get_setting_value.return_value = True
        return mock_service

    @pytest.fixture
    def updater_service(self):
        """Create UpdaterService instance for testing."""
        return UpdaterService()

    def test_get_current_version_success(self):
        """Test successful retrieval of current version."""
        with patch("src.version.VERSION", "1.2.3"):
            version = get_current_version()
            assert version == "1.2.3"


    def test_updater_service_initialization(self, updater_service):
        """Test UpdaterService initializes correctly."""
        assert updater_service.current_version is not None
        assert updater_service.thread_pool is not None
        assert updater_service.update_worker is None

    def test_signal_emission_structure(self, updater_service):
        """Test that UpdaterService has the expected signals."""
        # Verify all required signals exist
        assert hasattr(updater_service, "update_progress")
        assert hasattr(updater_service, "update_complete")
        assert hasattr(updater_service, "update_failed")
        assert hasattr(updater_service, "update_check_complete")
        assert hasattr(updater_service, "update_check_failed")

    def test_check_for_updates_starts_worker(self, updater_service):
        """Test that check_for_updates properly starts a worker thread."""
        with patch.object(updater_service.thread_pool, "start") as mock_start:
            updater_service.check_for_updates()
            mock_start.assert_called_once()

    def test_perform_update_starts_worker(self, updater_service):
        """Test that perform_update properly starts a worker thread."""
        with patch.object(updater_service.thread_pool, "start") as mock_start:
            updater_service.perform_update()
            mock_start.assert_called_once()
            assert updater_service.update_worker is not None

    def test_cancel_update_functionality(self, updater_service):
        """Test that cancel_update properly cancels running update."""
        # Start an update first
        updater_service.perform_update()
        assert updater_service.update_worker is not None

        # Cancel it
        updater_service.cancel_update()
        assert updater_service.update_worker is None

    @patch("src.services.updater_service.is_frozen")
    def test_create_shortcut_frozen_check(self, mock_is_frozen, updater_service):
        """Test shortcut creation checks frozen state."""
        # Test in development mode (not frozen)
        mock_is_frozen.return_value = False
        updater_service.create_shortcut_on_first_run()
        # Should return early without creating shortcut

        # Test in frozen mode
        mock_is_frozen.return_value = True
        with patch("src.services.updater_service.run_powershell") as mock_run_ps:
            with patch("src.services.updater_service.install_dir") as mock_install_dir:
                # Return a proper Path object instead of Mock
                test_dir = Path("C:/test/install")
                mock_install_dir.return_value = test_dir

                with patch.object(
                    Path, "exists", return_value=False
                ):  # Shortcut doesn't exist
                    updater_service.create_shortcut_on_first_run()
                    mock_run_ps.assert_called_once()
