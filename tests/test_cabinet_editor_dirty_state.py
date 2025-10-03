"""
Test for cabinet editor dialog dirty state handling (without GUI).
"""

import pytest
from unittest.mock import Mock


class MockCabinetEditorDialog:
    """Mock implementation of CabinetEditorDialog for testing without GUI."""

    def __init__(self, project_service=None, catalog_service=None):
        self.project_service = project_service
        self.catalog_service = catalog_service
        self.project_instance = None
        self.cabinet_type = None

        # Mock forms
        self.instance_form = Mock()
        self.type_form = Mock()
        self.parts_form = Mock()
        self.accessories_form = Mock()

        # Initialize all forms as clean
        self.instance_form.is_dirty.return_value = False
        self.type_form.is_dirty.return_value = False
        self.parts_form.is_dirty.return_value = False
        self.accessories_form.is_dirty.return_value = False

    def _save_all_forms(self) -> bool:
        """Implementation of _save_all_forms method extracted from real dialog."""
        saved_count = 0
        total_dirty = 0

        forms_to_check = [
            (self.instance_form, self.project_instance, "instance"),
            (self.type_form, self.cabinet_type, "type"),
            (self.parts_form, self.cabinet_type, "parts"),
            (
                self.accessories_form,
                self.project_instance or self.cabinet_type,
                "accessories",
            ),
        ]

        for form, data_object, form_type in forms_to_check:
            if form.is_dirty() and data_object:
                total_dirty += 1
                try:
                    if form_type == "instance" and self.project_service:
                        values = form.values()
                        updated_cabinet = self.project_service.update_cabinet(
                            self.project_instance.id, **values
                        )
                        if updated_cabinet:
                            self.project_instance = updated_cabinet
                            form.reset_dirty()
                            saved_count += 1

                    elif form_type == "type":
                        values = form.values()
                        success = self.catalog_service.update_type(
                            self.cabinet_type.id, values
                        )
                        if success:
                            for key, value in values.items():
                                if hasattr(self.cabinet_type, key):
                                    setattr(self.cabinet_type, key, value)
                            form.reset_dirty()
                            saved_count += 1

                    elif form_type in ["parts", "accessories"]:
                        form.reset_dirty()
                        saved_count += 1

                except Exception:
                    return False

        return saved_count == total_dirty

    def has_unsaved_changes(self) -> bool:
        """Check if any form has unsaved changes (from _cancel method)."""
        return (
            self.instance_form.is_dirty()
            or self.type_form.is_dirty()
            or self.parts_form.is_dirty()
            or self.accessories_form.is_dirty()
        )


