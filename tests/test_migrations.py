import os
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from alembic import command
from alembic.config import Config

from src.db_schema.orm_models import Base


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
    # WHEN
    command.upgrade(alembic_cfg, "head")

    # GIVEN
    engine = create_engine(f"sqlite:///{temp_db_path}")
    with engine.connect() as conn:
        metadata = sa.MetaData()
        metadata.reflect(bind=conn)

    # THEN
    model_tables = set(Base.metadata.tables.keys())
    db_tables = set(metadata.tables.keys())
    db_tables.discard("alembic_version")

    assert model_tables == db_tables, (
        f"Mismatch between models and DB tables:\n"
        f"Only in models: {model_tables - db_tables}\n"
        f"Only in DB: {db_tables - model_tables}"
    )
