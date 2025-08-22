import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.db_migration import upgrade_database

logger = logging.getLogger(__name__)


def ensure_db_and_migrate(base: Path) -> Path:
    """Ensure database file exists and run migrations."""
    # Ensure database file exists
    db_path = base / "cabplanner.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Using database at: %s", db_path)

    # Run migrations
    logger.info("Upgrading database schema (Alembic)...")
    upgrade_database(db_path)

    return db_path


def create_session(db_path: Path) -> Session:
    """Create and return a SQLAlchemy session."""
    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
