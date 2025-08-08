"""Unit tests for downloader with mocked network operations."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from src.app.update.downloader import download, DownloadCancelled


class TestDownloader:
    """Test download functionality with mocked network operations."""

    def test_download_success_with_progress(self):
        """Test successful download with progress reporting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"
            progress_callback = Mock()

            # Mock response with chunks
            mock_response = Mock()
            mock_response.headers = {"content-length": "1000"}
            mock_response.iter_content.return_value = [
                b"x" * 100,  # First chunk: 10% progress
                b"x" * 200,  # Second chunk: 30% progress
                b"x" * 300,  # Third chunk: 60% progress
                b"x" * 400,  # Fourth chunk: 100% progress
            ]

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                # Should complete without raising
                download(
                    "https://example.com/file.zip",
                    dest_path,
                    progress_callback=progress_callback,
                )

            # Verify file was created
            assert dest_path.exists()
            assert dest_path.stat().st_size == 1000

            # Verify progress was reported
            assert progress_callback.call_count >= 2  # At least some progress updates

            # Check that progress values are reasonable (0-100)
            for call in progress_callback.call_args_list:
                progress_value = call[0][0]
                assert 0 <= progress_value <= 100

    def test_download_no_content_length(self):
        """Test download when Content-Length header is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"
            progress_callback = Mock()

            # Mock response without content-length
            mock_response = Mock()
            mock_response.headers = {}  # No content-length
            mock_response.iter_content.return_value = [b"x" * 500, b"x" * 500]

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                download(
                    "https://example.com/file.zip",
                    dest_path,
                    progress_callback=progress_callback,
                )

            # Should still complete successfully
            assert dest_path.exists()
            # Progress callback might not be called without content-length
            # but the download should still work

    def test_download_cancellation(self):
        """Test download cancellation functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"

            # Create a cancellation flag
            cancelled = False

            def is_cancelled():
                return cancelled

            # Mock response with multiple chunks
            mock_response = Mock()
            mock_response.headers = {"content-length": "1000"}

            def chunk_generator():
                yield b"x" * 100
                # Cancel after first chunk
                nonlocal cancelled
                cancelled = True
                yield b"x" * 100  # This should trigger cancellation

            mock_response.iter_content.return_value = chunk_generator()

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                with pytest.raises(DownloadCancelled):
                    download(
                        "https://example.com/file.zip",
                        dest_path,
                        is_cancelled=is_cancelled,
                    )

            # File should not exist after cancellation
            assert not dest_path.exists()

    def test_download_content_length_mismatch(self):
        """Test download fails when actual size doesn't match Content-Length."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"

            # Mock response with mismatched content-length
            mock_response = Mock()
            mock_response.headers = {"content-length": "1000"}  # Claims 1000 bytes
            mock_response.iter_content.return_value = [b"x" * 500]  # Only 500 bytes

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                with pytest.raises(ValueError, match="Download incomplete"):
                    download("https://example.com/file.zip", dest_path)

            # File should be cleaned up after failure
            assert not dest_path.exists()

    def test_download_network_timeout(self):
        """Test download timeout handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"

            # Mock timeout exception
            with patch("src.app.update.downloader.requests.get") as mock_get:
                mock_get.side_effect = Exception("Connection timeout")

                with pytest.raises(Exception, match="Connection timeout"):
                    download("https://example.com/file.zip", dest_path, timeout=5)

    def test_download_http_error(self):
        """Test download with HTTP error response."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"

            # Mock HTTP error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                with pytest.raises(Exception, match="404 Not Found"):
                    download("https://example.com/file.zip", dest_path)

    def test_download_progress_accuracy(self):
        """Test accuracy of progress reporting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"
            progress_values = []

            def capture_progress(value):
                progress_values.append(value)

            # Mock response with known chunks
            mock_response = Mock()
            mock_response.headers = {"content-length": "1000"}
            mock_response.iter_content.return_value = [
                b"x" * 250,  # 25%
                b"x" * 250,  # 50%
                b"x" * 250,  # 75%
                b"x" * 250,  # 100%
            ]

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                download(
                    "https://example.com/file.zip",
                    dest_path,
                    progress_callback=capture_progress,
                )

            # Check progress values are monotonically increasing
            for i in range(1, len(progress_values)):
                assert progress_values[i] >= progress_values[i - 1]

            # Check final progress is 100% or close to it
            if progress_values:
                assert progress_values[-1] >= 90  # Allow some rounding

    def test_download_empty_chunks_filtered(self):
        """Test that empty chunks are filtered out."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"

            # Mock response with empty chunks (keep-alive chunks)
            mock_response = Mock()
            mock_response.headers = {"content-length": "500"}
            mock_response.iter_content.return_value = [
                b"x" * 100,  # Real chunk
                b"",  # Empty chunk (should be filtered)
                b"x" * 200,  # Real chunk
                b"",  # Empty chunk (should be filtered)
                b"x" * 200,  # Real chunk
            ]

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                download("https://example.com/file.zip", dest_path)

            # Should have correct final size (empty chunks filtered)
            assert dest_path.exists()
            assert dest_path.stat().st_size == 500

    def test_download_cleanup_on_exception(self):
        """Test that partial files are cleaned up on exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dest_path = Path(temp_dir) / "test_file.zip"

            # Mock response that fails mid-download
            mock_response = Mock()
            mock_response.headers = {"content-length": "1000"}

            def failing_chunks():
                yield b"x" * 100  # Some data written
                raise Exception("Network error during download")

            mock_response.iter_content.return_value = failing_chunks()

            with patch(
                "src.app.update.downloader.requests.get", return_value=mock_response
            ):
                with pytest.raises(Exception, match="Network error during download"):
                    download("https://example.com/file.zip", dest_path)

            # Partial file should be cleaned up
            assert not dest_path.exists()
