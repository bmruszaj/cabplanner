import os
import logging
import shutil
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum, auto

from PySide6.QtCore import QObject, Signal, QTimer, QRunnable, QThreadPool

from src.app.update.runtime import is_frozen, install_dir, tempdir
from src.app.update.github_client import GitHubClient
from src.app.update.versioning import is_newer_version
from src.app.update.downloader import download, DownloadCancelled
from src.app.update.zipops import safe_extract, find_app_root, verify_onedir_structure
from src.app.update.scripts_runner import run_powershell
from src.app.update.errors import (
    UpdateError,
    NetworkError,
    NoAssetError,
    BadArchiveError,
    UpdateCancelledError,
    NotFrozenError,
    GitHubAPIError,
    ExtractionFailedError,
    ScriptFailedError,
)
from scripts.update import get_update_script
from scripts.shortcut import get_shortcut_script

logger = logging.getLogger(__name__)


class UpdateFrequency(Enum):
    ON_LAUNCH = auto()
    DAILY = auto()
    WEEKLY = auto()
    MONTHLY = auto()
    NEVER = auto()


LABEL_TO_FREQ = {
    "Przy uruchomieniu": UpdateFrequency.ON_LAUNCH,
    "Codziennie": UpdateFrequency.DAILY,
    "Co tydzień": UpdateFrequency.WEEKLY,
    "Co miesiąc": UpdateFrequency.MONTHLY,
    "Nigdy": UpdateFrequency.NEVER,
}

GITHUB_REPO = "bmruszaj/cabplanner"


def get_current_version() -> str:
    """Get current version from the version module."""
    logger.debug("Attempting to get current application version")
    try:
        from src.version import VERSION

        logger.debug("Successfully retrieved version: %s", VERSION)
        return VERSION
    except Exception as e:
        logger.warning("Could not get current version: %s", e)
        return "0.0.0"


class UpdateCheckWorker(QRunnable):
    """Worker for checking updates in background thread."""

    def __init__(self, service: "UpdaterService"):
        super().__init__()
        self.service = service

    def run(self):
        """Check for updates without blocking UI."""
        try:
            current_version = get_current_version()

            # Get GitHub token from environment
            github_token = os.environ.get("GITHUB_TOKEN")
            client = GitHubClient(GITHUB_REPO, github_token)

            release_info = client.get_latest_release()
            latest_version = release_info.tag_name.lstrip("v").replace(
                "cabplanner-", ""
            )

            is_available = is_newer_version(current_version, latest_version)

            logger.info(
                "Update check completed: current=%s, latest=%s, available=%s",
                current_version,
                latest_version,
                is_available,
            )

            # Emit signal on main thread
            self.service.update_check_complete.emit(
                is_available, current_version, latest_version
            )

        except Exception as e:
            logger.exception("Update check failed: %s", e)
            # Convert to appropriate exception type
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                error = NetworkError(f"Network error: {e}")
            elif "github" in str(e).lower() or "api" in str(e).lower():
                error = GitHubAPIError(f"GitHub API error: {e}")
            else:
                error = UpdateError(f"Update check failed: {e}")

            self.service.update_check_failed.emit(error)