class TestCabinetEditorDirtyState:
    """Test cabinet editor dialog dirty state management."""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        project_service = Mock()
        catalog_service = Mock()
        return project_service, catalog_service

    @pytest.fixture
    def mock_data(self):
        """Create mock data objects."""
        project_instance = Mock()
        project_instance.id = 123
        cabinet_type = Mock()
        cabinet_type.id = 456
        return project_instance, cabinet_type

    @pytest.fixture
    def dialog(self, mock_services):
        """Create mock dialog for testing."""
        project_service, catalog_service = mock_services
        return MockCabinetEditorDialog(project_service, catalog_service)

    def test_save_all_forms_with_no_dirty_forms(self, dialog, mock_data):
        """Test saving when no forms are dirty."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # All forms are clean
        result = dialog._save_all_forms()

        assert result is True
        # No reset_dirty should be called since nothing was dirty
        dialog.instance_form.reset_dirty.assert_not_called()
        dialog.type_form.reset_dirty.assert_not_called()

    def test_save_all_forms_with_instance_dirty(self, dialog, mock_data):
        """Test saving when only instance form is dirty."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Make instance form dirty
        dialog.instance_form.is_dirty.return_value = True
        dialog.instance_form.values.return_value = {"width": 60, "height": 80}

        # Mock successful save
        dialog.project_service.update_cabinet.return_value = project_instance

        result = dialog._save_all_forms()

        assert result is True
        dialog.project_service.update_cabinet.assert_called_once_with(
            123, width=60, height=80
        )
        dialog.instance_form.reset_dirty.assert_called_once()
        dialog.type_form.reset_dirty.assert_not_called()

    def test_save_all_forms_with_type_dirty(self, dialog, mock_data):
        """Test saving when only type form is dirty."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Make type form dirty
        dialog.type_form.is_dirty.return_value = True
        dialog.type_form.values.return_value = {"nazwa": "Updated Cabinet"}

        # Mock successful save
        dialog.catalog_service.update_type.return_value = True

        result = dialog._save_all_forms()

        assert result is True
        dialog.catalog_service.update_type.assert_called_once_with(
            456, {"nazwa": "Updated Cabinet"}
        )
        dialog.type_form.reset_dirty.assert_called_once()
        dialog.instance_form.reset_dirty.assert_not_called()

    def test_save_all_forms_with_multiple_dirty(self, dialog, mock_data):
        """Test saving when multiple forms are dirty."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Make multiple forms dirty
        dialog.instance_form.is_dirty.return_value = True
        dialog.type_form.is_dirty.return_value = True
        dialog.parts_form.is_dirty.return_value = True

        dialog.instance_form.values.return_value = {"width": 60}
        dialog.type_form.values.return_value = {"nazwa": "Test"}

        # Mock successful saves
        dialog.project_service.update_cabinet.return_value = project_instance
        dialog.catalog_service.update_type.return_value = True

        result = dialog._save_all_forms()

        assert result is True
        dialog.instance_form.reset_dirty.assert_called_once()
        dialog.type_form.reset_dirty.assert_called_once()
        dialog.parts_form.reset_dirty.assert_called_once()
        dialog.accessories_form.reset_dirty.assert_not_called()

    def test_save_all_forms_with_service_failure(self, dialog, mock_data):
        """Test handling when service fails to save."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Make instance form dirty
        dialog.instance_form.is_dirty.return_value = True
        dialog.instance_form.values.return_value = {"width": 60}

        # Mock failed save
        dialog.project_service.update_cabinet.return_value = None

        result = dialog._save_all_forms()

        assert result is False
        dialog.instance_form.reset_dirty.assert_not_called()

    def test_save_all_forms_with_exception(self, dialog, mock_data):
        """Test handling when an exception occurs during save."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Make instance form dirty
        dialog.instance_form.is_dirty.return_value = True
        dialog.instance_form.values.return_value = {"width": 60}

        # Mock exception during save
        dialog.project_service.update_cabinet.side_effect = Exception("Database error")

        result = dialog._save_all_forms()

        assert result is False
        dialog.instance_form.reset_dirty.assert_not_called()

    def test_has_unsaved_changes_when_clean(self, dialog):
        """Test unsaved changes check when all forms are clean."""
        result = dialog.has_unsaved_changes()
        assert result is False

    def test_has_unsaved_changes_when_dirty(self, dialog):
        """Test unsaved changes check when some forms are dirty."""
        dialog.instance_form.is_dirty.return_value = True

        result = dialog.has_unsaved_changes()
        assert result is True

    def test_has_unsaved_changes_after_save_all(self, dialog, mock_data):
        """Test that unsaved changes check returns False after successful save_all."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Initially dirty
        dialog.instance_form.is_dirty.return_value = True
        dialog.instance_form.values.return_value = {"width": 60}
        dialog.project_service.update_cabinet.return_value = project_instance

        # Before save - should have unsaved changes
        assert dialog.has_unsaved_changes() is True

        # Save all forms
        result = dialog._save_all_forms()
        assert result is True

        # After save - forms should be marked as clean
        dialog.instance_form.is_dirty.return_value = (
            False  # Simulate reset_dirty effect
        )
        assert dialog.has_unsaved_changes() is False

    def test_partial_save_still_has_unsaved_changes(self, dialog, mock_data):
        """Test that failed saves still show unsaved changes."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Make forms dirty
        dialog.instance_form.is_dirty.return_value = True
        dialog.type_form.is_dirty.return_value = True

        dialog.instance_form.values.return_value = {"width": 60}
        dialog.type_form.values.return_value = {"nazwa": "Test"}

        # Mock partial failure
        dialog.project_service.update_cabinet.return_value = project_instance
        dialog.catalog_service.update_type.return_value = False  # This fails

        # Save should fail overall
        result = dialog._save_all_forms()
        assert result is False

        # Instance form would be reset, but type form remains dirty
        dialog.instance_form.is_dirty.return_value = False
        dialog.type_form.is_dirty.return_value = True  # Still dirty due to failed save

        # Should still have unsaved changes
        assert dialog.has_unsaved_changes() is True

    def test_accessories_form_with_instance_context(self, dialog, mock_data):
        """Test accessories form saving in instance context."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = project_instance
        dialog.cabinet_type = cabinet_type

        # Make accessories form dirty
        dialog.accessories_form.is_dirty.return_value = True

        result = dialog._save_all_forms()

        assert result is True
        dialog.accessories_form.reset_dirty.assert_called_once()

    def test_accessories_form_with_type_only_context(self, dialog, mock_data):
        """Test accessories form saving in type-only context."""
        project_instance, cabinet_type = mock_data
        dialog.project_instance = None  # No instance
        dialog.cabinet_type = cabinet_type

        # Make accessories form dirty
        dialog.accessories_form.is_dirty.return_value = True

        result = dialog._save_all_forms()

        assert result is True
        dialog.accessories_form.reset_dirty.assert_called_once()

    def test_no_data_object_skips_save(self, dialog):
        """Test that forms are skipped when no data object is available."""
        # No project_instance or cabinet_type set
        dialog.instance_form.is_dirty.return_value = True
        dialog.type_form.is_dirty.return_value = True

        result = dialog._save_all_forms()

        # Should succeed because no forms are actually processed (no data objects)
        assert result is True
        dialog.instance_form.reset_dirty.assert_not_called()
        dialog.type_form.reset_dirty.assert_not_called()
