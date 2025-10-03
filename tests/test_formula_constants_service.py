from src.services.formula_constants_service import FormulaConstantsService


class TestFormulaConstantsService:
    def test_set_new_constant(self, formula_constants_service):
        """Test setting a new constant."""
        constant = formula_constants_service.set(
            key="test_constant",
            value=25.5,
            type="float",
            group="test_group",
            description="Test constant",
        )

        assert constant.key == "test_constant"
        assert constant.value == 25.5
        assert constant.type == "float"
        assert constant.group == "test_group"
        assert constant.description == "Test constant"

    def test_set_update_existing_constant(
        self, formula_constants_service, sample_formula_constants
    ):
        """Test updating an existing constant."""
        # Update existing constant
        updated = formula_constants_service.set(
            key="plyta_thickness",
            value=20.0,
            type="float",
            group="updated_group",
            description="Updated description",
        )

        assert updated.key == "plyta_thickness"
        assert updated.value == 20.0
        assert updated.group == "updated_group"
        assert updated.description == "Updated description"

    def test_get_existing_constant(
        self, formula_constants_service, sample_formula_constants
    ):
        """Test getting an existing constant."""
        constant = formula_constants_service.get("plyta_thickness")

        assert constant is not None
        assert constant.key == "plyta_thickness"
        assert constant.value == 18.0
        assert constant.group == "dimensions"

    def test_get_nonexistent_constant(self, formula_constants_service):
        """Test getting a non-existent constant."""
        constant = formula_constants_service.get("nonexistent_key")
        assert constant is None

    def test_list_constants_no_filter(
        self, formula_constants_service, sample_formula_constants
    ):
        """Test listing all constants without filter."""
        constants = formula_constants_service.list_constants()

        assert len(constants) >= 5  # May have more from other tests
        keys = [c.key for c in constants]
        assert "plyta_thickness" in keys
        assert "hdf_thickness" in keys
        assert "base_height" in keys

    def test_list_constants_with_group_filter(
        self, formula_constants_service, sample_formula_constants
    ):
        """Test listing constants filtered by group."""
        # Test dimensions group
        dimensions = formula_constants_service.list_constants(group="dimensions")
        assert len(dimensions) >= 2
        keys = [c.key for c in dimensions]
        assert "plyta_thickness" in keys
        assert "hdf_thickness" in keys

        # Test defaults group
        defaults = formula_constants_service.list_constants(group="defaults")
        assert len(defaults) >= 2
        keys = [c.key for c in defaults]
        assert "base_height" in keys
        assert "upper_height" in keys

        # Test gaps group
        gaps = formula_constants_service.list_constants(group="gaps")
        assert len(gaps) >= 1
        gap_keys = [c.key for c in gaps]
        assert "front_gap_top" in gap_keys

    def test_list_constants_nonexistent_group(
        self, formula_constants_service, sample_formula_constants
    ):
        """Test listing constants for non-existent group."""
        constants = formula_constants_service.list_constants(group="nonexistent_group")
        assert len(constants) == 0

    def test_set_with_defaults(self, formula_constants_service):
        """Test setting constant with default parameters."""
        constant = formula_constants_service.set("simple_constant", 10.0)

        assert constant.key == "simple_constant"
        assert constant.value == 10.0
        assert constant.type == "float"  # default
        assert constant.group is None  # default
        assert constant.description is None  # default

    def test_set_different_value_types(self, formula_constants_service):
        """Test setting constants with different value types."""
        # Integer value (will be stored as float)
        int_constant = formula_constants_service.set("int_constant", 15)
        assert int_constant.value == 15.0

        # Float value
        float_constant = formula_constants_service.set("float_constant", 15.5)
        assert float_constant.value == 15.5

        # Zero value
        zero_constant = formula_constants_service.set("zero_constant", 0.0)
        assert zero_constant.value == 0.0

        # Negative value
        negative_constant = formula_constants_service.set("negative_constant", -5.5)
        assert negative_constant.value == -5.5

    def test_set_empty_string_values(self, formula_constants_service):
        """Test setting constant with empty string values."""
        constant = formula_constants_service.set(
            key="empty_strings", value=1.0, type="", group="", description=""
        )

        assert constant.type == ""
        assert constant.group == ""
        assert constant.description == ""

    def test_database_persistence(self, formula_constants_service):
        """Test that constants are properly persisted to database."""
        # Set a constant
        formula_constants_service.set(
            "persistence_test", 42.0, "float", "test", "Persistence test"
        )

        # Create new service instance with same session to verify persistence
        new_service = FormulaConstantsService(formula_constants_service.db)
        retrieved = new_service.get("persistence_test")

        assert retrieved is not None
        assert retrieved.key == "persistence_test"
        assert retrieved.value == 42.0
        assert retrieved.type == "float"
        assert retrieved.group == "test"
        assert retrieved.description == "Persistence test"
