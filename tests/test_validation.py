"""
Comprehensive validation tests for data integrity.

Tests cover:
1. Part dimensions validation (negative, zero, very large values)
2. Project names validation (empty, too long, special characters)
3. Material validation (invalid values)
4. Quantity validation (0, negative, float instead of int)
"""

import pytest
from sqlalchemy.exc import IntegrityError, DataError

from src.db_schema.orm_models import (
    ProjectCabinet,
)


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def test_project(session, project_service):
    """Create a test project."""
    return project_service.create_project(
        name="Test Project",
        order_number="TEST-001",
        kitchen_type="LOFT",
    )


@pytest.fixture
def test_cabinet(session, test_project):
    """Create a test cabinet."""
    cabinet = ProjectCabinet(
        project_id=test_project.id,
        sequence_number=1,
        body_color="White",
        front_color="Oak",
        handle_type="Standard",
        quantity=1,
    )
    session.add(cabinet)
    session.commit()
    return cabinet


@pytest.fixture
def test_template(session, template_service):
    """Create a test cabinet template."""
    return template_service.create_template(
        kitchen_type="LOFT",
        name="TestTemplate",
    )


# ============================================================
# PART DIMENSIONS VALIDATION TESTS
# ============================================================


class TestPartDimensionsValidation:
    """Test validation of part dimensions (width_mm, height_mm)."""

    # ---- Negative Values ----

    def test_add_part_negative_width(self, session, project_service, test_cabinet):
        """Test adding part with negative width."""
        # WHEN: Adding part with negative width
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Negative Width Part",
            width_mm=-500,
            height_mm=400,
        )

        # THEN: Operation may succeed (no DB constraint) but value is stored
        # This test documents current behavior - negative values are accepted
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].width_mm == -500

    def test_add_part_negative_height(self, session, project_service, test_cabinet):
        """Test adding part with negative height."""
        # WHEN: Adding part with negative height
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Negative Height Part",
            width_mm=500,
            height_mm=-400,
        )

        # THEN: Operation may succeed - documents current behavior
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].height_mm == -400

    def test_add_part_both_dimensions_negative(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with both dimensions negative."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Both Negative Part",
            width_mm=-500,
            height_mm=-400,
        )

        # Documents current behavior
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].width_mm == -500
            assert test_cabinet.parts[0].height_mm == -400

    # ---- Zero Values ----

    def test_add_part_zero_width(self, session, project_service, test_cabinet):
        """Test adding part with zero width."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Zero Width Part",
            width_mm=0,
            height_mm=400,
        )

        # THEN: Should handle zero width
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].width_mm == 0

    def test_add_part_zero_height(self, session, project_service, test_cabinet):
        """Test adding part with zero height."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Zero Height Part",
            width_mm=500,
            height_mm=0,
        )

        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].height_mm == 0

    def test_add_part_both_zero(self, session, project_service, test_cabinet):
        """Test adding part with both dimensions zero."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Zero Both Part",
            width_mm=0,
            height_mm=0,
        )

        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].width_mm == 0
            assert test_cabinet.parts[0].height_mm == 0

    # ---- Very Large Values ----

    def test_add_part_very_large_width(self, session, project_service, test_cabinet):
        """Test adding part with very large width (10 meters)."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Very Large Width Part",
            width_mm=10000,  # 10 meters
            height_mm=400,
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].width_mm == 10000

    def test_add_part_extremely_large_width(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with extremely large width (100 meters)."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Extremely Large Width Part",
            width_mm=100000,  # 100 meters
            height_mm=400,
        )

        # Should handle large values within integer range
        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].width_mm == 100000

    def test_add_part_max_integer_dimensions(
        self, session, project_service, test_cabinet
    ):
        """Test adding part with maximum integer dimensions."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Max Integer Part",
            width_mm=2147483647,  # Max 32-bit integer
            height_mm=2147483647,
        )

        # Should handle max integer values
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].width_mm == 2147483647

    # ---- Template Parts Dimensions ----

    def test_template_part_negative_dimensions(
        self, session, template_service, test_template
    ):
        """Test adding template part with negative dimensions - should be rejected by CHECK constraint."""
        # THEN: Should raise IntegrityError due to CHECK constraint ck_part_dims_nonneg
        with pytest.raises(IntegrityError, match="CHECK constraint failed"):
            template_service.add_part(
                cabinet_type_id=test_template.id,
                part_name="Negative Dim Part",
                height_mm=-720,
                width_mm=-560,
                pieces=1,
            )

    def test_template_part_zero_dimensions(
        self, session, template_service, test_template
    ):
        """Test adding template part with zero dimensions."""
        part = template_service.add_part(
            cabinet_type_id=test_template.id,
            part_name="Zero Dim Part",
            height_mm=0,
            width_mm=0,
            pieces=1,
        )

        assert part.height_mm == 0
        assert part.width_mm == 0


# ============================================================
# PROJECT NAME VALIDATION TESTS
# ============================================================


class TestProjectNameValidation:
    """Test validation of project names."""

    # ---- Empty Names ----

    def test_create_project_empty_name(self, session, project_service):
        """Test creating project with empty name."""
        # WHEN: Creating project with empty name
        project = project_service.create_project(
            name="",
            order_number="EMPTY-001",
            kitchen_type="LOFT",
        )

        # THEN: Project is created (no constraint on name being non-empty)
        assert project is not None
        assert project.name == ""

    def test_create_project_whitespace_only_name(self, session, project_service):
        """Test creating project with whitespace-only name."""
        project = project_service.create_project(
            name="   ",
            order_number="WHITESPACE-001",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert project.name == "   "

    def test_create_project_none_name(self, session, project_service):
        """Test creating project with None name."""
        # WHEN: Creating project with None name
        # THEN: Should raise IntegrityError due to NOT NULL constraint
        with pytest.raises(IntegrityError):
            project_service.create_project(
                name=None,
                order_number="NONE-001",
                kitchen_type="LOFT",
            )

    # ---- Very Long Names ----

    def test_create_project_long_name_255_chars(self, session, project_service):
        """Test creating project with 255 character name (at limit)."""
        long_name = "A" * 255

        project = project_service.create_project(
            name=long_name,
            order_number="LONG-001",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert len(project.name) == 255

    def test_create_project_very_long_name_500_chars(self, session, project_service):
        """Test creating project with 500 character name (over limit)."""
        very_long_name = "B" * 500

        # Behavior depends on DB - SQLite may truncate or allow
        try:
            project = project_service.create_project(
                name=very_long_name,
                order_number="VERYLONG-001",
                kitchen_type="LOFT",
            )
            # If succeeds, check what was stored
            assert project is not None
        except (IntegrityError, DataError):
            # Expected if DB enforces VARCHAR limit
            pass

    def test_create_project_extremely_long_name(self, session, project_service):
        """Test creating project with extremely long name (10000 chars)."""
        extremely_long_name = "C" * 10000

        try:
            project = project_service.create_project(
                name=extremely_long_name,
                order_number="EXTREMELONG-001",
                kitchen_type="LOFT",
            )
            assert project is not None
        except (IntegrityError, DataError):
            pass

    # ---- Special Characters ----

    def test_create_project_unicode_name(self, session, project_service):
        """Test creating project with Unicode characters."""
        unicode_name = "Projekt Kuchni Łódzka 日本語 🏠"

        project = project_service.create_project(
            name=unicode_name,
            order_number="UNICODE-001",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert project.name == unicode_name

    def test_create_project_polish_characters(self, session, project_service):
        """Test creating project with Polish diacritics."""
        polish_name = "Projekt Żółtej Kuchni Świętokrzyskiej"

        project = project_service.create_project(
            name=polish_name,
            order_number="POLISH-001",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert project.name == polish_name

    def test_create_project_special_chars(self, session, project_service):
        """Test creating project with special characters."""
        special_name = "Project <test> & 'quotes' \"double\" /path\\back"

        project = project_service.create_project(
            name=special_name,
            order_number="SPECIAL-001",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert project.name == special_name

    def test_create_project_sql_injection_attempt(self, session, project_service):
        """Test creating project with SQL injection attempt in name."""
        injection_name = "'; DROP TABLE projects; --"

        project = project_service.create_project(
            name=injection_name,
            order_number="INJECTION-001",
            kitchen_type="LOFT",
        )

        # Should be safely escaped and stored as literal string
        assert project is not None
        assert project.name == injection_name

    def test_create_project_newlines_in_name(self, session, project_service):
        """Test creating project with newlines in name."""
        newline_name = "Project\nWith\nNewlines"

        project = project_service.create_project(
            name=newline_name,
            order_number="NEWLINE-001",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert "\n" in project.name

    def test_create_project_tabs_in_name(self, session, project_service):
        """Test creating project with tabs in name."""
        tab_name = "Project\tWith\tTabs"

        project = project_service.create_project(
            name=tab_name,
            order_number="TAB-001",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert "\t" in project.name

    # ---- Order Number Validation ----

    def test_create_project_empty_order_number(self, session, project_service):
        """Test creating project with empty order number."""
        project = project_service.create_project(
            name="Test Project",
            order_number="",
            kitchen_type="LOFT",
        )

        assert project is not None
        assert project.order_number == ""

    def test_create_project_duplicate_order_number(self, session, project_service):
        """Test creating project with duplicate order number - should be rejected by UNIQUE constraint."""
        # Create first project
        project_service.create_project(
            name="First Project",
            order_number="DUPLICATE-001",
            kitchen_type="LOFT",
        )

        # THEN: Should raise IntegrityError due to UNIQUE constraint
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
            project_service.create_project(
                name="Second Project",
                order_number="DUPLICATE-001",
                kitchen_type="LOFT",
            )


# ============================================================
# MATERIAL VALIDATION TESTS
# ============================================================


class TestMaterialValidation:
    """Test validation of material field values."""

    # ---- Valid Materials ----

    def test_add_part_valid_plyta_12(self, session, project_service, test_cabinet):
        """Test adding part with valid PLYTA 12 material."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="PLYTA 12 Part",
            width_mm=500,
            height_mm=400,
            material="PLYTA 12",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "PLYTA 12"

    def test_add_part_valid_plyta_16(self, session, project_service, test_cabinet):
        """Test adding part with valid PLYTA 16 material."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="PLYTA 16 Part",
            width_mm=500,
            height_mm=400,
            material="PLYTA 16",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "PLYTA 16"

    def test_add_part_valid_plyta_18(self, session, project_service, test_cabinet):
        """Test adding part with valid PLYTA 18 material."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="PLYTA 18 Part",
            width_mm=500,
            height_mm=400,
            material="PLYTA 18",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "PLYTA 18"

    def test_add_part_valid_hdf(self, session, project_service, test_cabinet):
        """Test adding part with valid HDF material."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="HDF Part",
            width_mm=500,
            height_mm=400,
            material="HDF",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "HDF"

    def test_add_part_valid_front(self, session, project_service, test_cabinet):
        """Test adding part with valid FRONT material."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="FRONT Part",
            width_mm=500,
            height_mm=400,
            material="FRONT",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "FRONT"

    # ---- Invalid/Arbitrary Materials ----

    def test_add_part_invalid_material(self, session, project_service, test_cabinet):
        """Test adding part with invalid material name."""
        # WHEN: Adding part with invalid material
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Invalid Material Part",
            width_mm=500,
            height_mm=400,
            material="INVALID_MATERIAL",
        )

        # THEN: Currently no validation - any string is accepted
        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "INVALID_MATERIAL"

    def test_add_part_empty_material(self, session, project_service, test_cabinet):
        """Test adding part with empty material string."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Empty Material Part",
            width_mm=500,
            height_mm=400,
            material="",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == ""

    def test_add_part_null_material(self, session, project_service, test_cabinet):
        """Test adding part with None/null material."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Null Material Part",
            width_mm=500,
            height_mm=400,
            material=None,
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material is None

    def test_add_part_numeric_material(self, session, project_service, test_cabinet):
        """Test adding part with numeric string as material."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Numeric Material Part",
            width_mm=500,
            height_mm=400,
            material="12345",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "12345"

    def test_add_part_lowercase_material(self, session, project_service, test_cabinet):
        """Test adding part with lowercase material name."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Lowercase Material Part",
            width_mm=500,
            height_mm=400,
            material="plyta 18",  # lowercase
        )

        # Currently accepted - no case validation
        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].material == "plyta 18"

    def test_add_part_very_long_material(self, session, project_service, test_cabinet):
        """Test adding part with very long material name."""
        long_material = "M" * 100

        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Long Material Part",
            width_mm=500,
            height_mm=400,
            material=long_material,
        )

        # May succeed or fail depending on VARCHAR(32) constraint
        if result:
            session.refresh(test_cabinet)
            # Check if truncated or full value stored


