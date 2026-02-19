"""
Focused UI tests for cabinet card interactions.
"""

import os

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.gui.project_details.widgets import (
    CabinetCard,
    SequenceNumberInput,
    QuantityStepper,
)


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def card_factory(qapp):
    created = []

    def _create(**overrides):
        card_data = {
            "id": 101,
            "sequence": 1,
            "name": "Base Cabinet",
            "body_color": "White",
            "front_color": "White",
            "quantity": 1,
            "width_mm": 600,
            "height_mm": 720,
            "depth_mm": 560,
        }
        card_data.update(overrides)
        card = CabinetCard(card_data)
        card.resize(360, 260)
        card.show()
        qapp.processEvents()
        created.append(card)
        return card

    yield _create

    for card in created:
        card.close()
        card.deleteLater()
    qapp.processEvents()


def test_single_click_selects_and_double_click_edits(qapp, card_factory):
    card = card_factory(id=111)
    selected_ids = []
    edited_ids = []
    click_pos = QPoint(card.width() - 10, card.height() - 10)

    card.sig_selected.connect(lambda cid: selected_ids.append(cid))
    card.sig_edit.connect(lambda cid: edited_ids.append(cid))

    QTest.mouseClick(card, Qt.LeftButton, Qt.NoModifier, click_pos)
    qapp.processEvents()
    assert selected_ids == [111]
    assert edited_ids == []

    selected_ids.clear()
    edited_ids.clear()

    QTest.mouseDClick(card, Qt.LeftButton, Qt.NoModifier, click_pos)
    qapp.processEvents()
    # Double-click includes a press, so selection should be immediate as well.
    assert selected_ids == [111]
    assert edited_ids == [111]


def test_keyboard_selection_and_edit_support(qapp, card_factory):
    card = card_factory(id=112)
    selected_ids = []
    edited_ids = []
    card.sig_selected.connect(lambda cid: selected_ids.append(cid))
    card.sig_edit.connect(lambda cid: edited_ids.append(cid))

    card.setFocus()
    qapp.processEvents()

    QTest.keyClick(card, Qt.Key_Space)
    QTest.keyClick(card, Qt.Key_Return)
    qapp.processEvents()

    assert selected_ids == [112]
    assert edited_ids == [112]


def test_selected_state_uses_dynamic_property(card_factory):
    card = card_factory(id=113)

    card.set_selected(True)
    assert card.is_card_selected() is True
    assert card.property("selected") is True
    assert card.styleSheet() == ""

    card.set_selected(False)
    assert card.property("selected") is False


def test_quantity_stepper_replaces_placeholder_without_layout_jump(card_factory):
    card = card_factory(id=114, quantity=2)

    assert hasattr(card, "quantity_stepper")
    assert not hasattr(card, "_qty_placeholder")
    assert card.quantity_stepper.width() == QuantityStepper.expected_width()

    emitted = []
    card.sig_qty_changed.connect(lambda cid, qty: emitted.append((cid, qty)))
    card.quantity_stepper.increase_btn.click()

    assert emitted[-1] == (114, 3)


def test_sequence_validation_properties(qapp):
    widget = SequenceNumberInput(1)
    widget.set_duplicate_check_callback(lambda value: value == 2)
    widget.show()
    qapp.processEvents()

    widget._start_editing(None)
    widget.input_field.setText("2")
    widget._finish_editing()
    assert widget.get_value() == 1
    assert widget.input_field.property("invalid") is True

    widget.input_field.setText("3")
    widget._finish_editing()
    assert widget.get_value() == 3
    assert widget.input_field.property("invalid") is False
    assert widget.input_field.property("duplicate") is False

    widget.close()
    widget.deleteLater()
    qapp.processEvents()


def test_long_name_is_clamped_to_two_lines_and_tooltip_keeps_full_text(card_factory):
    long_name = (
        "Very long cabinet name with many details and tokens "
        "that should exceed two rendered lines in the card header area "
        "and therefore be truncated for readability."
    )
    card = card_factory(
        id=115, name=long_name, width_mm=None, height_mm=None, depth_mm=None
    )

    rendered = card.name_label.text()
    assert rendered != long_name
    assert rendered.count("\n") <= 1
    assert card.name_label.toolTip() == long_name
    assert "brak wymiarów" in (card.dims_label.toolTip() or card.dims_label.text())
