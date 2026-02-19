"""
Ensure Save/Cancel dialog actions are explicitly localized to Polish.
"""

import os
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from src.gui.dialogs.accessory_edit_dialog import AccessoryEditDialog
from src.gui.dialogs.cabinet_type_dialog import CabinetTypeDialog
from src.gui.dialogs.color_edit_dialog import ColorEditDialog
from src.gui.dialogs.part_edit_dialog import PartEditDialog
from src.gui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def _normalized_button_text(button):
    return button.text().replace("&", "").strip()


def _assert_polish_save_cancel_labels(button_box, save_button_id, cancel_button_id):
    save_button = button_box.button(save_button_id)
    cancel_button = button_box.button(cancel_button_id)

    assert save_button is not None
    assert cancel_button is not None
    assert _normalized_button_text(save_button) == "Zapisz"
    assert _normalized_button_text(cancel_button) == "Anuluj"


def test_accessory_dialog_buttons_are_polish(qapp):
    dialog = AccessoryEditDialog()
    _assert_polish_save_cancel_labels(
        dialog.button_box,
        QDialogButtonBox.StandardButton.Save,
        QDialogButtonBox.StandardButton.Cancel,
    )
    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_part_dialog_buttons_are_polish(qapp):
    dialog = PartEditDialog()
    _assert_polish_save_cancel_labels(
        dialog.button_box,
        QDialogButtonBox.StandardButton.Save,
        QDialogButtonBox.StandardButton.Cancel,
    )
    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_color_dialog_buttons_are_polish(qapp):
    dialog = ColorEditDialog(color_service=SimpleNamespace())
    button_box = dialog.findChild(QDialogButtonBox)
    assert button_box is not None

    _assert_polish_save_cancel_labels(
        button_box,
        QDialogButtonBox.StandardButton.Save,
        QDialogButtonBox.StandardButton.Cancel,
    )
    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_settings_dialog_buttons_are_polish(qapp, session):
    dialog = SettingsDialog(session)
    _assert_polish_save_cancel_labels(
        dialog.button_box,
        QDialogButtonBox.StandardButton.Save,
        QDialogButtonBox.StandardButton.Cancel,
    )
    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_cabinet_type_dialog_buttons_are_polish(qapp, session):
    dialog = CabinetTypeDialog(session)
    _assert_polish_save_cancel_labels(
        dialog.button_box,
        QDialogButtonBox.StandardButton.Save,
        QDialogButtonBox.StandardButton.Cancel,
    )
    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()
