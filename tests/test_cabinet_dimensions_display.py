"""
Tests for cabinet dimensions calculation and display logic.

Tests the _cabinet_to_card_data method which determines how dimensions
should be displayed on cabinet cards based on number and characteristics of parts.

Scenarios tested:
1. Cabinet with no parts - dimensions should not be displayed
2. Cabinet with 1 part - show 2D dimensions (width × height), no depth
3. Cabinet with 2+ parts with same widths - show 2D (width × height)
4. Cabinet with 2+ parts with different widths - show 3D with smallest width as depth
"""

from unittest.mock import Mock
import pytest

from src.db_schema.orm_models import ProjectCabinet, ProjectCabinetPart


@pytest.fixture
def mock_project_view():
    """Create a mock ProjectDetailsView with the _cabinet_to_card_data method."""
    from src.gui.project_details.view import ProjectDetailsView

    view = Mock(spec=ProjectDetailsView)
    # Bind the actual method to the mock
    view._cabinet_to_card_data = ProjectDetailsView._cabinet_to_card_data.__get__(view)
    return view


@pytest.fixture
def mock_cabinet_no_parts():
    """Create a cabinet with no parts."""
    cabinet = Mock(spec=ProjectCabinet)
    cabinet.id = 1
    cabinet.sequence_number = 1
    cabinet.quantity = 1
    cabinet.body_color = "Biały"
    cabinet.front_color = "Biały"
    cabinet.parts = []
    cabinet.cabinet_type = None
    return cabinet


@pytest.fixture
def mock_cabinet_single_part():
    """Create a cabinet with single part - should show 2D."""
    cabinet = Mock(spec=ProjectCabinet)
    cabinet.id = 2
    cabinet.sequence_number = 1
    cabinet.quantity = 1
    cabinet.body_color = "Biały"
    cabinet.front_color = "Biały"
    cabinet.cabinet_type = None

    part = Mock(spec=ProjectCabinetPart)
    part.width_mm = 560
    part.height_mm = 720
    part.calc_context_json = {"template_name": "Dolna"}

    cabinet.parts = [part]
    return cabinet


@pytest.fixture
def mock_cabinet_same_width_parts():
    """Create cabinet with multiple parts with same width - should show 2D."""
    cabinet = Mock(spec=ProjectCabinet)
    cabinet.id = 3
    cabinet.sequence_number = 1
    cabinet.quantity = 1
    cabinet.body_color = "Biały"
    cabinet.front_color = "Biały"
    cabinet.cabinet_type = None

    part1 = Mock(spec=ProjectCabinetPart)
    part1.width_mm = 560
    part1.height_mm = 720

    part2 = Mock(spec=ProjectCabinetPart)
    part2.width_mm = 560
    part2.height_mm = 720

    cabinet.parts = [part1, part2]
    return cabinet


@pytest.fixture
def mock_cabinet_different_width_parts():
    """Create cabinet with parts of different widths - should show 3D with depth."""
    cabinet = Mock(spec=ProjectCabinet)
    cabinet.id = 4
    cabinet.sequence_number = 1
    cabinet.quantity = 1
    cabinet.body_color = "Biały"
    cabinet.front_color = "Biały"
    cabinet.cabinet_type = None

    # Sides (thin - represents depth)
    part1 = Mock(spec=ProjectCabinetPart)
    part1.width_mm = 20
    part1.height_mm = 720

    # Front
    part2 = Mock(spec=ProjectCabinetPart)
    part2.width_mm = 560
    part2.height_mm = 720

    # Back
    part3 = Mock(spec=ProjectCabinetPart)
    part3.width_mm = 560
    part3.height_mm = 720

    cabinet.parts = [part1, part2, part3]
    return cabinet


