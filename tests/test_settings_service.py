import pytest


class TestSettingsService:
    def test_set_setting_new_string(self, settings_service):
        """Test setting a new string setting."""
        setting = settings_service.set_setting("test_string", "test_value", "str")

        assert setting.key == "test_string"
        assert setting.value == "test_value"
        assert setting.value_type == "str"

    def test_set_setting_new_bool(self, settings_service):
        """Test setting a new boolean setting."""
        setting = settings_service.set_setting("test_bool", True, "bool")

        assert setting.key == "test_bool"
        assert setting.value == "True"
        assert setting.value_type == "bool"

    def test_set_setting_new_int(self, settings_service):
        """Test setting a new integer setting."""
        setting = settings_service.set_setting("test_int", 42, "int")

        assert setting.key == "test_int"
        assert setting.value == "42"
        assert setting.value_type == "int"

    def test_set_setting_new_float(self, settings_service):
        """Test setting a new float setting."""
        setting = settings_service.set_setting("test_float", 3.14, "float")

        assert setting.key == "test_float"
        assert setting.value == "3.14"
        assert setting.value_type == "float"

    def test_set_setting_auto_detect_type(self, settings_service):
        """Test automatic type detection when type is not specified."""
        # Boolean
        bool_setting = settings_service.set_setting("auto_bool", True)
        assert bool_setting.value_type == "bool"

        # Integer
        int_setting = settings_service.set_setting("auto_int", 42)
        assert int_setting.value_type == "int"

        # Float
        float_setting = settings_service.set_setting("auto_float", 3.14)
        assert float_setting.value_type == "float"

        # String (default)
        str_setting = settings_service.set_setting("auto_str", "test")
        assert str_setting.value_type == "str"

    def test_set_setting_update_existing(self, settings_service, sample_settings):
        """Test updating an existing setting."""
        # Update existing setting
        updated = settings_service.set_setting("app_name", "Updated CabPlanner", "str")

        assert updated.key == "app_name"
        assert updated.value == "Updated CabPlanner"
        assert updated.value_type == "str"

    def test_get_setting_existing(self, settings_service, sample_settings):
        """Test getting an existing setting."""
        setting = settings_service.get_setting("app_name")

        assert setting is not None
        assert setting.key == "app_name"
        assert setting.value == "CabPlanner"
        assert setting.value_type == "str"

    def test_get_setting_nonexistent(self, settings_service):
        """Test getting a non-existent setting."""
        setting = settings_service.get_setting("nonexistent_key")
        assert setting is None

    def test_get_setting_value_string(self, settings_service, sample_settings):
        """Test getting string setting value."""
        value = settings_service.get_setting_value("app_name")
        assert value == "CabPlanner"
        assert isinstance(value, str)

    def test_get_setting_value_bool_true(self, settings_service, sample_settings):
        """Test getting boolean setting value (True)."""
        value = settings_service.get_setting_value("debug_mode")
        assert value is True
        assert isinstance(value, bool)

    def test_get_setting_value_bool_false(self, settings_service, sample_settings):
        """Test getting boolean setting value (False)."""
        value = settings_service.get_setting_value("auto_save")
        assert value is False
        assert isinstance(value, bool)

    def test_get_setting_value_int(self, settings_service, sample_settings):
        """Test getting integer setting value."""
        value = settings_service.get_setting_value("max_cabinets")
        assert value == 100
        assert isinstance(value, int)

    def test_get_setting_value_float(self, settings_service, sample_settings):
        """Test getting float setting value."""
        value = settings_service.get_setting_value("default_thickness")
        assert value == 18.0
        assert isinstance(value, float)

    def test_get_setting_value_with_default(self, settings_service):
        """Test getting setting value with default for non-existent key."""
        # String default
        value = settings_service.get_setting_value("nonexistent_str", "default_string")
        assert value == "default_string"

        # Boolean default
        value = settings_service.get_setting_value("nonexistent_bool", True)
        assert value is True

        # Integer default
        value = settings_service.get_setting_value("nonexistent_int", 999)
        assert value == 999

        # Float default
        value = settings_service.get_setting_value("nonexistent_float", 2.71)
        assert value == 2.71

    def test_get_setting_value_no_default(self, settings_service):
        """Test getting setting value without default returns None."""
        value = settings_service.get_setting_value("nonexistent_key")
        assert value is None

    def test_list_settings_all(self, settings_service, sample_settings):
        """Test listing all settings."""
        settings = settings_service.list_settings()

        assert len(settings) >= 6  # May have more from other tests
        keys = [s.key for s in settings]
        assert "app_name" in keys
        assert "debug_mode" in keys
        assert "max_cabinets" in keys

    def test_delete_setting_existing(self, settings_service, sample_settings):
        """Test deleting an existing setting."""
        result = settings_service.delete_setting("debug_mode")
        assert result is True

        # Verify setting is deleted
        deleted_setting = settings_service.get_setting("debug_mode")
        assert deleted_setting is None

    def test_delete_setting_nonexistent(self, settings_service):
        """Test deleting a non-existent setting."""
        result = settings_service.delete_setting("nonexistent_key")
        assert result is False

    def test_bool_value_parsing_case_insensitive(self, settings_service):
        """Test boolean value parsing is case insensitive."""
        # Test various boolean string representations
        test_cases = [
            ("true", True),
            ("TRUE", True),
            ("True", True),
            ("false", False),
            ("FALSE", False),
            ("False", False),
            ("yes", False),  # Only "true" should be True
            ("1", False),  # Only "true" should be True
        ]

        for str_value, expected in test_cases:
            # Create setting with manual string value
            settings_service.set_setting(f"bool_test_{str_value}", str_value, "bool")
            # Get the parsed value
            parsed_value = settings_service.get_setting_value(f"bool_test_{str_value}")
            assert parsed_value == expected, (
                f"Failed for '{str_value}' -> expected {expected}, got {parsed_value}"
            )

    def test_type_conversion_errors(self, settings_service):
        """Test handling of type conversion errors."""
        # Set invalid int value
        settings_service.set_setting("invalid_int", "not_a_number", "int")

        # Should raise ValueError when trying to get as int
        with pytest.raises(ValueError):
            settings_service.get_setting_value("invalid_int")

        # Set invalid float value
        settings_service.set_setting("invalid_float", "not_a_number", "float")

        # Should raise ValueError when trying to get as float
        with pytest.raises(ValueError):
            settings_service.get_setting_value("invalid_float")

    def test_database_persistence(self, settings_service):
        """Test that settings are properly persisted to database."""
        # Set a setting
        settings_service.set_setting("persistence_test", "test_value")

        # Create new service instance with same session to verify persistence
        from src.services.settings_service import SettingsService

        new_service = SettingsService(settings_service.db)
        retrieved = new_service.get_setting_value("persistence_test")

        assert retrieved == "test_value"

    def test_project_settings(self, settings_service):
        """Test project-related settings functionality."""
        # Test default_kitchen_type setting
        settings_service.set_setting("default_kitchen_type", "PARIS")
        assert settings_service.get_setting_value("default_kitchen_type") == "PARIS"

        # Test default_project_path setting
        settings_service.set_setting("default_project_path", "/path/to/projects")
        assert (
            settings_service.get_setting_value("default_project_path")
            == "/path/to/projects"
        )

        # Test with defaults
        assert (
            settings_service.get_setting_value("default_kitchen_type", "LOFT")
            == "PARIS"
        )
        assert (
            settings_service.get_setting_value("nonexistent_project_setting", "default")
            == "default"
        )
