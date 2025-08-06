import sys
import logging
from pathlib import Path

from PySide6.QtCore import QTimer, QSharedMemory
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.gui.main_window import MainWindow
from src.gui.resources.styles import get_theme
from src.services.settings_service import SettingsService
from src.db_migration import upgrade_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "cabplanner.log"),
    ],
)
logger = logging.getLogger(__name__)


class CabplannerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Cabplanner")
        self.app.setOrganizationName("Cabplanner")

        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).resolve().parents[2]

        db_path = base_path / "cabplanner.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using database at: {db_path}")

        logger.info("Upgrading database schema (Alembic)...")
        upgrade_database(db_path)

        self.engine = create_engine(f"sqlite:///{db_path}")
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self.app.aboutToQuit.connect(self.session.close)

        self.settings_service = SettingsService(self.session)
        is_dark_mode = self.settings_service.get_setting_value("dark_mode", False)

        self.app.setStyleSheet(get_theme(is_dark_mode))

        self.main_window = MainWindow(self.session)
        self.main_window.show()

    def run(self) -> int:
        """Run the application."""
        return self.app.exec()

    def check_for_updates(self):
        """Stub for auto-update logic. Run after the main window shows."""
        logger.info("Checking for updates...")
        # TODO: integrate your update-check mechanism here
        # e.g. spawn a thread or schedule a request to your update server


def main():
    """Main entry point for the application"""
    # Single-instance guard
    single = QSharedMemory("CabplannerApp")
    if not single.create(1):
        QMessageBox.warning(None, "Cabplanner", "Another instance is already running.")
        sys.exit(0)

    try:
        logger.info("Starting Cabplanner application")
        cabplanner = CabplannerApp()
        # Kick off auto-update check once the event loop starts
        QTimer.singleShot(0, cabplanner.check_for_updates)
        sys.exit(cabplanner.run())
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
