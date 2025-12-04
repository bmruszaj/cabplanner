import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.db_migration import upgrade_database, IncompatibleDatabaseError, check_database_compatibility

logger = logging.getLogger(__name__)


def handle_incompatible_database(db_path: Path, reason: str) -> bool:
    """
    Show dialog asking user to delete incompatible database.
    Returns True if user confirmed deletion and database was deleted.
    """
    from PySide6.QtWidgets import QMessageBox, QApplication
    
    # Ensure we have a QApplication
    app = QApplication.instance()
    if app is None:
        return False
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Niekompatybilna baza danych")
    msg.setText("Wykryto niekompatybilną bazę danych")
    msg.setInformativeText(
        f"{reason}\n\n"
        f"Lokalizacja: {db_path}\n\n"
        "Czy chcesz usunąć starą bazę danych i rozpocząć od nowa?\n\n"
        "UWAGA: Wszystkie zapisane projekty i ustawienia zostaną utracone!"
    )
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    msg.button(QMessageBox.Yes).setText("Usuń i kontynuuj")
    msg.button(QMessageBox.No).setText("Anuluj")
    
    if msg.exec() == QMessageBox.Yes:
        try:
            db_path.unlink()
            logger.info("User confirmed deletion of incompatible database: %s", db_path)
            return True
        except Exception as e:
            logger.error("Failed to delete database: %s", e)
            QMessageBox.critical(
                None,
                "Błąd",
                f"Nie udało się usunąć bazy danych:\n{e}"
            )
            return False
    else:
        logger.info("User declined to delete incompatible database")
        return False


def ensure_db_and_migrate(base: Path) -> tuple[Path, bool]:
    """Ensure database file exists and run migrations. Returns (db_path, is_first_run)."""
    db_path = base / "cabplanner.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    is_first_run = not db_path.exists()
    logger.info("Using database at: %s", db_path)

    logger.info("Upgrading database schema (Alembic)...")
    
    try:
        upgrade_database(db_path)
    except IncompatibleDatabaseError as e:
        logger.warning("Incompatible database detected: %s", e)
        if handle_incompatible_database(e.db_path, str(e)):
            # User deleted old database, try again
            is_first_run = True
            upgrade_database(db_path)
        else:
            # User declined, exit application
            raise SystemExit("Nie można kontynuować z niekompatybilną bazą danych")

    return db_path, is_first_run


def create_session(db_path: Path) -> Session:
    """Create and return a SQLAlchemy session."""
    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def seed_cabinet_templates_if_first_run(session: Session, base: Path) -> None:
    """Execute seed SQL files only on first run. SQL files handle duplicate prevention logic."""
    try:
        # Check if we already have cabinet types in the database
        from src.db_schema.orm_models import CabinetTemplate

        existing_count = session.query(CabinetTemplate).count()

        if existing_count > 0:
            logger.info(
                "Cabinet templates already exist in database (%d found), skipping seed",
                existing_count,
            )
            return

        logger.info("No cabinet templates found, running seed SQL files...")

        seed_dir_candidates = [
            base / "src" / "db_schema",
            base / "db_schema",
            Path(__file__).resolve().parents[1] / "db_schema",
        ]
        seed_dir = next((path for path in seed_dir_candidates if path.exists()), None)

        if seed_dir is None:
            logger.error(
                "Unable to locate seed SQL directory. Checked: %s",
                ", ".join(str(p) for p in seed_dir_candidates),
            )
            return

        seed_files = [
            seed_dir / "seed_cabinet_templates.sql",
            seed_dir / "seed_cabinets_formulas.sql",
            seed_dir / "seed_formula_constants.sql",
        ]
        connection = session.connection()
        for sql_path in seed_files:
            if not sql_path.exists():
                logger.warning("Seed SQL not found at %s; skipping", sql_path)
                continue
            sql = sql_path.read_text(encoding="utf-8")
            # Execute as a single script split by semicolons (SQLite DB-API executes one statement at a time)
            for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
                connection.execute(text(stmt))
        session.commit()
        logger.info("Executed seed SQL files successfully")
    except Exception:
        logger.exception("Error executing seed SQL")
