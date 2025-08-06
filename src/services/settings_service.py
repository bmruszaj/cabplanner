"""
Settings service for Cabplanner application.
Manages application settings and preferences.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db_schema.orm_models import Setting


class SettingsService:
    """Service for managing application settings."""

    def __init__(self, db_session: Session):
        """
        Initialize the service with a database session.

        Args:
            db_session: SQLAlchemy session
        """
        self.db = db_session

    def get_setting(self, key: str) -> Setting:
        """
        Get a setting by key.

        Args:
            key: The setting key to retrieve

        Returns:
            Setting: The requested setting or None
        """
        stmt = select(Setting).where(Setting.key == key)
        return self.db.scalar(stmt)

    def get_setting_value(self, key: str, default=None):
        """
        Get a setting value by key, with a default if not found.

        Args:
            key: The setting key
            default: Default value if setting is not found

        Returns:
            The setting value or default
        """
        setting = self.get_setting(key)
        if not setting:
            return default

        # Handle different value types
        if setting.value_type == "bool":
            return setting.value.lower() == "true"
        elif setting.value_type == "int":
            return int(setting.value)
        elif setting.value_type == "float":
            return float(setting.value)
        else:
            return setting.value

    def set_setting(self, key: str, value, value_type: str = None):
        """
        Create or update a setting.

        Args:
            key: Setting key
            value: Setting value
            value_type: Value type (str, bool, int, float)

        Returns:
            Setting: The created or updated setting
        """
        # Convert value to string for storage
        str_value = str(value)

        # Determine value type if not specified
        if value_type is None:
            if isinstance(value, bool):
                value_type = "bool"
            elif isinstance(value, int):
                value_type = "int"
            elif isinstance(value, float):
                value_type = "float"
            else:
                value_type = "str"

        # Try to get existing setting
        setting = self.get_setting(key)

        if setting:
            # Update existing setting
            setting.value = str_value
            setting.value_type = value_type
        else:
            # Create new setting
            setting = Setting(key=key, value=str_value, value_type=value_type)
            self.db.add(setting)

        self.db.commit()
        self.db.refresh(setting)
        return setting

    def delete_setting(self, key: str) -> bool:
        """
        Delete a setting by key.

        Args:
            key: The setting key to delete

        Returns:
            bool: True if deleted, False if not found
        """
        setting = self.get_setting(key)
        if setting:
            self.db.delete(setting)
            self.db.commit()
            return True
        return False

    def list_settings(self):
        """
        List all settings.

        Returns:
            List[Setting]: All settings in the database
        """
        stmt = select(Setting)
        return list(self.db.scalars(stmt).all())
