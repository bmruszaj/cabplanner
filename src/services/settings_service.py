from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.db_schema.orm_models import Setting


class SettingsService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_settings(self) -> Setting:
        """Get the global application settings, creating default if needed"""
        stmt = select(Setting)
        settings = self.db.scalars(stmt).first()

        # If no settings exist, create default
        if not settings:
            settings = Setting()
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)

        return settings

    def update_settings(
        self,
        *,
        base_formula_offset_mm: Optional[float] = None,
        advanced_script: Optional[str] = None,
        theme_accent_rgb: Optional[str] = None,
        autoupdate_interval: Optional[str] = None,
    ) -> Setting:
        """Update global application settings"""
        settings = self.get_settings()

        # Update only provided values
        if base_formula_offset_mm is not None:
            settings.base_formula_offset_mm = base_formula_offset_mm
        if advanced_script is not None:
            settings.advanced_script = advanced_script
        if theme_accent_rgb is not None:
            settings.theme_accent_rgb = theme_accent_rgb
        if autoupdate_interval is not None:
            settings.autoupdate_interval = autoupdate_interval

        self.db.commit()
        self.db.refresh(settings)
        return settings
