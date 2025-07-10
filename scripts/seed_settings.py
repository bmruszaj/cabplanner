from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.db_schema.orm_models import Setting

engine = create_engine("sqlite:///../cabplanner.db", echo=False)


def seed_settings():
    with Session(engine) as session:
        exists = session.query(Setting).first()
        if not exists:
            s = Setting(
                base_formula_offset_mm=-2.0,
                autoupdate_interval="weekly",
                current_version="0.1.0",
            )
            session.add(s)
            session.commit()
            print("✅ Seeded default settings row.")
        else:
            print("⚠️ Settings row already exists, skipping.")


if __name__ == "__main__":
    seed_settings()