class UpdateWorker(QRunnable):
    """Worker for performing updates in background thread."""

    def __init__(self, service: "UpdaterService"):
        super().__init__()
        self.service = service
        self.cancelled = False

    def is_cancelled(self) -> bool:
        """Check if update was cancelled."""
        return self.cancelled

    def cancel(self):
        """Cancel the update operation."""
        self.cancelled = True

    def run(self):
        """Perform update without blocking UI."""
        try:
            # Check if frozen
            if not is_frozen():
                logger.error("Cannot update in development mode")
                error = NotFrozenError("Cannot update in development mode")
                self.service.update_failed.emit(error)
                return

            current_install_dir = install_dir()
            temp_dir = tempdir()

            try:
                # Get release info
                github_token = os.environ.get("GITHUB_TOKEN")
                client = GitHubClient(GITHUB_REPO, github_token)
                release_info = client.get_latest_release()

                # Find Windows onedir ZIP asset
                zip_asset = None
                for asset in release_info.assets:
                    if asset.name.endswith(".zip"):
                        zip_asset = asset
                        break

                if not zip_asset:
                    logger.error("No ZIP asset found in release")
                    error = NoAssetError("No Windows ZIP package found")
                    self.service.update_failed.emit(error)
                    return

                # Download with progress (0-70%)
                zip_path = temp_dir / "update.zip"
                try:
                    download(
                        zip_asset.download_url,
                        zip_path,
                        progress_callback=lambda p: self.service.update_progress.emit(
                            min(int(p * 0.7), 70)
                        ),
                        is_cancelled=self.is_cancelled,
                        timeout=30,
                    )
                except DownloadCancelled:
                    error = UpdateCancelledError("Download cancelled")
                    self.service.update_failed.emit(error)
                    return

                if self.is_cancelled():
                    error = UpdateCancelledError("Update cancelled")
                    self.service.update_failed.emit(error)
                    return

                # Extract (70-85%)
                self.service.update_progress.emit(75)
                extract_dir = temp_dir / "extracted"
                try:
                    safe_extract(zip_path, extract_dir)
                except Exception as e:
                    logger.error("Extraction failed: %s", e)
                    error = ExtractionFailedError(f"Failed to extract ZIP: {e}")
                    self.service.update_failed.emit(error)
                    return

                if self.is_cancelled():
                    error = UpdateCancelledError("Update cancelled")
                    self.service.update_failed.emit(error)
                    return

                # Find and verify app root (85-95%)
                self.service.update_progress.emit(85)
                app_root = find_app_root(extract_dir)
                if not app_root:
                    error = BadArchiveError(
                        "Application executable not found in package"
                    )
                    self.service.update_failed.emit(error)
                    return

                if not verify_onedir_structure(app_root):
                    error = BadArchiveError("Invalid onedir package structure")
                    self.service.update_failed.emit(error)
                    return

                # Remove packaged database to preserve user data
                packaged_db = app_root / "cabplanner.db"
                if packaged_db.exists():
                    packaged_db.unlink()
                    logger.info("Removed packaged database to preserve user data")

                if self.is_cancelled():
                    error = UpdateCancelledError("Update cancelled")
                    self.service.update_failed.emit(error)
                    return

                # Prepare for update (95-100%)
                self.service.update_progress.emit(95)
                self.service.update_progress.emit(100)

                # Signal completion and start update process
                self.service.update_complete.emit()

                # Emit signal to start script on main thread (no timer needed in worker)
                self.service.request_start_script.emit(
                    str(current_install_dir), str(app_root)
                )

            finally:
                # Clean up on error (temp dir will be cleaned by update script on success)
                if self.cancelled and temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            logger.exception("Update failed: %s", e)
            # Convert to appropriate exception type
            if isinstance(e, UpdateError):
                self.service.update_failed.emit(e)
            else:
                error = UpdateError(f"Unexpected error: {e}")
                self.service.update_failed.emit(error)


