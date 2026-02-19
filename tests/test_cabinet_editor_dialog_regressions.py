"""
Regression tests for cabinet editor and custom cabinet dialog UX behavior.
"""

import os
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.cabinet_editor.editor_dialog import CabinetEditorDialog
from src.gui.dialogs.custom_cabinet_dialog import CustomCabinetDialog
import src.gui.cabinet_editor.editor_dialog as editor_dialog_module
import src.gui.dialogs.custom_cabinet_dialog as custom_dialog_module


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


class _FormulaServiceStub:
    def __init__(self):
        self.compute_call = None

    def detect_category(self, _template_name):
        return "D"

    def template_exists(self, _template_name):
        return True

    def compute_parts(self, template_name, width, height, depth):
        self.compute_call = (template_name, width, height, depth)
        return []


def _build_custom_project_instance():
    part = SimpleNamespace(
        id=1,
        part_name="Bok",
        width_mm=600,
        height_mm=720,
        pieces=1,
        material="PLYTA 18",
        wrapping=None,
        comments=None,
        processing_json=None,
        calc_context_json={"template_name": "D60"},
    )
    return SimpleNamespace(
        id=10,
        sequence_number=1,
        quantity=1,
        body_color="Bialy",
        front_color="Bialy",
        handle_type="Standardowy",
        hinges="Automatyczne",
        notes="",
        parts=[part],
        accessory_snapshots=[],
    )


def _build_cabinet_type():
    return SimpleNamespace(
        id=7,
        name="D60",
        parts=[],
        accessories=[],
    )


def test_custom_dialog_auto_dimensions_are_really_available(monkeypatch, qapp):
    formula_service = _FormulaServiceStub()
    project_service = SimpleNamespace()
    project = SimpleNamespace(id=1)

    monkeypatch.setattr(
        custom_dialog_module.QMessageBox, "information", lambda *a, **k: None
    )
    monkeypatch.setattr(
        custom_dialog_module.QMessageBox, "warning", lambda *a, **k: None
    )
    monkeypatch.setattr(
        custom_dialog_module.QMessageBox, "critical", lambda *a, **k: None
    )

    dialog = CustomCabinetDialog(formula_service, project_service, project)
    dialog.show()
    qapp.processEvents()

    assert dialog.width_spinbox.minimum() == 0
    assert dialog.height_spinbox.minimum() == 0
    assert dialog.depth_spinbox.minimum() == 0

    dialog.template_name_edit.setText("D60")
    dialog.width_spinbox.setValue(0)
    dialog.height_spinbox.setValue(0)
    dialog.depth_spinbox.setValue(0)

    dialog._calculate_parts()

    assert formula_service.compute_call == ("D60", None, None, None)

    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_custom_instance_mode_keeps_parts_tab_enabled(qapp):
    dialog = CabinetEditorDialog(
        catalog_service=None,
        project_service=SimpleNamespace(),
        color_service=None,
    )
    dialog.load_custom_instance(_build_custom_project_instance())
    dialog.show()
    qapp.processEvents()

    assert dialog.tab_widget.isTabEnabled(0) is True
    assert dialog.tab_widget.isTabEnabled(1) is True
    assert dialog.tab_widget.isTabEnabled(2) is True

    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_save_button_considers_dirty_changes_from_other_tabs(qapp):
    dialog = CabinetEditorDialog(
        catalog_service=None,
        project_service=SimpleNamespace(),
        color_service=None,
    )
    dialog.load_custom_instance(_build_custom_project_instance())
    dialog.show()
    qapp.processEvents()

    dialog.instance_form.quantity_spinbox.setValue(2)
    qapp.processEvents()
    assert dialog.instance_form.is_dirty() is True
    assert dialog.save_button.isEnabled() is True

    dialog.tab_widget.setCurrentWidget(dialog.accessories_form)
    qapp.processEvents()

    assert dialog.save_button.isEnabled() is True

    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_cancel_confirmation_includes_template_name_change(monkeypatch, qapp):
    class _FakeMessageBox:
        Question = object()
        YesRole = object()
        NoRole = object()
        instances = []

        def __init__(self, *args, **kwargs):
            self._clicked = None
            self._yes_button = None
            self._no_button = None
            self.__class__.instances.append(self)

        def setWindowTitle(self, *_args, **_kwargs):
            return None

        def setText(self, *_args, **_kwargs):
            return None

        def setIcon(self, *_args, **_kwargs):
            return None

        def addButton(self, _label, role):
            button = object()
            if role is self.YesRole:
                self._yes_button = button
            if role is self.NoRole:
                self._no_button = button
            return button

        def setDefaultButton(self, _button):
            return None

        def exec(self):
            self._clicked = self._no_button
            return 0

        def clickedButton(self):
            return self._clicked

    monkeypatch.setattr(editor_dialog_module, "QMessageBox", _FakeMessageBox)

    dialog = CabinetEditorDialog(
        catalog_service=SimpleNamespace(),
        project_service=None,
        color_service=None,
    )
    dialog.load_type(_build_cabinet_type())
    dialog.show()
    qapp.processEvents()

    dialog.name_edit.setText("D60-nowa")
    qapp.processEvents()

    assert dialog._has_unsaved_changes() is True

    dialog._cancel()

    assert len(_FakeMessageBox.instances) == 1

    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()
