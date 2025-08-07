import os
import sys
import logging
from pathlib import Path

from PySide6.QtCore import QSharedMemory, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.gui.main_window import MainWindow
from src.gui.resources.styles import get_theme
from src.gui.update_dialog import UpdateDialog
from src.services.settings_service import SettingsService
from src.services.updater_service import UpdaterService
from src.db_migration import upgrade_database
from src.version import VERSION

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "cabplanner.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# Detect auto-restart loop
if os.environ.get("CABPLANNER_RESTARTING") == "1":
    logger.critical(
        "Detected potential restart loop! Application was restarted recently."
    )
    if "--force-restart" not in sys.argv:
        logger.critical("Exiting to prevent infinite restart loop.")
        sys.exit(1)

# Set environment variable to detect restart loops
os.environ["CABPLANNER_RESTARTING"] = "1"

# Create a file to track this instance
instance_marker = Path(Path.home() / ".cabplanner_instance")
try:
    with open(instance_marker, "w") as f:
        f.write(str(os.getpid()))
except Exception as e:
    logger.warning(f"Could not write instance marker: {e}")

logger.debug("Application starting with PID: %s", os.getpid())
logger.debug("Command line arguments: %s", sys.argv)


class CabplannerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Cabplanner")
        self.app.setOrganizationName("Cabplanner")

        # Set application icon
        if getattr(sys, "frozen", False):
            # Running as executable - icon should be embedded
            icon_path = Path(sys.executable).parent / "_internal/icon.ico"
            if icon_path.exists():
                from PySide6.QtGui import QIcon
                self.app.setWindowIcon(QIcon(str(icon_path)))
        else:
            # Running in development - use icon from project root
            icon_path = Path(__file__).resolve().parents[2] / "icon.ico"
            if icon_path.exists():
                from PySide6.QtGui import QIcon
                self.app.setWindowIcon(QIcon(str(icon_path)))

        # Determine base path for frozen vs. dev mode
        if getattr(sys, "frozen", False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).resolve().parents[2]

        # Ensure database file exists
        db_path = base_path / "cabplanner.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Using database at: %s", db_path)

        # Run migrations
        logger.info("Upgrading database schema (Alembic)...")
        upgrade_database(db_path)

        # SQLAlchemy setup
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.app.aboutToQuit.connect(self.session.close)

        # Load user settings and theme
        self.settings_service = SettingsService(self.session)
        is_dark_mode = self.settings_service.get_setting_value("dark_mode", False)
        self.app.setStyleSheet(get_theme(is_dark_mode))

        # Create updater service
        self.updater_service = UpdaterService()

        # Create shortcut on first run
        self.updater_service.create_shortcut_on_first_run()

        # Create and show main window
        self.main_window = MainWindow(self.session)

    def run(self) -> int:
        """Show the main window and enter Qt's event loop."""
        self.main_window.show()

        # Check for updates on startup after a short delay
        QTimer.singleShot(2000, self._check_startup_updates)

        return self.app.exec()

    def _check_startup_updates(self):
        """Check for updates on startup based on user settings."""
        try:
            # Check if app was just updated and show success message
            self._check_and_show_update_success()

            # Create shortcut on every startup (if enabled in settings)
            create_shortcut_enabled = self.settings_service.get_setting_value("create_shortcut_on_start", True)
            if create_shortcut_enabled:
                self.updater_service.create_shortcut_on_first_run()

            # Update last check timestamp
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            self.settings_service.set_setting("last_update_check", now.isoformat())

            # Check if we should check for updates
            if not self.updater_service.should_check_for_updates(self.settings_service):
                logger.info("Skipping startup update check based on user settings")
                return

            logger.info("Performing startup update check...")

            # Connect signals for handling update results
            self.updater_service.update_check_complete.connect(
                self._handle_startup_update_result
            )

            # Perform the check
            self.updater_service.check_for_updates()

        except Exception as e:
            logger.exception(f"Error during startup update check: {e}")

    def _check_and_show_update_success(self):
        """Check if app was just updated and show success notification."""
        try:
            # Check for update success marker file
            if getattr(sys, 'frozen', False):
                current_exe_path = Path(sys.executable)
                install_dir = current_exe_path.parent
                success_marker = install_dir / ".update_success"

                if success_marker.exists():
                    # Show success message
                    QTimer.singleShot(1500, self._show_update_success_message)

                    # Remove the marker file
                    try:
                        success_marker.unlink()
                        logger.info("Removed update success marker")
                    except Exception as e:
                        logger.warning(f"Could not remove update success marker: {e}")

        except Exception as e:
            logger.exception(f"Error checking update success: {e}")

    def _show_update_success_message(self):
        """Show update success message to user."""
        try:
            QMessageBox.information(
                self.main_window,  # Use main_window instead of self
                "Aktualizacja zakończona",
                "Aplikacja została pomyślnie zaktualizowana do najnowszej wersji!\n\n"
                "Wszystkie Twoje dane zostały zachowane."
            )
        except Exception as e:
            logger.exception(f"Error showing update success message: {e}")

    def _handle_startup_update_result(
        self, update_available, current_version, latest_version
    ):
        """Handle the result of startup update check."""
        try:
            if update_available:
                logger.info(f"Update available: {current_version} -> {latest_version}")

                # Show update dialog
                dialog = UpdateDialog(VERSION, parent=self.main_window)

                # Connect signals properly
                dialog.check_for_updates.connect(self.updater_service.check_for_updates)

                # Connect update button to start the update process
                dialog.perform_update.connect(lambda: self._start_update_process(dialog))

                # Handle update progress and completion
                self.updater_service.update_progress.connect(dialog.on_update_progress)
                self.updater_service.update_complete.connect(dialog.on_update_completed)
                self.updater_service.update_failed.connect(dialog.on_update_failed)

                # Handle cancellation
                dialog.cancel_update.connect(dialog.reject)

                # Show that update is available
                dialog.update_available(current_version, latest_version)
                dialog.show()

            else:
                logger.info("No updates available at startup")

        except Exception as e:
            logger.exception(f"Error handling startup update result: {e}")

    def _start_update_process(self, dialog):
        """Start the update process with proper dialog state management."""
        try:
            # Show update started state
            dialog.on_update_started()

            # Start the actual update
            self.updater_service.perform_update()

        except Exception as e:
            logger.exception(f"Error starting update process: {e}")
            dialog.on_update_failed(str(e))


def main():
    """Entry point when run as a script."""
    single = QSharedMemory("CabplannerApp")
    if not single.create(1):
        QMessageBox.warning(None, "Cabplanner", "Another instance is already running.")
        sys.exit(0)

    try:
        logger.info("Starting Cabplanner application")
        app = CabplannerApp()
        sys.exit(app.run())
    except Exception:
        logger.exception("Unhandled exception in main")
        raise


if __name__ == "__main__":
    main()
