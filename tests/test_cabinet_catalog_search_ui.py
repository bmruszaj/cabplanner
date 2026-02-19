"""
UI regressions for catalog search behavior.
"""

import os

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.gui.cabinet_catalog.browser_widget import CatalogBrowserWidget
from src.gui.cabinet_catalog.window import CatalogWindow
from src.services.catalog_service import CatalogCabinetType


class _FakeCatalogService:
    def __init__(self):
        self.session = None
        self.calls: list[tuple[str, dict | None]] = []

    def list_types(self, query: str = "", filters: dict | None = None):
        self.calls.append((query, filters))
        return [
            CatalogCabinetType(
                id=1,
                name="D60",
                sku="LOFT-001",
                width_mm=600,
                height_mm=720,
                depth_mm=560,
                preview_path=None,
                kitchen_type="LOFT",
                description="Test item",
            )
        ]


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def test_browser_widget_uses_external_search_input_only(qapp):
    service = _FakeCatalogService()
    widget = CatalogBrowserWidget(service)
    widget.show()
    qapp.processEvents()

    assert not hasattr(widget, "search_edit")

    initial_calls = len(service.calls)
    widget.set_query("loft")
    assert len(service.calls) == initial_calls + 1
    assert service.calls[-1][0] == "loft"

    widget.set_query("loft")
    assert len(service.calls) == initial_calls + 1

    widget.close()
    widget.deleteLater()
    qapp.processEvents()


def test_catalog_window_search_is_debounced(qapp):
    service = _FakeCatalogService()
    window = CatalogWindow(catalog_service=service)
    window.show()
    qapp.processEvents()

    baseline_calls = len(service.calls)
    window.search_edit.setText("d")
    window.search_edit.setText("d6")
    window.search_edit.setText("d60")
    qapp.processEvents()

    assert len(service.calls) == baseline_calls

    QTest.qWait(window.SEARCH_DEBOUNCE_MS + 80)
    qapp.processEvents()

    assert len(service.calls) == baseline_calls + 1
    assert service.calls[-1][0] == "d60"

    window.close()
    window.deleteLater()
    qapp.processEvents()


def test_catalog_window_search_enter_applies_immediately(qapp):
    service = _FakeCatalogService()
    window = CatalogWindow(catalog_service=service)
    window.show()
    qapp.processEvents()

    baseline_calls = len(service.calls)
    window.search_edit.setText("loft")
    qapp.processEvents()
    assert len(service.calls) == baseline_calls

    window.search_edit.setFocus()
    qapp.processEvents()
    QTest.keyClick(window.search_edit, Qt.Key_Return)
    qapp.processEvents()

    assert len(service.calls) == baseline_calls + 1
    assert service.calls[-1][0] == "loft"

    window.close()
    window.deleteLater()
    qapp.processEvents()