# ============================================================
# QUANTITY VALIDATION TESTS
# ============================================================


class TestQuantityValidation:
    """Test validation of quantity/pieces fields."""

    # ---- Zero Quantity ----

    def test_add_part_zero_pieces(self, session, project_service, test_cabinet):
        """Test adding part with zero pieces."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Zero Pieces Part",
            width_mm=500,
            height_mm=400,
            pieces=0,
        )

        # Currently no validation - zero is accepted
        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].pieces == 0

    def test_cabinet_zero_quantity(self, session, test_project):
        """Test creating cabinet with zero quantity - should be rejected by CHECK constraint."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=1,
            body_color="White",
            front_color="Oak",
            handle_type="Standard",
            quantity=0,
        )
        session.add(cabinet)

        # THEN: Should raise IntegrityError due to CHECK constraint ck_quantity_pos
        with pytest.raises(IntegrityError, match="CHECK constraint failed"):
            session.commit()

    # ---- Negative Quantity ----

    def test_add_part_negative_pieces(self, session, project_service, test_cabinet):
        """Test adding part with negative pieces."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Negative Pieces Part",
            width_mm=500,
            height_mm=400,
            pieces=-5,
        )

        # Currently no validation - negative is accepted
        if result:
            session.refresh(test_cabinet)
            assert test_cabinet.parts[0].pieces == -5

    def test_cabinet_negative_quantity(self, session, test_project):
        """Test creating cabinet with negative quantity - should be rejected by CHECK constraint."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=1,
            body_color="White",
            front_color="Oak",
            handle_type="Standard",
            quantity=-3,
        )
        session.add(cabinet)

        # THEN: Should raise IntegrityError due to CHECK constraint ck_quantity_pos
        with pytest.raises(IntegrityError, match="CHECK constraint failed"):
            session.commit()

    # ---- Very Large Quantity ----

    def test_add_part_very_large_pieces(self, session, project_service, test_cabinet):
        """Test adding part with very large pieces count."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Large Pieces Part",
            width_mm=500,
            height_mm=400,
            pieces=1000000,
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].pieces == 1000000

    def test_cabinet_very_large_quantity(self, session, test_project):
        """Test creating cabinet with very large quantity."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=1,
            body_color="White",
            front_color="Oak",
            handle_type="Standard",
            quantity=999999,
        )
        session.add(cabinet)
        session.commit()

        assert cabinet.quantity == 999999

    # ---- Float Instead of Int ----

    def test_add_part_float_pieces(self, session, project_service, test_cabinet):
        """Test adding part with float pieces (should be int)."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Float Pieces Part",
            width_mm=500,
            height_mm=400,
            pieces=2.5,  # type: ignore  # Intentionally passing float
        )

        # SQLite may convert to int or raise error
        if result:
            session.refresh(test_cabinet)
            # Check what was stored - likely truncated to 2
            assert test_cabinet.parts[0].pieces in [2, 2.5]

    def test_cabinet_float_quantity(self, session, test_project):
        """Test creating cabinet with float quantity."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=1,
            body_color="White",
            front_color="Oak",
            handle_type="Standard",
            quantity=1.7,  # type: ignore  # Intentionally passing float
        )
        session.add(cabinet)
        session.commit()

        # SQLite may convert to int
        assert cabinet.quantity in [1, 2, 1.7]

    # ---- Template Part Pieces ----

    def test_template_part_zero_pieces(self, session, template_service, test_template):
        """Test adding template part with zero pieces."""
        part = template_service.add_part(
            cabinet_type_id=test_template.id,
            part_name="Zero Pieces Template Part",
            height_mm=720,
            width_mm=560,
            pieces=0,
        )

        assert part.pieces == 0

    def test_template_part_negative_pieces(
        self, session, template_service, test_template
    ):
        """Test adding template part with negative pieces - should be rejected by CHECK constraint."""
        # THEN: Should raise IntegrityError due to CHECK constraint ck_part_pieces_nonneg
        with pytest.raises(IntegrityError, match="CHECK constraint failed"):
            template_service.add_part(
                cabinet_type_id=test_template.id,
                part_name="Negative Pieces Template Part",
                height_mm=720,
                width_mm=560,
                pieces=-10,
            )


