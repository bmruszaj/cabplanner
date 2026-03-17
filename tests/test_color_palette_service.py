import pytest

from src.db_schema.orm_models import CabinetColor
from src.services.color_palette_service import ColorPaletteService


def test_ensure_seeded_is_idempotent(session):
    service = ColorPaletteService(session)

    service.ensure_seeded()
    first_count = session.query(CabinetColor).filter_by(source="system").count()

    service.ensure_seeded()
    second_count = session.query(CabinetColor).filter_by(source="system").count()

    assert first_count > 100
    assert first_count == second_count


def test_add_user_color_normalizes_hex_and_blocks_duplicates(session):
    service = ColorPaletteService(session)
    service.ensure_seeded()

    created = service.add_user_color("Moj testowy kolor", "#abc")
    assert created.hex_code == "#AABBCC"

    with pytest.raises(ValueError):
        service.add_user_color("moj TESTOWY  kolor", "#123456")


def test_list_recent_returns_empty_when_no_usage(session):
    service = ColorPaletteService(session)
    service.ensure_seeded()

    assert service.list_recent(limit=12) == []


def test_list_recent_sorted_by_usage_and_last_used(session):
    service = ColorPaletteService(session)
    service.ensure_seeded()

    service.mark_used("Biały")
    service.mark_used("Czarny")
    service.mark_used("Czarny")

    recent = service.list_recent(limit=2)

    assert len(recent) == 2
    assert recent[0].casefold() == "czarny"
    assert recent[1].casefold() == "biały"


def test_resolve_hex_for_system_user_and_direct_hex(session):
    service = ColorPaletteService(session)
    service.ensure_seeded()

    assert service.resolve_hex("biały") == "#FFFFFF"
    assert service.resolve_hex("#0f0") == "#00FF00"

    service.add_user_color("Kolor klienta", "#12ab9f")
    assert service.resolve_hex("kolor klienta") == "#12AB9F"


def test_list_searchable_names_includes_added_user_color(session):
    service = ColorPaletteService(session)
    service.ensure_seeded()
    service.add_user_color("Kolor runtime", "#13579B")

    names = service.list_searchable_names()

    assert any(name.casefold() == "kolor runtime" for name in names)


def test_list_dropdown_names_keeps_recent_first_without_hiding_other_colors(session):
    service = ColorPaletteService(session)
    service.ensure_seeded()
    service.add_user_color("Kolor recent", "#13579B")
    service.add_user_color("Kolor ukryty", "#2468AC")

    service.mark_used("Kolor recent")

    names = service.list_dropdown_names(recent_limit=12)
    normalized_names = [name.casefold() for name in names]

    assert normalized_names.count("kolor recent") == 1
    assert "kolor ukryty" in normalized_names
    assert normalized_names.index("kolor recent") < normalized_names.index(
        "kolor ukryty"
    )
