# scripts/seed_settings.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.db_schema.orm_models import Setting, Base

engine = create_engine("sqlite:///../cabplanner.db", echo=False)
Base.metadata.bind = engine


def seed_settings():
    with Session(engine) as session:
        exists = session.query(Setting).first()
        if not exists:
            s = Setting(
                values={},  # optional config blob
                current_version="0.0.1",
                autoupdate_enabled=False,
                autoupdate_interval_days=7,
                formula_script=None,
                logo_path=None,
            )
            session.add(s)
            session.commit()
            print("✅ Seeded default settings row.")
        else:
            print("⚠️  Settings row already exists, skipping.")


if __name__ == "__main__":
    seed_settings()
