from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db_schema.orm_models import Accessory


class AccessoryService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def list_accessories(self) -> List[Accessory]:
        stmt = select(Accessory)
        results = self.db.scalars(stmt).all()
        return list(results)

    def get_accessory(self, accessory_id: int) -> Optional[Accessory]:
        return self.db.get(Accessory, accessory_id)

    def find_by_name(self, name: str) -> Optional[Accessory]:
        """Find an accessory by its name."""
        stmt = select(Accessory).filter_by(name=name)
        return self.db.scalars(stmt).first()

    def create_accessory(self, name: str, unit: str = "szt") -> Accessory:
        """Create a new accessory with name and unit (szt or kpl)."""
        accessory = Accessory(name=name, unit=unit)
        self.db.add(accessory)
        self.db.commit()
        self.db.refresh(accessory)
        return accessory

    def update_accessory(self, accessory_id: int, **fields) -> Optional[Accessory]:
        accessory = self.get_accessory(accessory_id)
        if not accessory:
            return None
        for attr, val in fields.items():
            setattr(accessory, attr, val)
        accessory.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(accessory)
        return accessory

    def delete_accessory(self, accessory_id: int) -> bool:
        accessory = self.get_accessory(accessory_id)
        if not accessory:
            return False
        self.db.delete(accessory)
        self.db.commit()
        return True

    def get_or_create(self, name: str, unit: str = "szt") -> Accessory:
        """
        Find an existing Accessory by name, or create a new one if not found.
        Useful for inline add/find within project workflows.
        """
        accessory = self.find_by_name(name)
        if accessory:
            return accessory
        return self.create_accessory(name=name, unit=unit)
