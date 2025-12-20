"""
Tests for AddCabinetDialog and related components.
Tests GUI components that handle accessory unit field and catalog integration.
"""

import pytest

from src.gui.dialogs.add_cabinet_dialog import AccessoriesTableModel
from src.gui.dialogs.accessory_edit_dialog import AccessoryEditDialog


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
    """Test AccessoryEditDialog with unit radio buttons and catalog support."""

    @pytest.fixture
    def app(self):
        """Create QApplication for GUI tests."""
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    def test_dialog_has_name_combo(self, app):
        """Dialog should have ComboBox for name selection."""
        dialog = AccessoryEditDialog()

        assert hasattr(dialog, "name_combo")
        assert dialog.name_combo.isEditable()

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
        assert dialog.name_combo.currentText() == "Hinge"

    def test_load_accessory_with_kpl_unit(self, app):
        """Loading accessory with unit='kpl' should check kpl radio."""
        accessory = {"name": "Handle Set", "count": 1, "unit": "kpl"}
        dialog = AccessoryEditDialog(accessory=accessory)

        assert not dialog.szt_radio.isChecked()
        assert dialog.kpl_radio.isChecked()
        assert dialog.name_combo.currentText() == "Handle Set"

    def test_accessory_data_includes_unit_szt(self, app):
        """Saved accessory data should include unit='szt' when szt is selected."""
        dialog = AccessoryEditDialog()
        dialog.name_combo.setCurrentText("Test Accessory")
        dialog.szt_radio.setChecked(True)
        dialog.quantity_spinbox.setValue(5)

        # Simulate accept without closing
        dialog.accessory_data = {
            "name": dialog.name_combo.currentText().strip(),
            "unit": "kpl" if dialog.kpl_radio.isChecked() else "szt",
            "count": dialog.quantity_spinbox.value(),
        }

        assert dialog.accessory_data["unit"] == "szt"
        assert dialog.accessory_data["name"] == "Test Accessory"
        assert dialog.accessory_data["count"] == 5

    def test_accessory_data_includes_unit_kpl(self, app):
        """Saved accessory data should include unit='kpl' when kpl is selected."""
        dialog = AccessoryEditDialog()
        dialog.name_combo.setCurrentText("Handle Set")
        dialog.kpl_radio.setChecked(True)
        dialog.quantity_spinbox.setValue(1)

        # Simulate accept without closing
        dialog.accessory_data = {
            "name": dialog.name_combo.currentText().strip(),
            "unit": "kpl" if dialog.kpl_radio.isChecked() else "szt",
            "count": dialog.quantity_spinbox.value(),
        }

        assert dialog.accessory_data["unit"] == "kpl"

    def test_no_sku_field_exists(self, app):
        """Dialog should not have SKU field anymore."""
        dialog = AccessoryEditDialog()

        assert not hasattr(dialog, "sku_edit")

    def test_catalog_accessories_loaded(self, app):
        """Dialog should have catalog_accessories attribute."""
        dialog = AccessoryEditDialog()

        assert hasattr(dialog, "catalog_accessories")
        assert isinstance(dialog.catalog_accessories, list)

    def test_dialog_without_accessory_service(self, app):
        """Dialog should work without accessory_service (empty catalog)."""
        dialog = AccessoryEditDialog(accessory_service=None)

        assert dialog.catalog_accessories == []
        # ComboBox should still have empty option
        assert dialog.name_combo.count() >= 1


class TestAccessoryEditDialogCatalogIntegration:
    """Test AccessoryEditDialog with catalog service integration."""

    @pytest.fixture
    def app(self):
        """Create QApplication for GUI tests."""
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def mock_accessory_service(self):
        """Create a mock accessory service with catalog data."""
        from unittest.mock import MagicMock
        from types import SimpleNamespace

        service = MagicMock()
        service.list_accessories.return_value = [
            SimpleNamespace(name="Zawias cichy domyk", unit="szt"),
            SimpleNamespace(name="Uchwyt standardowy", unit="kpl"),
            SimpleNamespace(name="Prowadnica", unit="szt"),
        ]
        return service

    def test_catalog_items_in_combobox(self, app, mock_accessory_service):
        """Catalog items should appear in ComboBox."""
        dialog = AccessoryEditDialog(accessory_service=mock_accessory_service)

        # Should have empty option + 3 catalog items
        assert dialog.name_combo.count() == 4
        
        items = [dialog.name_combo.itemText(i) for i in range(dialog.name_combo.count())]
        assert "Zawias cichy domyk" in items
        assert "Uchwyt standardowy" in items
        assert "Prowadnica" in items

    def test_selecting_catalog_item_sets_unit(self, app, mock_accessory_service):
        """Selecting item from catalog should set default unit."""
        dialog = AccessoryEditDialog(accessory_service=mock_accessory_service)
        
        # Select kpl unit item
        dialog.name_combo.setCurrentText("Uchwyt standardowy")
        
        # Unit should be set to kpl
        assert dialog.kpl_radio.isChecked()

    def test_selecting_szt_item_sets_szt_unit(self, app, mock_accessory_service):
        """Selecting szt item from catalog should set szt unit."""
        dialog = AccessoryEditDialog(accessory_service=mock_accessory_service)
        
        # First change to kpl to verify it changes back
        dialog.kpl_radio.setChecked(True)
        
        # Select szt unit item
        dialog.name_combo.setCurrentText("Zawias cichy domyk")
        
        # Unit should be set to szt
        assert dialog.szt_radio.isChecked()

    def test_new_name_not_in_catalog(self, app, mock_accessory_service):
        """New names should be identified as not in catalog."""
        dialog = AccessoryEditDialog(accessory_service=mock_accessory_service)
        
        assert dialog._is_new_catalog_entry("Nowe akcesorium")
        assert not dialog._is_new_catalog_entry("Zawias cichy domyk")
        assert not dialog._is_new_catalog_entry("zawias cichy domyk")  # Case insensitive
