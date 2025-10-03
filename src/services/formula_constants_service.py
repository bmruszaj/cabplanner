from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db_schema.orm_models import FormulaConstant


class FormulaConstantsService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def list_constants(self, group: Optional[str] = None) -> List[FormulaConstant]:
        stmt = select(FormulaConstant)
        if group:
            stmt = stmt.filter_by(group=group)
        return list(self.db.scalars(stmt).all())

    def get(self, key: str) -> Optional[FormulaConstant]:
        stmt = select(FormulaConstant).filter_by(key=key)
        return self.db.scalars(stmt).first()

    def set(
        self,
        key: str,
        value: float,
        type: str = "float",
        group: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FormulaConstant:
        fc = self.get(key)
        if fc is None:
            fc = FormulaConstant(
                key=key, value=value, type=type, group=group, description=description
            )
            self.db.add(fc)
        else:
            fc.value = value
            fc.type = type
            fc.group = group
            fc.description = description
        self.db.commit()
        self.db.refresh(fc)
        return fc
