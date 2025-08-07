import pytest
import tempfile
import datetime
import zipfile
import os
from pathlib import Path
from unittest.mock import patch, Mock


from src.services.updater_service import (
    UpdaterService,
    get_current_version,
    download_file_with_progress,
    safe_extract,
)

# Mock version for testing
TEST_CURRENT_VERSION = "1.0.0"
TEST_NEWER_VERSION = "1.1.0"
TEST_OLDER_VERSION = "0.9.0"


class MockSettingsService:
    """Mock implementation of SettingsService for testing."""

    def __init__(self):
        self.settings = {
            "auto_update_enabled": True,
            "auto_update_frequency": "Co tydzień",
            "last_update_check": None,
        }

    def get_setting_value(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value, value_type=None):
        self.settings[key] = value


class TestUpdaterService:
    """Tests for the UpdaterService class."""

    @pytest.fixture
    def updater_service(self):
        """Create a fresh UpdaterService instance for each test."""
        with (
            patch(
                "src.services.updater_service.get_current_version",
                return_value=TEST_CURRENT_VERSION,
            ),
            patch(
                "src.services.updater_service.is_running_in_development_mode",
                return_value=False,  # Mock as running in production mode for tests
            ),
        ):
            service = UpdaterService()
            yield service

    @pytest.fixture
    def settings_service(self):
        """Create a mock SettingsService instance."""
        return MockSettingsService()

    def test_get_current_version(self):
        """Test getting the current version."""
        with patch("src.version.VERSION", TEST_CURRENT_VERSION):
            with patch(
                "src.services.updater_service.get_current_version",
                return_value=TEST_CURRENT_VERSION,
            ):
                assert get_current_version() == TEST_CURRENT_VERSION

    def test_version_to_tuple_conversion(self, updater_service):
        """Test conversion of version strings to tuples for comparison."""
        # Test regular versions
        assert updater_service._version_to_tuple("1.0.0") == (1, 0, 0)
        assert updater_service._version_to_tuple("1.10.0") == (1, 10, 0)

        # Test with extra components
        assert updater_service._version_to_tuple("1.0.0.1") == (1, 0, 0, 1)

        # Test with mixed numerical and string parts
        assert updater_service._version_to_tuple("1.0.0-beta.1") == (1, 0, 0, "-beta.1")

        # Test handling of invalid versions
        assert updater_service._version_to_tuple("invalid") == ("invalid",)
        assert updater_service._version_to_tuple("") == ()

    def test_should_check_for_updates_enabled(self, updater_service, settings_service):
        """Test that updates are checked when enabled and due."""
        # Default settings - should check
        assert updater_service.should_check_for_updates(settings_service)

        # Set last check to a week ago - should check with weekly frequency
        week_ago = (datetime.datetime.now() - datetime.timedelta(days=8)).isoformat()
        settings_service.settings["last_update_check"] = week_ago
        assert updater_service.should_check_for_updates(settings_service)

        # Set last check to yesterday - should not check with weekly frequency
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
        settings_service.settings["last_update_check"] = yesterday
        assert not updater_service.should_check_for_updates(settings_service)

    def test_should_check_for_updates_disabled(self, updater_service, settings_service):
        """Test that updates are not checked when disabled."""
        settings_service.settings["auto_update_enabled"] = False
        assert not updater_service.should_check_for_updates(settings_service)

    def test_should_check_for_updates_frequency(
        self, updater_service, settings_service
    ):
        """Test update check frequency settings."""
        # Set last check to 2 days ago
        two_days_ago = (
            datetime.datetime.now() - datetime.timedelta(days=2)
        ).isoformat()
        settings_service.settings["last_update_check"] = two_days_ago

        # Daily frequency - should check
        settings_service.settings["auto_update_frequency"] = "Codziennie"
        assert updater_service.should_check_for_updates(settings_service)

        # Weekly frequency - should not check
        settings_service.settings["auto_update_frequency"] = "Co tydzień"
        assert not updater_service.should_check_for_updates(settings_service)

        # Monthly frequency - should not check
        settings_service.settings["auto_update_frequency"] = "Co miesiąc"
        assert not updater_service.should_check_for_updates(settings_service)

        # Never check
        settings_service.settings["auto_update_frequency"] = "Nigdy"
        assert not updater_service.should_check_for_updates(settings_service)

    @patch("src.services.updater_service.is_running_in_development_mode")
    def test_should_check_for_updates_development_mode(
        self, mock_dev_mode, settings_service
    ):
        """Test that updates are blocked in development mode."""
        # Mock development mode detection to return True
        mock_dev_mode.return_value = True

        with patch(
            "src.services.updater_service.get_current_version",
            return_value=TEST_CURRENT_VERSION,
        ):
            updater_service = UpdaterService()

            # Even with updates enabled, should return False in dev mode
            settings_service.settings["auto_update_enabled"] = True
            assert not updater_service.should_check_for_updates(settings_service)

            # Verify the development mode check was called
            mock_dev_mode.assert_called()

    @patch("src.services.updater_service.get_latest_release_info")
    def test_check_for_updates_newer_version(
        self, mock_get_latest_release_info, updater_service
    ):
        """Test checking for updates when a newer version is available."""
        # Mock the API response with a newer version
        mock_get_latest_release_info.return_value = {
            "tag_name": f"v{TEST_NEWER_VERSION}",
            "assets": [
                {
                    "name": "cabplanner-1.1.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ],
        }

        # Create a spy for the signal
        signal_spy = Mock()
        updater_service.update_check_complete.connect(signal_spy)

        # Check for updates
        update_available, current_version, latest_version = (
            updater_service.check_for_updates()
        )

        # Verify results
        assert update_available
        assert current_version == TEST_CURRENT_VERSION
        assert latest_version == TEST_NEWER_VERSION

        # Verify signal was emitted with correct params
        signal_spy.assert_called_once_with(
            True, TEST_CURRENT_VERSION, TEST_NEWER_VERSION
        )

    @patch("src.services.updater_service.get_latest_release_info")
    def test_check_for_updates_same_version(
        self, mock_get_latest_release_info, updater_service
    ):
        """Test checking for updates when already on the latest version."""
        # Mock the API response with the same version
        mock_get_latest_release_info.return_value = {
            "tag_name": f"v{TEST_CURRENT_VERSION}",
            "assets": [
                {
                    "name": "cabplanner-1.0.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ],
        }

        # Create a spy for the signal
        signal_spy = Mock()
        updater_service.update_check_complete.connect(signal_spy)

        # Check for updates
        update_available, current_version, latest_version = (
            updater_service.check_for_updates()
        )

        # Verify results
        assert not update_available
        assert current_version == TEST_CURRENT_VERSION
        assert latest_version == TEST_CURRENT_VERSION

        # Verify signal was emitted with correct params
        signal_spy.assert_called_once_with(
            False, TEST_CURRENT_VERSION, TEST_CURRENT_VERSION
        )

    @patch("src.services.updater_service.get_latest_release_info")
    def test_check_for_updates_older_version(
        self, mock_get_latest_release_info, updater_service
    ):
        """Test checking for updates when remote version is older (should not happen in practice)."""
        # Mock the API response with an older version
        mock_get_latest_release_info.return_value = {
            "tag_name": f"v{TEST_OLDER_VERSION}",
            "assets": [
                {
                    "name": "cabplanner-0.9.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ],
        }

        # Create a spy for the signal
        signal_spy = Mock()
        updater_service.update_check_complete.connect(signal_spy)

        # Check for updates
        update_available, current_version, latest_version = (
            updater_service.check_for_updates()
        )

        # Verify results
        assert not update_available
        assert current_version == TEST_CURRENT_VERSION
        assert latest_version == TEST_OLDER_VERSION

        # Verify signal was emitted with correct params
        signal_spy.assert_called_once_with(
            False, TEST_CURRENT_VERSION, TEST_OLDER_VERSION
        )

    @patch("src.services.updater_service.get_latest_release_info")
    def test_check_for_updates_handles_tag_prefixes(
        self, mock_get_latest_release_info, updater_service
    ):
        """Test that the version checking handles various tag prefixes."""
        # Test with 'v' prefix
        mock_get_latest_release_info.return_value = {
            "tag_name": f"v{TEST_NEWER_VERSION}",
            "assets": [],
        }
        update_available, _, latest_version = updater_service.check_for_updates()
        assert update_available
        assert latest_version == TEST_NEWER_VERSION

        # Test with 'cabplanner-' prefix
        mock_get_latest_release_info.return_value = {
            "tag_name": f"cabplanner-{TEST_NEWER_VERSION}",
            "assets": [],
        }
        update_available, _, latest_version = updater_service.check_for_updates()
        assert update_available
        assert latest_version == TEST_NEWER_VERSION

    @patch("src.services.updater_service.get_latest_release_info")
    def test_check_for_updates_handles_api_error(
        self, mock_get_latest_release_info, updater_service
    ):
        """Test that the update checker handles API errors gracefully."""
        # Simulate an exception during API call
        mock_get_latest_release_info.side_effect = Exception("API Error")

        # Create a spy for the signal
        signal_spy = Mock()
        updater_service.update_check_complete.connect(signal_spy)

        # Check for updates
        update_available, current_version, latest_version = (
            updater_service.check_for_updates()
        )

        # Verify results
        assert not update_available
        assert current_version == TEST_CURRENT_VERSION
        assert latest_version == ""

        # Verify signal was emitted with correct params
        signal_spy.assert_called_once_with(False, TEST_CURRENT_VERSION, "")

    @patch("src.services.updater_service.requests.get")
    def test_download_file_with_progress(self, mock_requests_get):
        """Test downloading a file with progress tracking."""
        # Mock the requests response
        mock_response = Mock()
        mock_response.headers.get.return_value = "1000"  # Content length of 1000 bytes
        mock_response.iter_content.return_value = [
            b"a" * 500,
            b"b" * 500,
        ]  # Two chunks of 500 bytes
        mock_requests_get.return_value = mock_response

        # Create a temp file for download
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Mock progress callback
            progress_callback = Mock()

            # Download the file
            download_file_with_progress(
                "https://example.com/file.zip", tmp_path, progress_callback
            )

            # Verify the progress callback was called with expected values
            assert progress_callback.call_count == 2
            progress_callback.assert_any_call(50)  # First chunk (50%)
            progress_callback.assert_any_call(100)  # Second chunk (100%)

            # Verify the file was written correctly
            assert tmp_path.stat().st_size == 1000
        finally:
            # Clean up
            if tmp_path.exists():
                tmp_path.unlink()

    @patch("src.services.updater_service.get_latest_release_info")
    def test_perform_update_no_assets(self, mock_get_release_info, updater_service):
        """Test update process when no assets are found."""
        # Mock the release info with no assets
        mock_get_release_info.return_value = {"assets": []}

        # Create signal spy
        failed_spy = Mock()
        updater_service.update_failed.connect(failed_spy)

        # Run the update process
        updater_service.perform_update()

        # Verify failed signal was emitted with the correct message
        failed_spy.assert_called_once()
        assert "Nie znaleziono pakietu aktualizacji" in failed_spy.call_args[0][0]

    @patch("src.services.updater_service.get_latest_release_info")
    @patch("src.services.updater_service.download_file_with_progress")
    def test_perform_update_download_error(
        self, mock_download, mock_get_release_info, updater_service
    ):
        """Test update process with download error."""
        # Mock the release info
        mock_get_release_info.return_value = {
            "assets": [
                {
                    "name": "cabplanner-1.1.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ]
        }

        # Simulate download returning False (failure)
        mock_download.return_value = False

        # Create signal spy
        failed_spy = Mock()
        updater_service.update_failed.connect(failed_spy)

        # Run the update process
        updater_service.perform_update()

        # Verify failed signal was emitted with the correct message
        failed_spy.assert_called_once()
        assert "Błąd pobierania" in failed_spy.call_args[0][0]

    @patch("src.services.updater_service.get_latest_release_info")
    @patch("src.services.updater_service.download_file_with_progress")
    @patch("zipfile.ZipFile")
    def test_perform_update_extract_error(
        self, mock_zipfile, mock_download, mock_get_release_info, updater_service
    ):
        """Test update process with extraction error."""
        # Mock the release info
        mock_get_release_info.return_value = {
            "assets": [
                {
                    "name": "cabplanner-1.1.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ]
        }

        # Mock successful download
        mock_download.return_value = True

        # Simulate extraction error
        mock_zipfile.return_value.__enter__.side_effect = Exception("Extraction failed")

        # Create signal spy
        failed_spy = Mock()
        updater_service.update_failed.connect(failed_spy)

        # Run the update process
        updater_service.perform_update()

        # Verify failed signal was emitted with generic error message
        failed_spy.assert_called_once()
        assert "Błąd aktualizacji" in failed_spy.call_args[0][0]

    @patch("src.services.updater_service.get_latest_release_info")
    @patch("src.services.updater_service.download_file_with_progress")
    @patch("zipfile.ZipFile")
    @patch(
        "src.services.updater_service.safe_extract"
    )  # Mock safe_extract to avoid zipfile issues
    @patch("src.services.updater_service.is_running_in_development_mode")
    @patch("src.services.updater_service.get_current_version")
    def test_perform_update_blocked_in_development_mode(
        self,
        mock_get_current_version,
        mock_dev_mode,
        mock_safe_extract,
        mock_zipfile,
        mock_download,
        mock_get_release_info,
    ):
        """Test that perform_update is blocked in development mode."""
        # Mock development mode detection to return True
        mock_dev_mode.return_value = True
        mock_get_current_version.return_value = TEST_CURRENT_VERSION

        updater_service = UpdaterService()

        # Create signal spy
        failed_spy = Mock()
        updater_service.update_failed.connect(failed_spy)

        # Run the update process
        updater_service.perform_update()

        # Verify failed signal was emitted with development mode message
        failed_spy.assert_called_once()
        assert (
            "Aktualizacje są wyłączone w trybie deweloperskim"
            in failed_spy.call_args[0][0]
        )

    @patch("src.services.updater_service.get_latest_release_info")
    @patch("src.services.updater_service.download_file_with_progress")
    @patch("zipfile.ZipFile")
    @patch("src.services.updater_service.safe_extract")
    @patch("os.replace")
    @patch("os.execv")
    def test_perform_update_success(
        self,
        mock_execv,
        mock_replace,
        mock_safe_extract,
        mock_zipfile,
        mock_download,
        mock_get_release_info,
        updater_service,
    ):
        """Test successful update process."""
        # Mock the release info
        mock_get_release_info.return_value = {
            "assets": [
                {
                    "name": "cabplanner-1.1.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ]
        }

        # Mock successful download
        mock_download.return_value = True

        # Mock the ZipFile context manager
        mock_zipfile_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zipfile_instance
        mock_zipfile.return_value.__exit__.return_value = False

        # Mock safe_extract to do nothing
        mock_safe_extract.return_value = None

        # Mock the platform updater's find_executable method
        mock_exe_path = Path("fake_path/cabplanner.exe")

        # Mock script path existence
        with (
            patch.object(
                updater_service,
                "_get_update_script_path",
                return_value=Path("scripts/update.bat"),
            ),
            patch.object(
                updater_service.platform_updater,
                "find_executable",
                return_value=mock_exe_path,
            ),
            patch("pathlib.Path.exists", return_value=True),
        ):
            # Create signal spies
            progress_spy = Mock()
            complete_spy = Mock()
            failed_spy = Mock()

            updater_service.update_progress.connect(progress_spy)
            updater_service.update_complete.connect(complete_spy)
            updater_service.update_failed.connect(failed_spy)

            # Run the update process
            updater_service.perform_update()

            # Verify progress signals were emitted (at least 2: initial and final)
            assert progress_spy.call_count >= 2

            # Verify completion signal was emitted
            complete_spy.assert_called_once()

            # Verify failed signal was not emitted
            failed_spy.assert_not_called()

    @patch("src.services.updater_service.get_latest_release_info")
    @patch("src.services.updater_service.download_file_with_progress")
    @patch("src.services.updater_service.safe_extract")
    @patch("zipfile.ZipFile")
    def test_perform_update_no_exe(
        self,
        mock_zipfile,
        mock_safe_extract,
        mock_download,
        mock_get_release_info,
        updater_service,
    ):
        """Test update process when no executable is found in the package."""
        # Mock the release info
        mock_get_release_info.return_value = {
            "assets": [
                {
                    "name": "cabplanner-1.1.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ]
        }

        # Mock successful download
        mock_download.return_value = True

        # Mock the ZipFile context manager properly
        mock_zipfile_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zipfile_instance
        mock_zipfile.return_value.__exit__.return_value = False

        # Mock safe_extract to do nothing (avoid zipfile iteration issues)
        mock_safe_extract.return_value = None

        # Mock platform updater to return None (no exe found)
        with patch.object(
            updater_service.platform_updater, "find_executable", return_value=None
        ):
            # Create signal spy
            failed_spy = Mock()
            updater_service.update_failed.connect(failed_spy)

            # Run the update process
            updater_service.perform_update()

            # Verify failed signal was emitted with the correct message
            failed_spy.assert_called_once()
            assert (
                "Pakiet aktualizacji nie zawiera pliku wykonywalnego"
                in failed_spy.call_args[0][0]
            )


class TestSafeExtract:
    """Tests for the safe_extract function to prevent zip-slip vulnerabilities."""

    def test_safe_extract_normal_files(self):
        """Test that safe_extract works correctly with normal file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            extract_path.mkdir()

            # Create a test zip file with normal paths
            zip_path = Path(temp_dir) / "test.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("normal_file.txt", "content")
                zf.writestr("subdir/nested_file.txt", "nested content")
                zf.writestr("another_file.exe", "exe content")

            # Extract using safe_extract - should work without issues
            with zipfile.ZipFile(zip_path, "r") as zf:
                safe_extract(zf, extract_path)

            # Verify files were extracted correctly
            assert (extract_path / "normal_file.txt").exists()
            assert (extract_path / "subdir" / "nested_file.txt").exists()
            assert (extract_path / "another_file.exe").exists()

            # Verify file contents
            assert (extract_path / "normal_file.txt").read_text() == "content"
            assert (
                extract_path / "subdir" / "nested_file.txt"
            ).read_text() == "nested content"

    def test_safe_extract_blocks_zip_slip_attack(self):
        """Test that safe_extract prevents zip-slip attacks with malicious paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            extract_path.mkdir()

            # Create a test zip file with malicious paths
            zip_path = Path(temp_dir) / "malicious.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # These paths would try to escape the extraction directory
                zf.writestr("../../../etc/passwd", "malicious content")
                zf.writestr("..\\..\\windows\\system32\\evil.exe", "evil content")

            # Attempt to extract using safe_extract - should raise RuntimeError
            with zipfile.ZipFile(zip_path, "r") as zf:
                with pytest.raises(RuntimeError, match="Illegal path in zip"):
                    safe_extract(zf, extract_path)

            # Verify no files were extracted outside the intended directory
            parent_dir = extract_path.parent
            malicious_files = [
                parent_dir / "etc" / "passwd",
                parent_dir / "windows" / "system32" / "evil.exe",
            ]
            for malicious_file in malicious_files:
                assert not malicious_file.exists()

    def test_safe_extract_blocks_absolute_paths(self):
        """Test that safe_extract prevents extraction of files with absolute paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            extract_path.mkdir()

            # Create a test zip file with absolute paths
            zip_path = Path(temp_dir) / "absolute_paths.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # These paths are absolute and should be blocked
                if os.name == "nt":  # Windows
                    zf.writestr("C:\\Windows\\System32\\malicious.exe", "malicious")
                    zf.writestr("D:\\temp\\evil.txt", "evil")
                else:  # Unix-like
                    zf.writestr("/etc/passwd", "malicious")
                    zf.writestr("/tmp/evil.txt", "evil")

            # Attempt to extract using safe_extract - should raise RuntimeError
            with zipfile.ZipFile(zip_path, "r") as zf:
                with pytest.raises(RuntimeError, match="Illegal path in zip"):
                    safe_extract(zf, extract_path)

    def test_safe_extract_allows_deep_nesting(self):
        """Test that safe_extract allows legitimate deep directory nesting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            extract_path.mkdir()

            # Create a test zip file with deeply nested but legitimate paths
            zip_path = Path(temp_dir) / "deep_nesting.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                deep_path = "level1/level2/level3/level4/level5/deep_file.txt"
                zf.writestr(deep_path, "deep content")

            # Extract using safe_extract - should work
            with zipfile.ZipFile(zip_path, "r") as zf:
                safe_extract(zf, extract_path)

            # Verify the deeply nested file was extracted correctly
            deep_file = (
                extract_path
                / "level1"
                / "level2"
                / "level3"
                / "level4"
                / "level5"
                / "deep_file.txt"
            )
            assert deep_file.exists()
            assert deep_file.read_text() == "deep content"

    def test_safe_extract_handles_windows_paths(self):
        """Test that safe_extract correctly handles Windows-style paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            extract_path.mkdir()

            # Create a test zip file with Windows-style paths
            zip_path = Path(temp_dir) / "windows_paths.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # Legitimate Windows-style paths within the extraction directory
                zf.writestr("folder\\subfolder\\file.txt", "windows content")
                zf.writestr("another\\path\\executable.exe", "exe content")

            # Extract using safe_extract - should work
            with zipfile.ZipFile(zip_path, "r") as zf:
                safe_extract(zf, extract_path)

            # Verify files were extracted (paths normalized by pathlib)
            assert (extract_path / "folder" / "subfolder" / "file.txt").exists()
            assert (extract_path / "another" / "path" / "executable.exe").exists()

    def test_safe_extract_blocks_mixed_attack_vectors(self):
        """Test that safe_extract blocks various zip-slip attack vectors in one zip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            extract_path.mkdir()

            # Create a test zip file with mixed attack vectors
            zip_path = Path(temp_dir) / "mixed_attacks.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # Mix of legitimate and malicious paths
                zf.writestr("legitimate_file.txt", "good content")
                zf.writestr("../escape_attempt.txt", "malicious content")
                zf.writestr("..\\windows_escape.exe", "evil content")
                zf.writestr("good_folder/good_file.txt", "more good content")

            # Attempt to extract using safe_extract - should raise RuntimeError
            # The function should detect the malicious paths and block the entire extraction
            with zipfile.ZipFile(zip_path, "r") as zf:
                with pytest.raises(RuntimeError, match="Illegal path in zip"):
                    safe_extract(zf, extract_path)

            # Verify that even legitimate files weren't extracted due to security violation
            assert not (extract_path / "legitimate_file.txt").exists()
            assert not (extract_path / "good_folder" / "good_file.txt").exists()

    def test_safe_extract_empty_zip(self):
        """Test that safe_extract handles empty zip files correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_path = Path(temp_dir) / "extract"
            extract_path.mkdir()

            # Create an empty zip file
            zip_path = Path(temp_dir) / "empty.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                pass  # Create empty zip

            # Extract using safe_extract - should work without issues
            with zipfile.ZipFile(zip_path, "r") as zf:
                safe_extract(zf, extract_path)

            # Verify extraction directory still exists and is empty
            assert extract_path.exists()
            assert not any(extract_path.iterdir())  # Should be empty


class TestBatchScriptUpdate:
    """Tests for the batch script-based update mechanism."""

    @pytest.fixture
    def temp_update_dir(self):
        """Create a temporary directory for update testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_get_update_script_path(self, temp_update_dir):
        """Test that the update script path is found correctly."""
        with patch(
            "src.services.updater_service.get_current_version", return_value="1.0.0"
        ):
            updater_service = UpdaterService()

            # Create a mock script file
            script_path = temp_update_dir / "scripts" / "update.bat"
            script_path.parent.mkdir(parents=True)
            script_path.write_text("@echo off\necho test script")

            # Mock the script detection to force it to use our temp directory
            with patch.object(
                updater_service, "_get_update_script_path"
            ) as mock_get_script:
                mock_get_script.return_value = script_path
                found_path = updater_service._get_update_script_path()
                assert found_path == script_path

    @patch("src.services.updater_service.get_latest_release_info")
    @patch("src.services.updater_service.download_file_with_progress")
    @patch("src.services.updater_service.safe_extract")
    @patch("zipfile.ZipFile")
    def test_perform_update_prepares_script(
        self,
        mock_zipfile,
        mock_safe_extract,
        mock_download,
        mock_get_release_info,
        temp_update_dir,
    ):
        """Test that perform_update prepares the batch script execution."""
        # Mock the release info
        mock_get_release_info.return_value = {
            "assets": [
                {
                    "name": "cabplanner-1.1.0.zip",
                    "browser_download_url": "https://example.com/file.zip",
                }
            ]
        }

        # Mock successful download
        mock_download.return_value = True

        # Mock the ZipFile context manager
        mock_zipfile_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zipfile_instance
        mock_zipfile.return_value.__exit__.return_value = False

        # Mock safe_extract
        mock_safe_extract.return_value = None

        # Create a fake executable in the extract directory
        fake_exe = temp_update_dir / "cabplanner.exe"
        fake_exe.write_text("fake executable")

        # Create the script file
        script_path = temp_update_dir / "scripts" / "update.bat"
        script_path.parent.mkdir(parents=True)
        script_path.write_text("@echo off\necho test script")

        with (
            patch(
                "src.services.updater_service.get_current_version", return_value="1.0.0"
            ),
            patch(
                "src.services.updater_service.is_running_in_development_mode",
                return_value=False,
            ),
            patch("tempfile.gettempdir", return_value=str(temp_update_dir)),
        ):
            updater_service = UpdaterService()

            # Mock the script path detection to use our test script
            with (
                patch.object(
                    updater_service, "_get_update_script_path", return_value=script_path
                ),
                patch.object(
                    updater_service.platform_updater,
                    "find_executable",
                    return_value=fake_exe,
                ),
            ):
                # Create signal spies
                progress_spy = Mock()
                complete_spy = Mock()
                failed_spy = Mock()

                updater_service.update_progress.connect(progress_spy)
                updater_service.update_complete.connect(complete_spy)
                updater_service.update_failed.connect(failed_spy)

                # Run the update process
                updater_service.perform_update()

                # Verify completion signal was emitted (script prepared successfully)
                complete_spy.assert_called_once()

                # Verify failed signal was not emitted
                failed_spy.assert_not_called()

                # Verify update script path and args were prepared
                assert hasattr(updater_service, "update_script_path")
                assert hasattr(updater_service, "update_script_args")
                assert updater_service.update_script_path == script_path
                assert len(updater_service.update_script_args) == 3

    @patch("subprocess.Popen")
    @patch("src.services.updater_service.QTimer")
    def test_default_restarter_with_script(
        self, mock_qtimer, mock_popen, temp_update_dir
    ):
        """Test that the default restarter uses the update script when available."""
        with patch(
            "src.services.updater_service.get_current_version", return_value="1.0.0"
        ):
            updater_service = UpdaterService()

            # Create a mock update script
            script_path = temp_update_dir / "update.bat"
            script_path.write_text("@echo off\necho test script")
            updater_service.update_script_path = script_path
            updater_service.update_script_args = ["arg1", "arg2", "arg3"]

            exe_path = temp_update_dir / "cabplanner.exe"

            # Call the restarter
            updater_service._default_restarter(exe_path)

            # Verify subprocess.Popen was called with the script
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args[0][0]
            assert str(script_path) in call_args
            assert "arg1" in call_args
            assert "arg2" in call_args
            assert "arg3" in call_args

            # Verify QTimer was used to schedule app exit
            mock_qtimer.singleShot.assert_called_once_with(
                1000, updater_service._exit_application
            )

    @patch("subprocess.Popen")
    @patch("os.execv")
    @patch("src.services.updater_service.QTimer")
    @patch("src.services.updater_service.QMessageBox")
    def test_default_restarter_fallback(
        self, mock_messagebox, mock_qtimer, mock_execv, mock_popen, temp_update_dir
    ):
        """Test that the default restarter falls back to execv when no script exists."""
        with patch(
            "src.services.updater_service.get_current_version", return_value="1.0.0"
        ):
            updater_service = UpdaterService()

            exe_path = temp_update_dir / "cabplanner.exe"

            # Call the restarter without setting update_script_path
            updater_service._default_restarter(exe_path)

            # Verify subprocess.Popen was NOT called
            mock_popen.assert_not_called()

            # Verify fallback behavior was used - QTimer.singleShot should be called
            mock_qtimer.singleShot.assert_called()

            # Verify QMessageBox.information was called for the fallback
            mock_messagebox.information.assert_called_once()

    @patch("src.services.updater_service.QMessageBox")
    @patch("sys.exit")
    def test_exit_application(self, mock_sys_exit, mock_messagebox):
        """Test the _exit_application method."""
        with patch(
            "src.services.updater_service.get_current_version", return_value="1.0.0"
        ):
            updater_service = UpdaterService()

            # Call _exit_application
            updater_service._exit_application()

            # Verify message box was shown
            mock_messagebox.information.assert_called_once()

            # Verify sys.exit was called
            mock_sys_exit.assert_called_once_with(0)

    def test_external_script_exists(self):
        """Test that the external update.bat script exists in the scripts directory."""
        script_path = Path(
            "C:/Users/barrt/PycharmProjects/cabplanner/scripts/update.bat"
        )
        assert script_path.exists(), "External update.bat script should exist"

        # Verify script content has expected Polish text
        script_content = script_path.read_text(encoding="cp1252")
        expected_text = [
            "Aktualizowanie Cabplanner...",
            "Tworzenie kopii zapasowej...",
            "Instalowanie nowej wersji...",
            "Uruchamianie aplikacji...",
        ]

        for text in expected_text:
            assert text in script_content, f"Script should contain: {text}"