class TestCabinetDimensionsDisplay:
    """Test cabinet dimension calculation and display."""

    def test_cabinet_no_parts_no_dimensions(
        self, mock_project_view, mock_cabinet_no_parts
    ):
        """Cabinet with no parts should not display dimensions."""
        card_data = mock_project_view._cabinet_to_card_data(mock_cabinet_no_parts)

        assert card_data["width_mm"] is None
        assert card_data["height_mm"] is None
        assert card_data["depth_mm"] is None

    def test_cabinet_single_part_2d_dimensions(
        self, mock_project_view, mock_cabinet_single_part
    ):
        """Cabinet with single part should show 2D (width × height, no depth)."""
        card_data = mock_project_view._cabinet_to_card_data(mock_cabinet_single_part)

        assert card_data["width_mm"] == 560
        assert card_data["height_mm"] == 720
        assert card_data["depth_mm"] is None  # No depth for single part
        assert card_data["name"] == "Dolna + niestandardowa"

    def test_cabinet_same_width_parts_2d(
        self, mock_project_view, mock_cabinet_same_width_parts
    ):
        """Cabinet with multiple parts of same width should show 2D."""
        card_data = mock_project_view._cabinet_to_card_data(
            mock_cabinet_same_width_parts
        )

        assert card_data["width_mm"] == 560
        assert card_data["height_mm"] == 720
        # When widths are all the same, no depth can be calculated
        assert card_data["depth_mm"] is None

    def test_cabinet_different_width_parts_3d(
        self, mock_project_view, mock_cabinet_different_width_parts
    ):
        """Cabinet with parts of different widths should show 3D with smallest width as depth."""
        card_data = mock_project_view._cabinet_to_card_data(
            mock_cabinet_different_width_parts
        )

        assert card_data["width_mm"] == 560  # Max of widths
        assert card_data["height_mm"] == 720
        assert card_data["depth_mm"] == 20  # Min of widths (smallest = depth)

    def test_cabinet_with_none_dimensions(self, mock_project_view):
        """Cabinet with parts having None dimensions should handle gracefully."""
        cabinet = Mock(spec=ProjectCabinet)
        cabinet.id = 5
        cabinet.sequence_number = 1
        cabinet.quantity = 1
        cabinet.body_color = "Biały"
        cabinet.front_color = "Biały"
        cabinet.cabinet_type = None

        part = Mock(spec=ProjectCabinetPart)
        part.width_mm = None
        part.height_mm = 720

        cabinet.parts = [part]

        card_data = mock_project_view._cabinet_to_card_data(cabinet)

        # Should handle None gracefully
        assert card_data["width_mm"] is None
        assert card_data["height_mm"] == 720

    def test_cabinet_three_parts_complex(self, mock_project_view):
        """Complex scenario: cabinet with sides, front, and back."""
        cabinet = Mock(spec=ProjectCabinet)
        cabinet.id = 6
        cabinet.sequence_number = 1
        cabinet.quantity = 1
        cabinet.body_color = "Biały"
        cabinet.front_color = "Biały"
        cabinet.cabinet_type = None

        # Side (thin - depth)
        side = Mock(spec=ProjectCabinetPart)
        side.width_mm = 560  # Width of cabinet
        side.height_mm = 720

        # Bottom (thin - depth)
        bottom = Mock(spec=ProjectCabinetPart)
        bottom.width_mm = 560
        bottom.height_mm = 564  # Front width

        # Front (actual width)
        front = Mock(spec=ProjectCabinetPart)
        front.width_mm = 600
        front.height_mm = 720

        cabinet.parts = [side, bottom, front]

        card_data = mock_project_view._cabinet_to_card_data(cabinet)

        # Should use max width, max height, and min of different widths as depth
        assert card_data["width_mm"] == 600  # Max width
        assert card_data["height_mm"] == 720
        assert card_data["depth_mm"] == 560  # Min of widths (smallest = depth)

    def test_cabinet_with_catalog_type(self, mock_project_view):
        """Cabinet with catalog type should use type name, not custom name."""
        cabinet = Mock(spec=ProjectCabinet)
        cabinet.id = 7
        cabinet.sequence_number = 1
        cabinet.quantity = 1
        cabinet.body_color = "Biały"
        cabinet.front_color = "Biały"

        cabinet_type = Mock()
        cabinet_type.name = "LOFT Dolna 60"
        cabinet_type.kitchen_type = "LOFT"
        cabinet.cabinet_type = cabinet_type

        part = Mock(spec=ProjectCabinetPart)
        part.width_mm = 600
        part.height_mm = 720

        cabinet.parts = [part]

        card_data = mock_project_view._cabinet_to_card_data(cabinet)

        assert card_data["name"] == "LOFT Dolna 60"
        assert card_data["kitchen_type"] == "LOFT"
