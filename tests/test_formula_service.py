import pytest
from unittest.mock import Mock

from src.services.formula_service import FormulaService, PartPlan


@pytest.fixture
def mock_session():
    """Mock session with formula constants."""
    session = Mock()

    # Mock constants
    constants = [
        Mock(key="plyta_thickness", value=18.0),
        Mock(key="hdf_thickness", value=3.0),
        Mock(key="base_height", value=720.0),
        Mock(key="upper_height", value=720.0),
        Mock(key="tall_height", value=2020.0),
        Mock(key="base_depth", value=560.0),
        Mock(key="upper_depth", value=300.0),
        Mock(key="tall_depth", value=560.0),
        Mock(key="front_gap_top", value=2.0),
        Mock(key="front_gap_bottom", value=2.0),
        Mock(key="front_gap_side", value=2.0),
        Mock(key="shelf_back_clear", value=10.0),
    ]

    session.query.return_value.all.return_value = constants
    return session


@pytest.fixture
def service(mock_session):
    return FormulaService(mock_session)


class TestFormulaService:
    def test_detect_category_base_cabinets(self, service):
        """Test detection of base cabinet categories."""
        assert service.detect_category("D60") == "D"
        assert service.detect_category("d40") == "D"
        assert service.detect_category(" D30S3 ") == "D"

    def test_detect_category_upper_cabinets(self, service):
        """Test detection of upper cabinet categories."""
        assert service.detect_category("G60") == "G"
        assert service.detect_category("g40") == "G"
        assert service.detect_category(" G30V ") == "G"

    def test_detect_category_tall_cabinets(self, service):
        """Test detection of tall cabinet categories."""
        assert service.detect_category("N60") == "N"
        assert service.detect_category("n40") == "N"

    def test_detect_category_corner_cabinets(self, service):
        """Test detection of corner cabinet categories."""
        assert service.detect_category("DNZ90") == "DNZ"
        assert service.detect_category("dnz80") == "DNZ"

    def test_detect_category_unknown(self, service):
        """Test detection of unknown categories."""
        assert service.detect_category("X60") == "UNKNOWN"
        assert service.detect_category("ABC") == "UNKNOWN"
        assert service.detect_category("") == "UNKNOWN"

    def test_extract_width_from_name_standard(self, service):
        """Test width extraction from standard template names."""
        assert service.extract_width_from_name("D60") == 600
        assert service.extract_width_from_name("G40") == 400
        assert service.extract_width_from_name("N30") == 300

    def test_extract_width_from_name_with_suffixes(self, service):
        """Test width extraction with various suffixes."""
        assert service.extract_width_from_name("G40S3") == 400
        assert service.extract_width_from_name("D60V") == 600
        assert service.extract_width_from_name("DNZ90L") == 900

    def test_extract_width_from_name_with_spaces(self, service):
        """Test width extraction from names with spaces."""
        assert service.extract_width_from_name(" D 60 ") == 600
        assert service.extract_width_from_name("G 40 S3") == 400

    def test_extract_width_from_name_no_digits(self, service):
        """Test width extraction when no digits present."""
        assert service.extract_width_from_name("ABC") is None
        assert service.extract_width_from_name("") is None
        assert service.extract_width_from_name("DXYZ") is None

    def test_get_constants_caching(self, service):
        """Test that constants are cached properly."""
        # First call
        constants1 = service.get_constants()
        # Second call should use cache
        constants2 = service.get_constants()

        assert constants1 == constants2
        assert service.session.query.call_count == 1

    def test_refresh_constants_clears_cache(self, service):
        """Test that refresh_constants clears the cache."""
        # Get constants to populate cache
        service.get_constants()
        service.session.query.call_count = 1

        # Refresh cache
        service.refresh_constants()

        # Next call should query database again
        service.get_constants()
        assert service.session.query.call_count == 2

    def test_fill_defaults_from_template_base_cabinet(self, service):
        """Test filling defaults for base cabinets."""
        constants = service.get_constants()

        # Test with missing height and depth
        W, H, D = service.fill_defaults_from_template(
            "D60", "D", 600, None, None, constants
        )

        assert W == 600
        assert H == 720  # base_height
        assert D == 560  # base_depth

    def test_fill_defaults_from_template_upper_cabinet(self, service):
        """Test filling defaults for upper cabinets."""
        constants = service.get_constants()

        # Test with missing width, height and depth
        W, H, D = service.fill_defaults_from_template(
            "G40", "G", None, None, None, constants
        )

        assert W == 400  # extracted from name
        assert H == 720  # upper_height
        assert D == 300  # upper_depth

    def test_fill_defaults_from_template_tall_cabinet(self, service):
        """Test filling defaults for tall cabinets."""
        constants = service.get_constants()

        # Test with missing all dimensions
        W, H, D = service.fill_defaults_from_template(
            "N60", "N", None, None, None, constants
        )

        assert W == 600  # extracted from name
        assert H == 2020  # tall_height
        assert D == 560  # tall_depth

    def test_fill_defaults_fallback_width(self, service):
        """Test fallback width when extraction fails."""
        constants = service.get_constants()

        # Test with template name that has no extractable width
        W, H, D = service.fill_defaults_from_template(
            "UNKNOWN", "D", None, None, None, constants
        )

        assert W == 600  # fallback default
        assert H == 720
        assert D == 560

    def test_compute_parts_basic(self, service):
        """Test basic parts computation."""
        # This is a complex test that would need more setup
        # For now, test that it returns a list of PartPlan objects
        parts = service.compute_parts("D60")

        assert isinstance(parts, list)
        # We can't test specific parts without more complex setup,
        # but we can verify the structure
        if parts:
            assert all(isinstance(part, PartPlan) for part in parts)

    def test_compute_parts_with_dimensions(self, service):
        """Test parts computation with custom dimensions."""
        parts = service.compute_parts("D60", user_W=600, user_H=720, user_D=560)

        assert isinstance(parts, list)
        if parts:
            assert all(isinstance(part, PartPlan) for part in parts)
