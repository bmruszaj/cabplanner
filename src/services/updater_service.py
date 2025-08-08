import os
import sys
import shutil
import logging
import zipfile

import requests
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)


def is_running_in_development_mode() -> bool:
    """
    Detect if the application is running in development mode.
    Returns True if running as Python script (e.g., from PyCharm), False if running as compiled executable.
    """
    # Check if running as frozen executable (PyInstaller, cx_Freeze, etc.)
    if getattr(sys, "frozen", False):
        logger.debug("Application is running as compiled executable")
        return False

    # Check if running from PyCharm specifically
    if "pycharm" in os.environ.get("_", "").lower():
        logger.debug("Application is running from PyCharm IDE")
        return True

    # Check for PyCharm environment variables
    pycharm_vars = ["PYCHARM_HOSTED", "PYCHARM_DISPLAY_PORT", "JETBRAINS_IDE"]
    if any(var in os.environ for var in pycharm_vars):
        logger.debug(
            "Application is running in PyCharm (environment variables detected)"
        )
        return True

    # Check if sys.executable is python.exe (indicating script mode)
    if sys.executable.endswith(("python.exe", "python3.exe", "python")):
        logger.debug("Application is running as Python script")
        return True

    # Check if __file__ exists and points to a .py file
    try:
        main_file = sys.modules["__main__"].__file__
        if main_file and main_file.endswith(".py"):
            logger.debug("Application is running from .py file: %s", main_file)
            return True
    except (AttributeError, KeyError):
        pass

    logger.debug("Application appears to be running as compiled executable")
    return False


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
RELEASE_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

logger.info("Updater service module initialized with repository: %s", GITHUB_REPO)


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


def get_latest_release_info() -> dict:
    """Fetch information about the latest GitHub release."""
    logger.debug("Fetching latest release info from: %s", RELEASE_API_URL)
    try:
        response = requests.get(RELEASE_API_URL, timeout=5)
        response.raise_for_status()
        release_info = response.json()
        tag = release_info.get("tag_name", "unknown")
        logger.debug("GitHub API response successful, release tag: %s", tag)
        return release_info
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch release info: %s", e)
        raise


