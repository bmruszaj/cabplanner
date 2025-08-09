from PySide6.QtWidgets import QApplication
from sqlalchemy.orm import Session
from src.gui.resources.styles import get_theme
from src.services.settings_service import SettingsService

def apply_theme(app: QApplication, session: Session) -> None:
    """Apply the user's theme preference to the application."""
    settings_service = SettingsService(session)
    is_dark_mode = settings_service.get_setting_value("dark_mode", False)
    app.setStyleSheet(get_theme(is_dark_mode))

