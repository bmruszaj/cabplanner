"""
Regression tests for color dropdown population in UI widgets.
"""

import os

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.cabinet_catalog.add_footer import AddFooter
from src.gui.cabinet_editor.instance_form import InstanceForm
from src.services.color_palette_service import ColorPaletteService


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def _combo_items(combo_box):
    return [combo_box.itemText(index) for index in range(combo_box.count())]


def test_add_footer_dropdown_includes_new_color_before_first_use(qapp, session):
    service = ColorPaletteService(session)
    service.ensure_seeded()
    service.add_user_color("Nowy kolor testowy", "#13579B")

    widget = AddFooter(color_service=service)
    widget.show()
    qapp.processEvents()

    assert "Nowy kolor testowy" in _combo_items(widget.body_color_combo)
    assert "Nowy kolor testowy" in _combo_items(widget.front_color_combo)

    widget.close()
    widget.deleteLater()
    qapp.processEvents()


def test_instance_form_dropdown_includes_new_color_before_first_use(qapp, session):
    service = ColorPaletteService(session)
    service.ensure_seeded()
    service.add_user_color("Kolor z edytora", "#2468AC")

    widget = InstanceForm(color_service=service)
    widget.show()
    qapp.processEvents()

    assert "Kolor z edytora" in _combo_items(widget.body_color_combo)
    assert "Kolor z edytora" in _combo_items(widget.front_color_combo)

    widget.close()
    widget.deleteLater()
    qapp.processEvents()