class UpdaterService(QObject):
    """Service for checking updates and performing application updates."""

    # Signals - now emit exception objects instead of enum codes
    update_progress = Signal(int)
    update_complete = Signal()
    update_failed = Signal(Exception)  # Now emits exception objects
    update_check_complete = Signal(bool, str, str)  # available, current, latest
    update_check_failed = Signal(Exception)  # Now emits exception objects

    # New signals for moving timer operations to main thread
    request_start_script = Signal(str, str)  # install_dir, new_dir
    request_quit = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_version = get_current_version()
        self.thread_pool = QThreadPool()
        self.update_worker = None

        # Connect signals to move timer operations to main thread
        self.request_start_script.connect(self._start_update_script)
        self.request_quit.connect(self._quit_application)

        logger.info("UpdaterService initialized with version: %s", self.current_version)

    def should_check_for_updates(self, settings_service) -> bool:
        """Decide whether to check for updates based on user settings."""
        enabled = settings_service.get_setting_value("auto_update_enabled", True)
        if not enabled:
            logger.info("Automatic updates disabled in settings")
            return False

        freq_label = settings_service.get_setting_value(
            "auto_update_frequency", "Co tydzień"
        )
        freq = LABEL_TO_FREQ.get(freq_label, UpdateFrequency.WEEKLY)
        last_iso = settings_service.get_setting_value("last_update_check", "")

        if not last_iso:
            return True

        try:
            last_dt = datetime.fromisoformat(last_iso)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
        except Exception:
            logger.warning("Invalid last_update_check format: %s", last_iso)
            return True

        delta = (now - last_dt).days
        if freq is UpdateFrequency.ON_LAUNCH:
            return True
        elif freq is UpdateFrequency.DAILY:
            return delta >= 1
        elif freq is UpdateFrequency.WEEKLY:
            return delta >= 7
        elif freq is UpdateFrequency.MONTHLY:
            return delta >= 30
        return False  # NEVER

    def check_for_updates(self):
        """Check GitHub for a newer release asynchronously."""
        logger.info("Starting async update check...")
        worker = UpdateCheckWorker(self)
        self.thread_pool.start(worker)

    def perform_update(self):
        """Download, install, and restart the application asynchronously."""
        logger.info("Starting async update process...")
        self.update_worker = UpdateWorker(self)
        self.thread_pool.start(self.update_worker)

    def cancel_update(self):
        """Cancel the ongoing update operation."""
        if self.update_worker:
            logger.info("Cancelling update operation...")
            self.update_worker.cancel()
            self.update_worker = None

    def create_shortcut_on_first_run(self):
        """Create shortcut on first application run."""
        if not is_frozen():
            logger.debug("Not creating shortcut in development mode")
            return

        current_install_dir = install_dir()
        shortcut_path = current_install_dir / "Cabplanner.lnk"

        # Only create if shortcut doesn't exist
        if shortcut_path.exists():
            logger.debug("Shortcut already exists")
            return

        try:
            script_content = get_shortcut_script()
            process = run_powershell(
                script_content, [str(current_install_dir)], hidden=True
            )

            logger.info("Started shortcut creation script with PID: %s", process.pid)

        except Exception as e:
            logger.warning("Failed to create shortcut: %s", e)

    def _start_update_script(self, install_dir: str, new_dir: str):
        """Start the update script on the main thread with a small delay."""
        # Small delay so UI can repaint
        QTimer.singleShot(
            500, lambda: self._run_update_script(Path(install_dir), Path(new_dir))
        )

    def _run_update_script(self, install_dir: Path, new_dir: Path):
        """Run the PowerShell update script on the main thread."""
        try:
            logger.info("Preparing to run update script...")
            logger.info("Install directory: %s", install_dir)
            logger.info("New directory: %s", new_dir)

            # Verify paths exist before running script
            if not install_dir.exists():
                raise ScriptFailedError(
                    f"Install directory does not exist: {install_dir}"
                )
            if not new_dir.exists():
                raise ScriptFailedError(f"New directory does not exist: {new_dir}")

            script_content = get_update_script()
            logger.info(
                "Generated PowerShell script (length: %d chars)", len(script_content)
            )

            # Log script arguments for debugging
            script_args = [str(install_dir), str(new_dir)]
            logger.info("Script arguments: %s", script_args)

            process = run_powershell(script_content, script_args, hidden=True)
            logger.info("Started update script with PID: %s", process.pid)

            # Check if process is still running after a brief moment
            import time

            time.sleep(0.5)
            poll_result = process.poll()
            if poll_result is not None:
                logger.error(
                    "PowerShell process exited immediately with code: %s", poll_result
                )
                raise ScriptFailedError(
                    f"PowerShell script failed immediately with exit code: {poll_result}"
                )
            else:
                logger.info("PowerShell process is running successfully")

            # Queue app quit on main thread with a small delay
            QTimer.singleShot(2000, self.request_quit.emit)

        except Exception as e:
            logger.error("Failed to run update script: %s", e)
            error = ScriptFailedError(f"Failed to run update script: {e}")
            self.update_failed.emit(error)

    def _quit_application(self):
        """Quit the application (called on main thread)."""
        try:
            from PySide6.QtCore import QCoreApplication

            logger.info("Quitting application for update...")
            QCoreApplication.quit()
        except Exception as e:
            logger.error("Error quitting application: %s", e)
