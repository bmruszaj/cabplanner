"""
Focused tests for ProjectDetailsView and ProjectDetailsWidget behavior.
"""

import os
from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest

from src.gui.project_details.constants import VIEW_MODE_TABLE
from src.gui.project_details.models import CabinetTableModel
from src.gui.project_details.view import ProjectDetailsView
from src.gui.project_details import widget as widget_module


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def project_details_view(qapp):
    view = ProjectDetailsView()
    view.resize(900, 700)
    view.show()
    qapp.processEvents()
    yield view
    view.close()
    view.deleteLater()
    qapp.processEvents()


def _make_part(width_mm=None, height_mm=None, calc_context_json=None):
    return SimpleNamespace(
        width_mm=width_mm,
        height_mm=height_mm,
        calc_context_json=calc_context_json,
    )


def _make_cabinet(
    cabinet_id: int,
    sequence: int = 1,
    quantity: int = 1,
    cabinet_type=None,
    parts=None,
    body_color="Biały",
    front_color="Biały",
):
    return SimpleNamespace(
        id=cabinet_id,
        type_id=getattr(cabinet_type, "id", None),
        sequence_number=sequence,
        quantity=quantity,
        cabinet_type=cabinet_type,
        parts=parts or [],
        body_color=body_color,
        front_color=front_color,
    )


class _FakeController:
    def __init__(self, cabinets=None):
        self.cabinets = cabinets or []
        self.load_calls = 0

    def load_data(self):
        self.load_calls += 1


def test_load_if_needed_loads_only_once_for_empty_controller_cache(
    project_details_view,
):
    view = project_details_view
    controller = _FakeController(cabinets=[])
    view.controller = controller
    view._data_loaded = False

    view.load_if_needed()
    view.load_if_needed()

    assert controller.load_calls == 1
    assert view._data_loaded is True


def test_show_event_does_not_reload_after_first_empty_load(project_details_view, qapp):
    view = project_details_view
    controller = _FakeController(cabinets=[])
    view.controller = controller
    view._data_loaded = False

    view.hide()
    qapp.processEvents()
    view.show()
    qapp.processEvents()
    assert controller.load_calls == 1

    view.hide()
    qapp.processEvents()
    view.show()
    qapp.processEvents()
    assert controller.load_calls == 1


def test_view_state_stays_in_table_mode_after_apply_card_order(project_details_view):
    view = project_details_view
    cabinets = [_make_cabinet(1, sequence=1, quantity=1)]

    view._on_view_mode_changed(VIEW_MODE_TABLE)
    view.apply_card_order(cabinets)

    assert view._current_view_mode == VIEW_MODE_TABLE
    assert view.stacked_widget.currentWidget() is view.table_view


def test_table_refreshes_when_data_changes_in_table_mode(project_details_view):
    view = project_details_view
    view._on_view_mode_changed(VIEW_MODE_TABLE)

    initial = [_make_cabinet(11, sequence=1, quantity=1)]
    updated = [_make_cabinet(11, sequence=1, quantity=3)]

    view.apply_card_order(initial)
    model = view.table_view.model()
    assert model.rowCount() == 1
    assert model.data(model.index(0, 5)) == 1

    view.apply_card_order(updated)
    model = view.table_view.model()
    assert model.rowCount() == 1
    assert model.data(model.index(0, 5)) == 3


def test_cabinet_table_model_uses_custom_name_and_real_dimensions():
    parts = [
        _make_part(
            width_mm=600,
            height_mm=720,
            calc_context_json={"template_name": "D60"},
        )
    ]
    cabinet = _make_cabinet(31, sequence=7, quantity=2, cabinet_type=None, parts=parts)
    model = CabinetTableModel([cabinet])

    assert model.data(model.index(0, 1)) == "D60 + niestandardowa"
    assert model.data(model.index(0, 2)) == "600x720 mm"
    assert model.data(model.index(0, 0), role=Qt.ItemDataRole.UserRole) == 31


def test_widget_show_event_uses_load_if_needed(monkeypatch, qapp):
    class FakeDetailsView(QWidget):
        def __init__(self, session=None, project=None, modal=False, parent=None):
            super().__init__(parent)
            self.load_calls = 0
            self._data_loaded = False

        def load_if_needed(self):
            self.load_calls += 1
            self._data_loaded = True

    monkeypatch.setattr(widget_module, "ProjectDetailsView", FakeDetailsView)

    project = SimpleNamespace(name="Test Project")
    widget = widget_module.ProjectDetailsWidget(session=None, project=project)
    widget.show()
    qapp.processEvents()

    QTest.qWait(80)
    qapp.processEvents()

    assert widget.details_view is not None
    assert widget.details_view.load_calls == 1

    widget.close()
    widget.deleteLater()
    qapp.processEvents()