def download_file_with_progress(
    url: str, dest_path: Path, progress_callback=None
) -> bool:
    """Download a file with progress reporting."""
    logger.debug("Starting download from URL: %s to path: %s", url, dest_path)
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024
        downloaded = 0
        last_log_percent = 0

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(block_size):
                downloaded += len(chunk)
                f.write(chunk)
                if progress_callback and total_size:
                    percent = int(downloaded * 100 / total_size)
                    progress_callback(percent)
                    current_log = (percent // 10) * 10
                    if current_log > last_log_percent:
                        logger.debug(
                            "Download progress: %d%% (%0.2f KB/%0.2f KB)",
                            percent,
                            downloaded / 1024,
                            total_size / 1024,
                        )
                        last_log_percent = current_log

        logger.debug("Download completed: %s", dest_path)
        return True
    except requests.exceptions.Timeout as e:
        logger.error("Timeout downloading %s: %s", url, e)
        return False
    except Exception:
        logger.exception("Unexpected error downloading %s", url)
        return False


def safe_extract(zip_ref: zipfile.ZipFile, extract_path: Path):
    """Safely extract zip to prevent zip-slip vulnerabilities."""
    for member in zip_ref.namelist():
        member_path = extract_path / member
        if not str(member_path.resolve()).startswith(str(extract_path.resolve())):
            raise RuntimeError(f"Illegal path in zip: {member}")
    zip_ref.extractall(path=extract_path)


def _find_extracted_app_root(extract_dir: Path) -> Path | None:
    """Find the extracted app root by locating cabplanner.exe."""
    exe = next(extract_dir.rglob("cabplanner.exe"), None)
    return exe.parent if exe else None


def _create_shortcut_if_missing(install_dir: Path):
    """Create desktop shortcut if it doesn't exist (first run only)."""
    shortcut_path = install_dir / "Cabplanner.lnk"
    exe_path = install_dir / "cabplanner.exe"

    # Only create if both exe exists and shortcut doesn't exist
    if exe_path.exists() and not shortcut_path.exists():
        try:
            # Use PowerShell to create shortcut with icon
            ps_script = f"""
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{install_dir}"
$Shortcut.IconLocation = "{exe_path},0"
$Shortcut.Description = "Cabplanner Application"
$Shortcut.Save()
"""

            import tempfile

            ps_path = Path(tempfile.gettempdir()) / "create_shortcut.ps1"
            ps_path.write_text(ps_script, encoding="utf-8")

            result = subprocess.run(
                [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ps_path),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Created shortcut: {shortcut_path}")
            else:
                logger.warning(f"Failed to create shortcut: {result.stderr}")

            # Clean up temp script
            ps_path.unlink(missing_ok=True)

        except Exception as e:
            logger.warning(f"Could not create shortcut: {e}")


class UpdaterService(QObject):
    """Service for checking updates and performing application updates."""

    update_progress = Signal(int)
    update_complete = Signal()
    update_failed = Signal(str)
    update_check_complete = Signal(bool, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_version = get_current_version()
        logger.info("Current application version: %s", self.current_version)

    def _write_and_run_inplace_update(self, install_dir: Path, new_dir: Path):
        """Write and execute PowerShell script for in-place folder update."""
        import tempfile

        try:
            from scripts.update import get_update_script

            script_content = get_update_script()
        except ImportError:
            logger.error("Could not import update script")
            self.update_failed.emit("Nie można załadować skryptu aktualizacji")
            return

        ps_path = Path(tempfile.gettempdir()) / "cabplanner_inplace_update.ps1"
        ps_path.write_text(script_content, encoding="utf-8")

        logger.info(f"Created PowerShell update script: {ps_path}")
        logger.info(f"Install directory: {install_dir}")
        logger.info(f"New package directory: {new_dir}")

        subprocess.Popen(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                str(ps_path),
                str(install_dir),
                str(new_dir),
            ],
            creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
        )

        from PySide6.QtCore import QCoreApplication

        QCoreApplication.quit()

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
        if freq is UpdateFrequency.DAILY:
            return delta >= 1
        if freq is UpdateFrequency.WEEKLY:
            return delta >= 7
        if freq is UpdateFrequency.MONTHLY:
            return delta >= 30
        return False  # NEVER

    def check_for_updates(self) -> tuple[bool, str, str]:
        """Check GitHub for a newer release."""
        try:
            logger.info("Checking for application updates...")
            info = get_latest_release_info()
            tag = info.get("tag_name", "").lstrip("v").replace("cabplanner-", "")
            logger.info("Latest version available: %s", tag)

            curr_tup = self._version_to_tuple(self.current_version)
            new_tup = self._version_to_tuple(tag)
            avail = new_tup > curr_tup

            self.update_check_complete.emit(avail, self.current_version, tag)
            return avail, self.current_version, tag
        except Exception:
            logger.exception("Failed to check for updates")
            self.update_check_complete.emit(False, self.current_version, "")
            return False, self.current_version, ""

    def _version_to_tuple(self, version: str) -> tuple:
        """Convert a version string into a comparable tuple."""
        if not version:
            return ()
        for sep in ("-", "+"):
            if sep in version:
                main, pre = version.split(sep, 1)
                parts = [int(p) if p.isdigit() else p for p in main.split(".")]
                return tuple(parts) + (f"{sep}{pre}",)
        parts = [int(p) if p.isdigit() else p for p in version.split(".")]
        return tuple(parts)

    def perform_update(self):
        """Download, install, and restart the application with folder-based updates."""
        try:
            # Skip update in development mode
            if is_running_in_development_mode():
                logger.warning("Cannot perform update in development mode")
                self.update_failed.emit(
                    "Aktualizacja nie jest dostępna w trybie deweloperskim"
                )
                return

            # Get current executable path and install directory
            if getattr(sys, "frozen", False):
                current_exe_path = Path(sys.executable)
                install_dir = current_exe_path.parent
            else:
                self.update_failed.emit(
                    "Nie można zaktualizować: aplikacja nie jest skompilowana"
                )
                return

            logger.info(f"Current install directory: {install_dir}")

            # Get latest release info
            release_info = get_latest_release_info()

            # Find download URL - look for .zip file (onedir package)
            download_url = None
            asset_name = None

            for asset in release_info.get("assets", []):
                if asset["name"].endswith(".zip"):
                    download_url = asset["browser_download_url"]
                    asset_name = asset["name"]
                    logger.info(f"Found ZIP asset: {asset_name}")
                    break

            if not download_url:
                logger.error("No ZIP assets found in release")
                available_assets = [
                    asset["name"] for asset in release_info.get("assets", [])
                ]
                logger.error(f"Available assets: {available_assets}")
                self.update_failed.emit(
                    "Nie znaleziono pakietu aktualizacji (ZIP) dla Windows"
                )
                return

            # Create temporary directory for update
            import tempfile

            temp_dir = Path(tempfile.mkdtemp(prefix="cabplanner_update_"))
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir()

            logger.info(f"Downloading update from: {download_url}")
            logger.info(f"Temporary directory: {temp_dir}")

            # Download zip file (0-70% progress)
            zip_path = temp_dir / "update.zip"
            success = download_file_with_progress(
                download_url,
                zip_path,
                progress_callback=lambda p: self.update_progress.emit(
                    min(int(p * 0.7), 70)
                ),
            )

            if not success:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.update_failed.emit("Nie udało się pobrać aktualizacji")
                return

            # Extract the zip file (70-80% progress)
            self.update_progress.emit(75)
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    safe_extract(zip_ref, extract_dir)
                logger.info(f"Extracted update to: {extract_dir}")
            except Exception as e:
                logger.error(f"Failed to extract zip: {e}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.update_failed.emit(f"Nie udało się rozpakować aktualizacji: {e}")
                return

            # Find the extracted app root by locating cabplanner.exe
            new_dir = _find_extracted_app_root(extract_dir)
            if not new_dir or not new_dir.exists():
                logger.error("No app root found in extracted files")
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.update_failed.emit(
                    "Nie znaleziono aplikacji w pakiecie aktualizacji"
                )
                return

            logger.info(f"Found app root: {new_dir}")

            # Safety: remove packaged database if present (preserve user data)
            db_in_pkg = new_dir / "cabplanner.db"
            if db_in_pkg.exists():
                logger.info("Removing packaged database to preserve user data")
                db_in_pkg.unlink()

            # Verify the new executable exists and is not empty
            new_exe = new_dir / "cabplanner.exe"
            if not new_exe.exists() or new_exe.stat().st_size == 0:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.update_failed.emit("Pobrany plik aktualizacji jest uszkodzony")
                return

            logger.info(
                f"Update package ready: {new_exe} ({new_exe.stat().st_size} bytes)"
            )

            # Update progress (80-100%)
            self.update_progress.emit(90)

            logger.info("Preparing to restart application for update...")

            # Final progress update
            self.update_progress.emit(100)

            # Signal that update is complete and restart
            self.update_complete.emit()

            # Use a short delay to ensure UI updates, then restart using in-place update
            QTimer.singleShot(
                1000, lambda: self._write_and_run_inplace_update(install_dir, new_dir)
            )

        except Exception as e:
            logger.exception(f"Error during update process: {e}")
            self.update_failed.emit(f"Błąd podczas aktualizacji: {e}")

    def create_shortcut_on_first_run(self):
        """Create shortcut on first application run."""
        if getattr(sys, "frozen", False):
            current_exe_path = Path(sys.executable)
            install_dir = current_exe_path.parent
            _create_shortcut_if_missing(install_dir)
