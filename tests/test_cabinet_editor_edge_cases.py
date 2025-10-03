"""
Edge case tests for cabinet editor dirty state handling.
"""

from unittest.mock import Mock


class TestCabinetEditorEdgeCases:
    """Test edge cases for cabinet editor dirty state management."""

    def test_save_with_no_project_instance_or_cabinet_type(self):
        """Test saving when neither project_instance nor cabinet_type is set."""
        # Mock forms
        instance_form = Mock()
        type_form = Mock()
        parts_form = Mock()
        accessories_form = Mock()

        # All forms are dirty but no data objects
        instance_form.is_dirty.return_value = True
        type_form.is_dirty.return_value = True
        parts_form.is_dirty.return_value = True
        accessories_form.is_dirty.return_value = True

        # No data objects available
        project_instance = None
        cabinet_type = None

        # Extracted logic
        saved_count = 0
        total_dirty = 0

        forms_to_check = [
            (instance_form, project_instance, "instance"),
            (type_form, cabinet_type, "type"),
            (parts_form, cabinet_type, "parts"),
            (accessories_form, project_instance or cabinet_type, "accessories"),
        ]

        for form, data_object, form_type in forms_to_check:
            if form.is_dirty() and data_object:
                total_dirty += 1
                # This branch will never execute because data_object is None

        result = saved_count == total_dirty

        # Should succeed because no forms were processed (no data objects)
        assert result is True
        assert saved_count == 0
        assert total_dirty == 0

        # No forms should be reset
        instance_form.reset_dirty.assert_not_called()
        type_form.reset_dirty.assert_not_called()
        parts_form.reset_dirty.assert_not_called()
        accessories_form.reset_dirty.assert_not_called()

    def test_accessories_form_data_object_priority(self):
        """Test that accessories form uses project_instance first, then cabinet_type."""
        accessories_form = Mock()
        accessories_form.is_dirty.return_value = True

        project_instance = Mock()
        cabinet_type = Mock()

        # When both are available, should use project_instance
        data_object = project_instance or cabinet_type
        assert data_object == project_instance

        # When only cabinet_type is available
        project_instance = None
        data_object = project_instance or cabinet_type
        assert data_object == cabinet_type

        # When neither is available
        cabinet_type = None
        data_object = project_instance or cabinet_type
        assert data_object is None

    def test_form_values_exception_handling(self):
        """Test handling when form.values() raises an exception."""
        # Mock services and data
        project_service = Mock()
        project_instance = Mock()
        project_instance.id = 123

        # Mock form that raises exception in values()
        instance_form = Mock()
        instance_form.is_dirty.return_value = True
        instance_form.values.side_effect = Exception("Form values error")

        # Extracted logic with exception handling
        saved_count = 0
        total_dirty = 0

        forms_to_check = [
            (instance_form, project_instance, "instance"),
        ]

        for form, data_object, form_type in forms_to_check:
            if form.is_dirty() and data_object:
                total_dirty += 1
                try:
                    if form_type == "instance":
                        values = form.values()  # This will raise exception
                        updated_cabinet = project_service.update_cabinet(
                            project_instance.id, **values
                        )
                        if updated_cabinet:
                            form.reset_dirty()
                            saved_count += 1
                except Exception:
                    # Should return False on exception
                    result = False
                    break
        else:
            result = saved_count == total_dirty

        assert result is False
        assert saved_count == 0
        assert total_dirty == 1

        # Service should not be called due to exception
        project_service.update_cabinet.assert_not_called()
        instance_form.reset_dirty.assert_not_called()

    def test_all_forms_clean_after_successful_save(self):
        """Test scenario where all forms are cleaned after successful save."""
        # Mock forms - all initially dirty
        instance_form = Mock()
        type_form = Mock()
        parts_form = Mock()
        accessories_form = Mock()

        instance_form.is_dirty.return_value = True
        type_form.is_dirty.return_value = True
        parts_form.is_dirty.return_value = True
        accessories_form.is_dirty.return_value = True

        instance_form.values.return_value = {"width": 60}
        type_form.values.return_value = {"nazwa": "Test"}

        # Mock services and data
        project_service = Mock()
        catalog_service = Mock()
        project_instance = Mock()
        project_instance.id = 123
        cabinet_type = Mock()
        cabinet_type.id = 456

        project_service.update_cabinet.return_value = project_instance
        catalog_service.update_type.return_value = True

        # Simulate successful save of all forms
        saved_count = 0
        total_dirty = 0

        forms_to_check = [
            (instance_form, project_instance, "instance"),
            (type_form, cabinet_type, "type"),
            (parts_form, cabinet_type, "parts"),
            (accessories_form, project_instance, "accessories"),
        ]

        for form, data_object, form_type in forms_to_check:
            if form.is_dirty() and data_object:
                total_dirty += 1
                try:
                    if form_type == "instance":
                        values = form.values()
                        updated_cabinet = project_service.update_cabinet(
                            project_instance.id, **values
                        )
                        if updated_cabinet:
                            form.reset_dirty()
                            saved_count += 1
                    elif form_type == "type":
                        values = form.values()
                        success = catalog_service.update_type(cabinet_type.id, values)
                        if success:
                            form.reset_dirty()
                            saved_count += 1
                    elif form_type in ["parts", "accessories"]:
                        form.reset_dirty()
                        saved_count += 1
                except Exception:
                    result = False
                    break
        else:
            result = saved_count == total_dirty

        # All should be saved successfully
        assert result is True
        assert saved_count == 4
        assert total_dirty == 4

        # All forms should be reset
        instance_form.reset_dirty.assert_called_once()
        type_form.reset_dirty.assert_called_once()
        parts_form.reset_dirty.assert_called_once()
        accessories_form.reset_dirty.assert_called_once()

        # After successful save, all forms should be clean
        instance_form.is_dirty.return_value = False
        type_form.is_dirty.return_value = False
        parts_form.is_dirty.return_value = False
        accessories_form.is_dirty.return_value = False

        # Check unsaved changes
        has_unsaved = (
            instance_form.is_dirty()
            or type_form.is_dirty()
            or parts_form.is_dirty()
            or accessories_form.is_dirty()
        )

        assert has_unsaved is False

    def test_service_returns_none_vs_false(self):
        """Test distinction between service returning None and False."""
        # Mock services and data
        project_service = Mock()
        catalog_service = Mock()
        project_instance = Mock()
        project_instance.id = 123
        cabinet_type = Mock()
        cabinet_type.id = 456

        # Mock forms
        instance_form = Mock()
        type_form = Mock()

        instance_form.is_dirty.return_value = True
        type_form.is_dirty.return_value = True

        instance_form.values.return_value = {"width": 60}
        type_form.values.return_value = {"nazwa": "Test"}

        # Test: project_service returns None (falsy)
        project_service.update_cabinet.return_value = None
        catalog_service.update_type.return_value = True

        saved_count = 0
        total_dirty = 0

        forms_to_check = [
            (instance_form, project_instance, "instance"),
            (type_form, cabinet_type, "type"),
        ]

        for form, data_object, form_type in forms_to_check:
            if form.is_dirty() and data_object:
                total_dirty += 1
                if form_type == "instance":
                    values = form.values()
                    updated_cabinet = project_service.update_cabinet(
                        project_instance.id, **values
                    )
                    if updated_cabinet:  # None is falsy, so this won't execute
                        form.reset_dirty()
                        saved_count += 1
                elif form_type == "type":
                    values = form.values()
                    success = catalog_service.update_type(cabinet_type.id, values)
                    if success:  # True, so this will execute
                        form.reset_dirty()
                        saved_count += 1

        result = saved_count == total_dirty

        # Should fail because instance save returned None
        assert result is False
        assert saved_count == 1  # Only type succeeded
        assert total_dirty == 2

        # Only type form should be reset
        instance_form.reset_dirty.assert_not_called()
        type_form.reset_dirty.assert_called_once()

    def test_empty_form_values(self):
        """Test handling of empty form values."""
        # Mock services and data
        project_service = Mock()
        project_instance = Mock()
        project_instance.id = 123

        # Mock form returning empty values
        instance_form = Mock()
        instance_form.is_dirty.return_value = True
        instance_form.values.return_value = {}  # Empty dict

        project_service.update_cabinet.return_value = project_instance

        # Extracted logic
        saved_count = 0
        total_dirty = 0

        forms_to_check = [
            (instance_form, project_instance, "instance"),
        ]

        for form, data_object, form_type in forms_to_check:
            if form.is_dirty() and data_object:
                total_dirty += 1
                if form_type == "instance":
                    values = form.values()
                    updated_cabinet = project_service.update_cabinet(
                        project_instance.id,
                        **values,  # Empty dict unpacked
                    )
                    if updated_cabinet:
                        form.reset_dirty()
                        saved_count += 1

        result = saved_count == total_dirty

        # Should succeed even with empty values
        assert result is True
        assert saved_count == 1
        assert total_dirty == 1

        # Service should be called with no keyword arguments
        project_service.update_cabinet.assert_called_once_with(123)
        instance_form.reset_dirty.assert_called_once()
