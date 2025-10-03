"""
Shared test fixtures for all tests in the cabplanner project.

This file provides common fixtures that are automatically available to all test files
in this directory and its subdirectories.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db_schema.orm_models import Base
from src.services.template_service import TemplateService
from src.services.project_service import ProjectService
from src.services.formula_constants_service import FormulaConstantsService
from src.services.settings_service import SettingsService
from src.services.accessory_service import AccessoryService
from src.services.catalog_service import CatalogService


@pytest.fixture(scope="function")
def engine():
    """Create a fresh in-memory SQLite database for each test function."""
    return create_engine("sqlite:///:memory:", future=True)


@pytest.fixture(scope="function", autouse=True)
def prepare_db(engine):
    """Automatically create all database tables for each test function."""
    Base.metadata.create_all(engine)
    yield
    # Cleanup is automatic with in-memory database


@pytest.fixture(scope="function")
def session(engine):
    """Provide a fresh database session for each test function."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# Service fixtures
@pytest.fixture
def template_service(session):
    """Provide TemplateService instance."""
    return TemplateService(session)


@pytest.fixture
def project_service(session):
    """Provide ProjectService instance."""
    return ProjectService(session)


@pytest.fixture
def formula_constants_service(session):
    """Provide FormulaConstantsService instance."""
    return FormulaConstantsService(session)


@pytest.fixture
def settings_service(session):
    """Provide SettingsService instance."""
    return SettingsService(session)


@pytest.fixture
def accessory_service(session):
    """Provide AccessoryService instance."""
    return AccessoryService(session)


@pytest.fixture
def catalog_service(session):
    """Provide CatalogService instance."""
    return CatalogService(session)


@pytest.fixture
def formula_engine(formula_constants_service):
    """Provide FormulaEngine instance."""
    from src.services.formula_engine import FormulaEngine

    return FormulaEngine(formula_constants_service)


# Common test data fixtures
@pytest.fixture
def sample_project(project_service):
    """Create a sample project for testing."""
    return project_service.create_project(name="Test Project", order_number="TEST-001")


@pytest.fixture
def sample_template(template_service):
    """Create a sample cabinet template."""
    return template_service.create_template(kitchen_type="LOFT", nazwa="TestTemplate")


@pytest.fixture
def sample_formula_constants(formula_constants_service):
    """Create sample formula constants for testing."""
    constants = [
        formula_constants_service.set(
            "plyta_thickness", 18.0, "float", "dimensions", "Thickness of board"
        ),
        formula_constants_service.set(
            "hdf_thickness", 3.0, "float", "dimensions", "Thickness of HDF"
        ),
        formula_constants_service.set(
            "base_height", 720.0, "float", "defaults", "Default base cabinet height"
        ),
        formula_constants_service.set(
            "upper_height", 720.0, "float", "defaults", "Default upper cabinet height"
        ),
        formula_constants_service.set(
            "tall_height", 2020.0, "float", "defaults", "Default tall cabinet height"
        ),
        formula_constants_service.set(
            "base_depth", 560.0, "float", "defaults", "Default base cabinet depth"
        ),
        formula_constants_service.set(
            "upper_depth", 300.0, "float", "defaults", "Default upper cabinet depth"
        ),
        formula_constants_service.set(
            "tall_depth", 560.0, "float", "defaults", "Default tall cabinet depth"
        ),
        formula_constants_service.set(
            "front_gap_top", 2.0, "float", "gaps", "Gap at top of front"
        ),
        formula_constants_service.set(
            "front_gap_bottom", 2.0, "float", "gaps", "Gap at bottom of front"
        ),
        formula_constants_service.set(
            "front_gap_side", 2.0, "float", "gaps", "Gap at side of front"
        ),
        formula_constants_service.set(
            "shelf_back_clear", 10.0, "float", "gaps", "Shelf back clearance"
        ),
    ]
    return constants


@pytest.fixture
def sample_settings(settings_service):
    """Create sample settings for testing."""
    settings = [
        settings_service.set_setting("app_name", "CabPlanner", "str"),
        settings_service.set_setting("debug_mode", True, "bool"),
        settings_service.set_setting("max_cabinets", 100, "int"),
        settings_service.set_setting("default_thickness", 18.0, "float"),
        settings_service.set_setting("window_width", 1200, "int"),
        settings_service.set_setting("auto_save", False, "bool"),
    ]
    return settings


@pytest.fixture
def sample_project_cabinets(session, sample_project, template_service):
    """Create sample project cabinets for testing."""
    from src.db_schema.orm_models import ProjectCabinet

    # Create some test templates first
    template1 = template_service.create_template(
        nazwa="TestTemplate1", kitchen_type="MODERN"
    )

    template2 = template_service.create_template(
        nazwa="TestTemplate2", kitchen_type="TRADITIONAL"
    )

    # Create project cabinets
    cabinets = []

    cabinet1 = ProjectCabinet(
        project_id=sample_project.id,
        type_id=template1.id,
        sequence_number=1,
        quantity=2,
        body_color="#ffffff",
        front_color="#000000",
        handle_type="Standard",
    )
    session.add(cabinet1)
    cabinets.append(cabinet1)

    cabinet2 = ProjectCabinet(
        project_id=sample_project.id,
        type_id=template2.id,
        sequence_number=2,
        quantity=1,
        body_color="#f0f0f0",
        front_color="#333333",
        handle_type="Handleless",
    )
    session.add(cabinet2)
    cabinets.append(cabinet2)

    session.commit()
    return cabinets


# Test isolation utilities
@pytest.fixture(autouse=True)
def isolate_tests(session):
    """Ensure test isolation by rolling back after each test."""
    yield
    session.rollback()
