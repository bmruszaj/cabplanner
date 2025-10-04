import pytest
from src.services.formula_engine import CalculatedPart


class TestFormulaEngine:
    @pytest.fixture(autouse=True)
    def setup_formula_constants(self, formula_constants_service):
        """Set up formula constants that FormulaEngine expects."""
        # Set up some default constants that FormulaEngine expects
        formula_constants_service.set(
            "defaults.board_mm", 18.0, "float", "defaults", "Board thickness"
        )
        formula_constants_service.set(
            "defaults.hdf_mm", 3.0, "float", "defaults", "HDF thickness"
        )
        formula_constants_service.set(
            "gaps.front_gap_top", 2.0, "float", "gaps", "Front gap top"
        )
        formula_constants_service.set(
            "gaps.front_gap_bottom", 2.0, "float", "gaps", "Front gap bottom"
        )
        formula_constants_service.set(
            "gaps.front_gap_side", 2.0, "float", "gaps", "Front gap side"
        )
        formula_constants_service.set(
            "gaps.shelf_back_clear", 10.0, "float", "gaps", "Shelf back clearance"
        )

    def test_calculate_lower_cabinet_parts(self, formula_engine):
        """Test calculating parts for a lower cabinet."""
        # GIVEN dimensions for a lower cabinet
        width, height, depth = 600, 720, 560

        # WHEN calculating parts
        parts = formula_engine.calculate_lower_cabinet_parts(width, height, depth)

        # THEN should return a list of CalculatedPart objects
        assert isinstance(parts, list)
        assert len(parts) > 0
        assert all(isinstance(part, CalculatedPart) for part in parts)

        # THEN should include expected part types
        part_names = [part.part_name for part in parts]
        expected_parts = ["wieniec dolny", "boki", "front", "HDF"]
        for expected in expected_parts:
            assert expected in part_names

    def test_calculate_upper_cabinet_parts(self, formula_engine):
        """Test calculating parts for an upper cabinet."""
        # GIVEN dimensions for an upper cabinet
        width, height, depth = 600, 720, 300

        # WHEN calculating parts
        parts = formula_engine.calculate_upper_cabinet_parts(width, height, depth)

        # THEN should return a list of CalculatedPart objects
        assert isinstance(parts, list)
        assert len(parts) > 0
        assert all(isinstance(part, CalculatedPart) for part in parts)

        # THEN should include expected part types
        part_names = [part.part_name for part in parts]
        expected_parts = [
            "wieniec dolny i górny",
            "boki",
            "półka",
            "front słoje poziomo",
            "HDF",
        ]
        for expected in expected_parts:
            assert expected in part_names

    def test_calculate_drawer_parts(self, formula_engine):
        """Test calculating parts for a drawer."""
        # GIVEN dimensions for a drawer
        width, height, depth = 400, 100, 450

        # WHEN calculating parts
        parts = formula_engine.calculate_drawer_parts(width, height, depth)

        # THEN should return a list of CalculatedPart objects
        assert isinstance(parts, list)
        assert len(parts) > 0
        assert all(isinstance(part, CalculatedPart) for part in parts)

        # THEN should include expected part types
        part_names = [part.part_name for part in parts]
        expected_parts = ["front", "boki", "dno", "tyl"]
        for expected in expected_parts:
            assert expected in part_names

    def test_calculate_cabinet_parts_lower(self, formula_engine):
        """Test calculating cabinet parts with lower cabinet type."""
        # GIVEN cabinet type "lower"
        cabinet_type = "lower"
        width, height, depth = 600, 720, 560

        # WHEN calculating parts
        parts = formula_engine.calculate_cabinet_parts(
            cabinet_type, width, height, depth
        )

        # THEN should delegate to lower cabinet calculation
        assert isinstance(parts, list)
        assert len(parts) > 0
