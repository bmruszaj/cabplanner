from pathlib import Path
import logging

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


class IncompatibleDatabaseError(Exception):
    """Raised when database schema is incompatible with current migrations."""

    def __init__(self, message: str, db_path: Path):
        super().__init__(message)
        self.db_path = db_path


def get_alembic_config(db_path: Path) -> Config:
    """Get Alembic config pointing to the given database."""
    ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    config = Config(str(ini_path))
    db_url = f"sqlite:///{db_path}"
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def check_database_compatibility(db_path: Path) -> tuple[bool, str]:
    """
    Check if the existing database is compatible with current migrations.

    Returns:
        (is_compatible, reason) - True if compatible or no database exists
    """
    if not db_path.exists():
        return True, "No database exists yet"

    engine = None
    try:
        config = get_alembic_config(db_path)
        script = ScriptDirectory.from_config(config)

        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
                )
            )
            if not result.fetchone():
                # Old database without Alembic - incompatible
                return (
                    False,
                    "Baza danych pochodzi ze starej wersji aplikacji (brak tabeli migracji)",
                )

            # Get current revision from database
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

            if current_rev is None:
                return False, "Baza danych nie ma zapisanej wersji schematu"

            # Check if the current revision exists in our scripts
            try:
                script.get_revision(current_rev)
            except Exception:
                return (
                    False,
                    f"Wersja schematu bazy ({current_rev[:8]}...) nie jest zgodna z aktualną wersją aplikacji",
                )

            # Check if cabinet_types table has the correct schema (name column instead of nazwa)
            result = conn.execute(text("PRAGMA table_info(cabinet_types)"))
            columns = {row[1] for row in result.fetchall()}

            if "nazwa" in columns and "name" not in columns:
                return (
                    False,
                    "Schemat bazy danych jest nieaktualny (kolumna 'nazwa' zamiast 'name')",
                )

        return True, "Database is compatible"

    except Exception as e:
        logger.warning(f"Error checking database compatibility: {e}")
        return False, f"Nie można zweryfikować bazy danych: {e}"

    finally:
        # Ensure engine is disposed to release file lock
        if engine is not None:
            engine.dispose()


def upgrade_database(db_path: Path) -> None:
    """
    Run Alembic migrations to bring the SQLite database at db_path up to date.
    Raises IncompatibleDatabaseError if migration cannot proceed.
    """
    # Check compatibility first
    is_compatible, reason = check_database_compatibility(db_path)
    if not is_compatible:
        raise IncompatibleDatabaseError(reason, db_path)

    config = get_alembic_config(db_path)

    # Apply all migrations
    command.upgrade(config, "head")