# ============================================================
# COMBINED VALIDATION TESTS
# ============================================================


class TestCombinedValidation:
    """Test combined validation scenarios."""

    def test_part_all_invalid_values(self, session, project_service, test_cabinet):
        """Test adding part with multiple invalid values at once."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="",  # Empty name
            width_mm=-100,  # Negative
            height_mm=0,  # Zero
            pieces=-5,  # Negative
            material="INVALID",  # Invalid material
        )

        # Currently fails only on empty name
        assert result is False

    def test_part_edge_case_combination(self, session, project_service, test_cabinet):
        """Test part with valid name but edge case dimensions."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="Edge Case Part",
            width_mm=1,  # Minimum valid
            height_mm=1,  # Minimum valid
            pieces=1,
            material="PLYTA 18",
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].width_mm == 1
        assert test_cabinet.parts[0].height_mm == 1

    def test_project_with_invalid_kitchen_type(self, session, project_service):
        """Test creating project with non-standard kitchen type."""
        project = project_service.create_project(
            name="Test Project",
            order_number="KITCHEN-001",
            kitchen_type="NONEXISTENT_TYPE",
        )

        # Currently no validation on kitchen_type
        assert project is not None
        assert project.kitchen_type == "NONEXISTENT_TYPE"

    def test_cabinet_all_empty_strings(self, session, test_project):
        """Test creating cabinet with all empty string fields."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=1,
            body_color="",
            front_color="",
            handle_type="",
            quantity=1,
        )
        session.add(cabinet)
        session.commit()

        assert cabinet.body_color == ""
        assert cabinet.front_color == ""
        assert cabinet.handle_type == ""


# ============================================================
# BOUNDARY VALUE TESTS
# ============================================================


class TestBoundaryValues:
    """Test boundary values for various fields."""

    def test_sequence_number_zero(self, session, test_project):
        """Test cabinet with sequence number zero."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=0,
            body_color="White",
            front_color="Oak",
            handle_type="Standard",
            quantity=1,
        )
        session.add(cabinet)
        session.commit()

        assert cabinet.sequence_number == 0

    def test_sequence_number_negative(self, session, test_project):
        """Test cabinet with negative sequence number."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=-1,
            body_color="White",
            front_color="Oak",
            handle_type="Standard",
            quantity=1,
        )
        session.add(cabinet)
        session.commit()

        assert cabinet.sequence_number == -1

    def test_sequence_number_very_large(self, session, test_project):
        """Test cabinet with very large sequence number."""
        cabinet = ProjectCabinet(
            project_id=test_project.id,
            sequence_number=999999,
            body_color="White",
            front_color="Oak",
            handle_type="Standard",
            quantity=1,
        )
        session.add(cabinet)
        session.commit()

        assert cabinet.sequence_number == 999999

    def test_part_name_single_character(self, session, project_service, test_cabinet):
        """Test part with single character name."""
        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name="A",
            width_mm=500,
            height_mm=400,
        )

        assert result is True
        session.refresh(test_cabinet)
        assert test_cabinet.parts[0].part_name == "A"

    def test_part_name_max_length(self, session, project_service, test_cabinet):
        """Test part with maximum length name."""
        max_name = "X" * 255

        result = project_service.add_part_to_cabinet(
            cabinet_id=test_cabinet.id,
            part_name=max_name,
            width_mm=500,
            height_mm=400,
        )

        assert result is True
        session.refresh(test_cabinet)
        assert len(test_cabinet.parts[0].part_name) == 255
