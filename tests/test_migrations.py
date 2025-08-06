import os
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, inspect
from alembic import command
from alembic.config import Config

from src.db_schema.orm_models import Base
from src.db_migration import upgrade_database  # your helper

# The set of tables we expect after a full migration
EXPECTED_TABLES = set(Base.metadata.tables.keys()) | {"alembic_version"}


def get_alembic_config(db_url: str) -> Config:
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    )
    config = Config(config_path)
    config.set_main_option("sqlalchemy.url", db_url)
    return config


@pytest.fixture(scope="function")
def temp_db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture(scope="function")
def alembic_cfg(temp_db_path):
    return get_alembic_config(f"sqlite:///{temp_db_path}")


def test_alembic_upgrade_and_schema_match(alembic_cfg, temp_db_path):
    # WHEN: run all migrations via alembic.command
    command.upgrade(alembic_cfg, "head")

    # GIVEN: reflect the schema from the migrated DB
    engine = create_engine(f"sqlite:///{temp_db_path}")
    with engine.connect() as conn:
        metadata = sa.MetaData()
        metadata.reflect(bind=conn)

    # THEN: only our model tables, no extras (ignore alembic_version)
    model_tables = set(Base.metadata.tables.keys())
    db_tables = set(metadata.tables.keys())
    db_tables.discard("alembic_version")

    assert model_tables == db_tables, (
        f"Mismatch between models and DB tables:\n"
        f"Only in models: {model_tables - db_tables}\n"
        f"Only in DB: {db_tables - model_tables}"
    )


def test_upgrade_database_creates_all_tables(temp_db_path):
    # GIVEN a fresh (non-existent) DB
    if temp_db_path.exists():
        temp_db_path.unlink()

    # WHEN we call our helper
    upgrade_database(temp_db_path)

    # THEN all expected tables are present
    engine = create_engine(f"sqlite:///{temp_db_path}")
    tables = set(inspect(engine).get_table_names())
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Missing tables after upgrade_database(): {missing}"


def test_upgrade_database_idempotent(temp_db_path):
    # GIVEN a DB already migrated once
    upgrade_database(temp_db_path)

    # WHEN we call it again
    upgrade_database(temp_db_path)

    # THEN it still has at least the expected tables and raises no errors
    engine = create_engine(f"sqlite:///{temp_db_path}")
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES <= tables
