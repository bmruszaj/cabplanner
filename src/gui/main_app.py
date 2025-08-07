# src/gui/main_app.py

import sys
import logging
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QTimer, QSharedMemory
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.gui.main_window import MainWindow
from src.gui.resources.styles import get_theme
from src.services.settings_service import SettingsService
from src.services.updater_service import UpdaterService
from src.db_migration import upgrade_database

# Debug override: when True, always run update check at startup regardless of settings
DEBUG_ALWAYS_RUN_UPDATES = True

# Enable DEBUG logging for the updater service
logging.getLogger("src.services.updater_service").setLevel(logging.DEBUG)
updater_logger = logging.getLogger("src.services.updater_service")
updater_logger.propagate = True

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


class CabplannerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Cabplanner")
        self.app.setOrganizationName("Cabplanner")

        # Determine base path for frozen vs. dev mode
        if getattr(sys, "frozen", False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).resolve().parents[2]

        # Ensure database file exists
        db_path = base_path / "cabplanner.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using database at: {db_path}")

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

        # Create main window (but don't show yet)
        self.main_window = MainWindow(self.session)

        # Prepare updater service with a QObject parent
        self.updater_service = UpdaterService(self.main_window)

    def run(self) -> int:
        """Show main window and schedule an update check once the event loop is running."""
        # Queue the direct update check to fire immediately after exec() starts
        QTimer.singleShot(0, self.direct_check_for_updates)

        # Now show the main UI and enter Qt's event loop
        self.main_window.show()
        return self.app.exec()

    def direct_check_for_updates(self):
        """Perform an update check on startup, honoring settings unless debugging override is enabled."""
        try:
            logger.debug("DIRECT CHECK: starting update check process")

            # Check user preferences unless debug override is set
            should_run = self.updater_service.should_check_for_updates(
                self.settings_service
            )
            if not should_run and not DEBUG_ALWAYS_RUN_UPDATES:
                print("Skipping update check based on user preferences")
                logger.info("Skipping update check based on user preferences")
                return

            if DEBUG_ALWAYS_RUN_UPDATES:
                logger.info("Debug override: forcing update check at startup")

            # Record timestamp of this check
            self.settings_service.set_setting(
                "last_update_check", datetime.now().isoformat()
            )

            # Show a brief status message
            if hasattr(self.main_window, "status") and self.main_window.status:
                self.main_window.status.showMessage(
                    "DEBUG: Sprawdzanie aktualizacji…", 5000
                )

            # Use the main window (a QObject) as parent so signals fire properly
            independent_updater = UpdaterService(self.main_window)

            logger.debug("DIRECT CHECK: connecting update_check_complete signal")
            independent_updater.update_check_complete.connect(
                lambda available, current, latest: self._status_update_handler(
                    available, current, latest
                )
            )

            logger.debug("DIRECT CHECK: calling check_for_updates()")
            independent_updater.check_for_updates()
            logger.debug("DIRECT CHECK: check_for_updates() returned")

        except Exception as e:
            logger.exception("DIRECT CHECK ERROR", exc_info=e)
            if hasattr(self.main_window, "status") and self.main_window.status:
                self.main_window.status.showMessage("DEBUG: Błąd aktualizacji", 5000)

    def _status_update_handler(self, update_available, current_version, latest_version):
        """Update the main window's status bar with the result."""
        try:
            if update_available:
                msg = f"Dostępna aktualizacja: {latest_version}"
            else:
                msg = "Masz najnowszą wersję programu"

            if hasattr(self.main_window, "status") and self.main_window.status:
                self.main_window.status.showMessage(msg, 5000)

        except Exception as e:
            logger.exception(f"Error updating status bar: {e}")

    # (other dialog-based methods omitted for brevity)


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
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
