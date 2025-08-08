"""File downloader with progress reporting and cancellation support."""

import logging
from pathlib import Path
from typing import Callable, Optional
import requests

logger = logging.getLogger(__name__)


class DownloadCancelled(Exception):
    """Exception raised when download is cancelled."""

    pass


def download(
    url: str,
    dest_path: Path,
    progress_callback: Optional[Callable[[int], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
    timeout: int = 30,
) -> None:
    """
    Download a file with progress reporting and cancellation support.

    Args:
        url: URL to download from
        dest_path: Destination file path
        progress_callback: Optional callback for progress updates (0-100)
        is_cancelled: Optional callback to check if download should be cancelled
        timeout: Request timeout in seconds

    Raises:
        DownloadCancelled: If download was cancelled
        requests.RequestException: On network errors
        ValueError: If Content-Length verification fails
    """
    logger.debug("Starting download from %s to %s", url, dest_path)

    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        # Get and verify content length
        content_length_header = response.headers.get("content-length")
        if not content_length_header:
            logger.warning("No Content-Length header in response")
            total_size = 0
        else:
            total_size = int(content_length_header)
            logger.debug("Expected download size: %d bytes", total_size)

        block_size = 8192
        downloaded = 0

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=block_size):
                # Check for cancellation
                if is_cancelled and is_cancelled():
                    logger.info("Download cancelled by user")
                    raise DownloadCancelled("Download was cancelled")

                if chunk:  # Filter out keep-alive chunks
                    downloaded += len(chunk)
                    f.write(chunk)

                    # Report progress
                    if progress_callback and total_size > 0:
                        percent = min(int(downloaded * 100 / total_size), 100)
                        progress_callback(percent)

        # Verify downloaded size matches Content-Length if provided
        if total_size > 0 and downloaded != total_size:
            logger.error(
                "Download size mismatch: expected %d, got %d", total_size, downloaded
            )
            raise ValueError(
                f"Download incomplete: expected {total_size} bytes, got {downloaded}"
            )

        logger.debug(
            "Download completed: %d bytes written to %s", downloaded, dest_path
        )

    except requests.exceptions.Timeout:
        logger.error("Download timeout for %s", url)
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Download failed for %s: %s", url, e)
        raise
    except Exception:
        # Clean up partial download on failure
        if dest_path.exists():
            dest_path.unlink(missing_ok=True)
        raise
