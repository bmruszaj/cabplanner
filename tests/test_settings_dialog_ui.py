import os

import pytest
from PySide6.QtWidgets import QApplication

from src.gui.settings_dialog import SettingsDialog
from src.services.settings_service import SettingsService


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def test_settings_dialog_loads_report_layout_settings(qapp, session, settings_service):
    settings_service.set_setting("report_left_margin_mm", 7)
    settings_service.set_setting("report_right_margin_mm", 12)
    settings_service.set_setting("report_notes_column_width_percent", 34)
    settings_service.set_setting("report_column_gap_mm", 0.5)
    settings_service.set_setting("report_row_spacing_pt", 3.2)
    settings_service.set_setting("report_header_blank_row", True)

    dialog = SettingsDialog(session)

    assert dialog.report_left_margin_mm.value() == 7
    assert dialog.report_right_margin_mm.value() == 12
    assert dialog.report_notes_column_width_percent.value() == 34
    assert dialog.report_column_gap_mm.value() == pytest.approx(0.5)
    assert dialog.report_row_spacing_pt.value() == pytest.approx(3.2)
    assert dialog.report_header_blank_row.isChecked() is True

    dialog.reject()
    dialog.deleteLater()
    qapp.processEvents()


def test_settings_dialog_saves_report_layout_settings(qapp, session, tmp_path):
    dialog = SettingsDialog(session)
    dialog.db_path_edit.setText(str(tmp_path / "cabplanner.db"))
    dialog.report_left_margin_mm.setValue(4)
    dialog.report_right_margin_mm.setValue(9)
    dialog.report_notes_column_width_percent.setValue(36)
    dialog.report_column_gap_mm.setValue(0.4)
    dialog.report_row_spacing_pt.setValue(1.1)
    dialog.report_header_blank_row.setChecked(True)

    dialog.save_settings()

    settings_service = SettingsService(session)
    assert settings_service.get_setting_value("report_left_margin_mm") == 4
    assert settings_service.get_setting_value("report_right_margin_mm") == 9
    assert settings_service.get_setting_value("report_notes_column_width_percent") == 36
    assert settings_service.get_setting_value("report_column_gap_mm") == pytest.approx(
        0.4
    )
    assert settings_service.get_setting_value("report_row_spacing_pt") == pytest.approx(
        1.1
    )
    assert settings_service.get_setting_value("report_header_blank_row") is True

    dialog.deleteLater()
    qapp.processEvents()
