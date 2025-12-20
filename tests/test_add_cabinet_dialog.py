"""
Tests for AddCabinetDialog and related components.
Tests GUI components that handle accessory unit field.
"""

import pytest

from src.gui.dialogs.add_cabinet_dialog import (
    AccessoriesTableModel,
    AccessoryEditDialog,
)


class TestAccessoriesTableModel:
    """Test AccessoriesTableModel with unit field."""

    def test_headers_include_unit_column(self):
        """Table headers should include Jedn. instead of SKU."""
        model = AccessoriesTableModel([])
        assert model.headers == ["Nazwa", "Ilość", "Jedn."]

    def test_data_displays_unit_as_szt(self):
        """Unit 'szt' should display as 'szt.'"""
        accessories = [{"name": "Hinge", "count": 4, "unit": "szt"}]
        model = AccessoriesTableModel(accessories)

        # Column 0 = name
        from PySide6.QtCore import Qt

        assert model.data(model.index(0, 0), Qt.DisplayRole) == "Hinge"
        # Column 1 = count
        assert model.data(model.index(0, 1), Qt.DisplayRole) == 4
        # Column 2 = unit
        assert model.data(model.index(0, 2), Qt.DisplayRole) == "szt."

    def test_data_displays_unit_as_kpl(self):
        """Unit 'kpl' should display as 'kpl.'"""
        accessories = [{"name": "Handle Set", "count": 1, "unit": "kpl"}]
        model = AccessoriesTableModel(accessories)

        from PySide6.QtCore import Qt

        assert model.data(model.index(0, 2), Qt.DisplayRole) == "kpl."

    def test_data_defaults_to_szt_when_unit_missing(self):
        """When unit is missing, should default to 'szt.'"""
        accessories = [{"name": "Hinge", "count": 4}]  # No unit field
        model = AccessoriesTableModel(accessories)

        from PySide6.QtCore import Qt

        assert model.data(model.index(0, 2), Qt.DisplayRole) == "szt."

    def test_update_accessories(self):
        """Model should update when accessories list changes."""
        model = AccessoriesTableModel([])
        assert model.rowCount() == 0

        new_accessories = [
            {"name": "Hinge", "count": 4, "unit": "szt"},
            {"name": "Handle", "count": 1, "unit": "kpl"},
        ]
        model.update_accessories(new_accessories)
        assert model.rowCount() == 2


class TestAccessoryEditDialog:
    """Test AccessoryEditDialog with unit radio buttons."""

    @pytest.fixture
    def app(self):
        """Create QApplication for GUI tests."""
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    def test_dialog_has_unit_radio_buttons(self, app):
        """Dialog should have radio buttons for unit selection."""
        dialog = AccessoryEditDialog()

        assert hasattr(dialog, "szt_radio")
        assert hasattr(dialog, "kpl_radio")
        assert hasattr(dialog, "unit_group")

    def test_default_unit_is_szt(self, app):
        """Default unit should be 'szt'."""
        dialog = AccessoryEditDialog()

        assert dialog.szt_radio.isChecked()
        assert not dialog.kpl_radio.isChecked()

    def test_load_accessory_with_szt_unit(self, app):
        """Loading accessory with unit='szt' should check szt radio."""
        accessory = {"name": "Hinge", "count": 4, "unit": "szt"}
        dialog = AccessoryEditDialog(accessory=accessory)

        assert dialog.szt_radio.isChecked()
        assert not dialog.kpl_radio.isChecked()

    def test_load_accessory_with_kpl_unit(self, app):
        """Loading accessory with unit='kpl' should check kpl radio."""
        accessory = {"name": "Handle Set", "count": 1, "unit": "kpl"}
        dialog = AccessoryEditDialog(accessory=accessory)

        assert not dialog.szt_radio.isChecked()
        assert dialog.kpl_radio.isChecked()

    def test_accessory_data_includes_unit_szt(self, app):
        """Saved accessory data should include unit='szt' when szt is selected."""
        dialog = AccessoryEditDialog()
        dialog.name_edit.setText("Test Accessory")
        dialog.szt_radio.setChecked(True)
        dialog.quantity_spinbox.setValue(5)

        # Simulate accept without closing
        dialog.accessory_data = {
            "name": dialog.name_edit.text().strip(),
            "unit": "kpl" if dialog.kpl_radio.isChecked() else "szt",
            "count": dialog.quantity_spinbox.value(),
        }

        assert dialog.accessory_data["unit"] == "szt"
        assert dialog.accessory_data["name"] == "Test Accessory"
        assert dialog.accessory_data["count"] == 5

    def test_accessory_data_includes_unit_kpl(self, app):
        """Saved accessory data should include unit='kpl' when kpl is selected."""
        dialog = AccessoryEditDialog()
        dialog.name_edit.setText("Handle Set")
        dialog.kpl_radio.setChecked(True)
        dialog.quantity_spinbox.setValue(1)

        # Simulate accept without closing
        dialog.accessory_data = {
            "name": dialog.name_edit.text().strip(),
            "unit": "kpl" if dialog.kpl_radio.isChecked() else "szt",
            "count": dialog.quantity_spinbox.value(),
        }

        assert dialog.accessory_data["unit"] == "kpl"

    def test_no_sku_field_exists(self, app):
        """Dialog should not have SKU field anymore."""
        dialog = AccessoryEditDialog()

        assert not hasattr(dialog, "sku_edit")
