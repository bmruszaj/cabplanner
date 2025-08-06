from pathlib import Path

from alembic.config import Config
from alembic import command


def upgrade_database(db_path: Path) -> None:
    """
    Run Alembic migrations to bring the SQLite database at db_path up to date.
    """
    # Locate the alembic.ini (assumed at project root next to main_app.py)
    ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    config = Config(str(ini_path))

    # Override the sqlalchemy.url so Alembic points at our SQLite file
    db_url = f"sqlite:///{db_path}"
    config.set_main_option("sqlalchemy.url", db_url)

    # Apply all migrations
    command.upgrade(config, "head")
