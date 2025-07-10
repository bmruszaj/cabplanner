import pytest
from src.services.formula_engine import FormulaEngine


@pytest.fixture
def engine():
    return FormulaEngine(base_offset_mm=-2.0)


def test_compute_with_all_numeric_keys(engine):
    # GIVEN a dict of multiple numeric dimensions
    dims = {"width": 600, "height": 800.0, "depth": 300}
    # WHEN compute is called
    result = engine.compute(dims)
    # THEN each numeric value has the base offset applied
    assert result == {
        "width": 598,
        "height": 798.0,
        "depth": 298,
    }


def test_compute_with_mixed_types(engine):
    # GIVEN a dict with mixed value types
    dims = {"width": 200, "label": "XL", "enabled": True}
    # WHEN compute is called
    result = engine.compute(dims)
    # THEN numeric values are offset, non-numeric are unchanged
    assert result["width"] == 198
    assert result["label"] == "XL"
    assert result["enabled"] is True


def test_compute_empty_dict(engine):
    # GIVEN an empty dict
    dims = {}
    # WHEN compute is called
    result = engine.compute(dims)
    # THEN result is also empty
    assert result == {}


def test_compute_zero_and_negative(engine):
    # GIVEN dims including zero and negative numbers
    dims = {"zero": 0, "neg": -5.5}
    # WHEN compute is called
    result = engine.compute(dims)
    # THEN it correctly applies offset
    assert result["zero"] == -2.0
    assert result["neg"] == -7.5
