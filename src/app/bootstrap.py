import sys
from PySide6.QtWidgets import QApplication
from sqlalchemy.orm import Session
from src.gui.main_window import MainWindow
from src.services.settings_service import SettingsService
from src.services.updater_service import UpdaterService


def create_qt_app() -> QApplication:
    """Create and configure the Qt application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Cabplanner")
    app.setOrganizationName("Cabplanner")
    return app


def create_services(session: Session) -> dict:
    """Create application services and return them in a dictionary."""
    settings_service = SettingsService(session)
    updater_service = UpdaterService()

    # Create shortcut on first run
    updater_service.create_shortcut_on_first_run()

    return {"settings": settings_service, "updater": updater_service}


def create_main_window(session: Session) -> MainWindow:
    """Create and return the main application window."""
    return MainWindow(session)
