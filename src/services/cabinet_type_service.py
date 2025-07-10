from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db_schema.orm_models import CabinetType


class CabinetTypeService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def list_cabinet_types(self, kitchen_type: Optional[str] = None) -> List[CabinetType]:
        stmt = select(CabinetType)
        if kitchen_type is not None:
            stmt = stmt.filter_by(kitchen_type=kitchen_type)
        results = self.db.scalars(stmt).all()
        return list(results)

    def get_cabinet_type(self, type_id: int) -> Optional[CabinetType]:
        return self.db.get(CabinetType, type_id)

    def create_cabinet_type(
        self,
        kitchen_type: str,
        nazwa: str,
        hdf_plecy: bool = False,
        listwa_count: int = 0,
        listwa_w_mm: Optional[float] = None,
        listwa_h_mm: Optional[float] = None,
        wieniec_count: int = 0,
        wieniec_w_mm: Optional[float] = None,
        wieniec_h_mm: Optional[float] = None,
        bok_count: int = 0,
        bok_w_mm: Optional[float] = None,
        bok_h_mm: Optional[float] = None,
        front_count: int = 0,
        front_w_mm: Optional[float] = None,
        front_h_mm: Optional[float] = None,
        polka_count: int = 0,
        polka_w_mm: Optional[float] = None,
        polka_h_mm: Optional[float] = None,
    ) -> CabinetType:
        ctype = CabinetType(
            kitchen_type=kitchen_type,
            nazwa=nazwa,
            hdf_plecy=hdf_plecy,
            listwa_count=listwa_count,
            listwa_w_mm=listwa_w_mm,
            listwa_h_mm=listwa_h_mm,
            wieniec_count=wieniec_count,
            wieniec_w_mm=wieniec_w_mm,
            wieniec_h_mm=wieniec_h_mm,
            bok_count=bok_count,
            bok_w_mm=bok_w_mm,
            bok_h_mm=bok_h_mm,
            front_count=front_count,
            front_w_mm=front_w_mm,
            front_h_mm=front_h_mm,
            polka_count=polka_count,
            polka_w_mm=polka_w_mm,
            polka_h_mm=polka_h_mm,
            # created_at and updated_at will use model defaults
        )
        self.db.add(ctype)
        self.db.commit()
        self.db.refresh(ctype)
        return ctype

    def update_cabinet_type(self, type_id: int, **fields) -> Optional[CabinetType]:
        ctype = self.get_cabinet_type(type_id)
        if not ctype:
            return None
        for attr, val in fields.items():
            setattr(ctype, attr, val)
        ctype.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(ctype)
        return ctype

    def delete_cabinet_type(self, type_id: int) -> bool:
        ctype = self.get_cabinet_type(type_id)
        if not ctype:
            return False
        self.db.delete(ctype)
        self.db.commit()
        return True
