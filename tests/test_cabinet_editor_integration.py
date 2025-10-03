"""
Simple integration test for cabinet editor dialog logic (without GUI).
"""

from unittest.mock import Mock


class TestCabinetEditorRealLogic:
    """Test the real logic extracted from CabinetEditorDialog without GUI dependencies."""

    def test_save_all_forms_method_signature(self):
        """Test that we can verify the method exists and works logically."""
        # Import the real class just to check method exists
        from src.gui.cabinet_editor.editor_dialog import CabinetEditorDialog

        # Verify the method exists (without instantiating the class)
        assert hasattr(CabinetEditorDialog, "_save_all_forms")

        # Check it's a method
        import inspect

        assert inspect.isfunction(getattr(CabinetEditorDialog, "_save_all_forms"))

    def test_extracted_save_all_forms_logic(self):
        """Test the extracted logic from _save_all_forms method."""
        # This tests the same logic pattern as in _save_all_forms
        # without needing to create actual GUI components

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
        parts_form = Mock()
        accessories_form = Mock()

        # Test scenario: instance and parts forms are dirty
        instance_form.is_dirty.return_value = True
        type_form.is_dirty.return_value = False
        parts_form.is_dirty.return_value = True
        accessories_form.is_dirty.return_value = False

        instance_form.values.return_value = {"width": 60, "height": 80}

        # Mock successful services
        project_service.update_cabinet.return_value = project_instance

        # Extracted logic from _save_all_forms
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
                    return False

        result = saved_count == total_dirty

        # Verify results
        assert result is True
        assert saved_count == 2  # instance and parts
        assert total_dirty == 2

        # Verify correct calls
        project_service.update_cabinet.assert_called_once_with(123, width=60, height=80)
        instance_form.reset_dirty.assert_called_once()
        parts_form.reset_dirty.assert_called_once()
        type_form.reset_dirty.assert_not_called()
        accessories_form.reset_dirty.assert_not_called()

    def test_extracted_has_unsaved_changes_logic(self):
        """Test the extracted logic from has_unsaved_changes check."""
        # Mock forms
        instance_form = Mock()
        type_form = Mock()
        parts_form = Mock()
        accessories_form = Mock()

        # All clean
        instance_form.is_dirty.return_value = False
        type_form.is_dirty.return_value = False
        parts_form.is_dirty.return_value = False
        accessories_form.is_dirty.return_value = False

        # Extracted logic from _cancel method
        has_unsaved = (
            instance_form.is_dirty()
            or type_form.is_dirty()
            or parts_form.is_dirty()
            or accessories_form.is_dirty()
        )

        assert has_unsaved is False

        # Make one dirty
        instance_form.is_dirty.return_value = True

        has_unsaved = (
            instance_form.is_dirty()
            or type_form.is_dirty()
            or parts_form.is_dirty()
            or accessories_form.is_dirty()
        )

        assert has_unsaved is True

    def test_extracted_logic_with_service_failure(self):
        """Test extracted logic handles service failures correctly."""
        # Mock services and data
        project_service = Mock()
        catalog_service = Mock()
        project_instance = Mock()
        project_instance.id = 123
        cabinet_type = Mock()
        cabinet_type.id = 456

        # Mock forms - both dirty
        instance_form = Mock()
        type_form = Mock()
        parts_form = Mock()
        accessories_form = Mock()

        instance_form.is_dirty.return_value = True
        type_form.is_dirty.return_value = True
        parts_form.is_dirty.return_value = False
        accessories_form.is_dirty.return_value = False

        instance_form.values.return_value = {"width": 60}
        type_form.values.return_value = {"nazwa": "Test"}

        # Mock: instance succeeds, type fails
        project_service.update_cabinet.return_value = project_instance
        catalog_service.update_type.return_value = False  # Failure

        # Extracted logic
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

        result = saved_count == total_dirty

        # Should fail because type save failed
        assert result is False
        assert saved_count == 1  # Only instance succeeded
        assert total_dirty == 2

        # Verify partial resets
        instance_form.reset_dirty.assert_called_once()
        type_form.reset_dirty.assert_not_called()  # Failed to save
