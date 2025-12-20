from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db_schema.orm_models import (
    CabinetTemplate,
    CabinetPart,
    CabinetTemplateAccessory,
    Accessory,
)


class TemplateService:
    def __init__(self, db_session: Session):
        self.db = db_session

    # Templates
    def list_templates(
        self, kitchen_type: Optional[str] = None
    ) -> List[CabinetTemplate]:
        stmt = select(CabinetTemplate)
        if kitchen_type:
            stmt = stmt.filter_by(kitchen_type=kitchen_type)
        return list(self.db.scalars(stmt).all())

    def get_template(self, template_id: int) -> Optional[CabinetTemplate]:
        return self.db.get(CabinetTemplate, template_id)

    def create_template(self, *, kitchen_type: str, name: str) -> CabinetTemplate:
        tpl = CabinetTemplate(kitchen_type=kitchen_type, name=name)
        self.db.add(tpl)
        try:
            self.db.commit()
            self.db.refresh(tpl)
            return tpl
        except IntegrityError as e:
            self.db.rollback()
            # Handle specific constraint violations
            if "UNIQUE constraint failed: cabinet_types.name" in str(e):
                raise ValueError(
                    f"Typ szafki o nazwie '{name}' już istnieje. Wybierz inną nazwę."
                )
            elif "UNIQUE constraint failed" in str(e):
                raise ValueError(
                    "Wystąpił błąd unikalności danych. Sprawdź wprowadzone wartości."
                )
            else:
                raise ValueError(f"Błąd bazy danych: {str(e)}")

    def delete_template(self, template_id: int) -> bool:
        tpl = self.get_template(template_id)
        if not tpl:
            return False
        self.db.delete(tpl)
        self.db.commit()
        return True

    def update_template(self, template_id: int, **fields) -> Optional[CabinetTemplate]:
        tpl = self.get_template(template_id)
        if not tpl:
            return None
        for k, v in fields.items():
            setattr(tpl, k, v)
        try:
            self.db.commit()
            self.db.refresh(tpl)
            return tpl
        except IntegrityError as e:
            self.db.rollback()
            # Handle specific constraint violations
            if "UNIQUE constraint failed: cabinet_types.name" in str(e):
                raise ValueError(
                    f"Typ szafki o nazwie '{fields.get('name', '')}' już istnieje. Wybierz inną nazwę."
                )
            elif "UNIQUE constraint failed" in str(e):
                raise ValueError(
                    "Wystąpił błąd unikalności danych. Sprawdź wprowadzone wartości."
                )
            else:
                raise ValueError(f"Błąd bazy danych: {str(e)}")

    # Parts
    def add_part(
        self,
        *,
        cabinet_type_id: int,
        part_name: str,
        height_mm: int,
        width_mm: int,
        pieces: int = 1,
        material: Optional[str] = None,
        wrapping: Optional[str] = None,
        comments: Optional[str] = None,
    ) -> CabinetPart:
        part = CabinetPart(
            cabinet_type_id=cabinet_type_id,
            part_name=part_name,
            height_mm=height_mm,
            width_mm=width_mm,
            pieces=pieces,
            material=material,
            wrapping=wrapping,
            comments=comments,
        )
        self.db.add(part)
        self.db.commit()
        self.db.refresh(part)
        return part

    def list_parts(self, cabinet_type_id: int) -> List[CabinetPart]:
        stmt = select(CabinetPart).filter(
            CabinetPart.cabinet_type_id == cabinet_type_id
        )
        return list(self.db.scalars(stmt).all())

    def delete_part(self, part_id: int) -> bool:
        part = self.db.get(CabinetPart, part_id)
        if not part:
            return False
        self.db.delete(part)
        self.db.commit()
        return True

    # Accessories
    def add_accessory(
        self,
        *,
        cabinet_type_id: int,
        accessory_id: int,
        count: int = 1,
    ) -> CabinetTemplateAccessory:
        """Add an accessory link to a cabinet template."""
        link = CabinetTemplateAccessory(
            cabinet_type_id=cabinet_type_id,
            accessory_id=accessory_id,
            count=count,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def add_accessory_by_name(
        self,
        *,
        cabinet_type_id: int,
        name: str,
        unit: str = "szt",
        count: int = 1,
    ) -> CabinetTemplateAccessory:
        """
        Add an accessory to a cabinet template by name.
        Creates the accessory if it doesn't exist.
        """
        # Find or create accessory
        stmt = select(Accessory).filter_by(name=name)
        accessory = self.db.scalars(stmt).first()
        if not accessory:
            accessory = Accessory(name=name, unit=unit)
            self.db.add(accessory)
            self.db.flush()

        # Check if link already exists
        existing_link = self.db.get(
            CabinetTemplateAccessory, (cabinet_type_id, accessory.id)
        )
        if existing_link:
            # Update count if link exists
            existing_link.count = count
            self.db.commit()
            self.db.refresh(existing_link)
            return existing_link

        # Create new link
        link = CabinetTemplateAccessory(
            cabinet_type_id=cabinet_type_id,
            accessory_id=accessory.id,
            count=count,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def list_accessories(self, cabinet_type_id: int) -> List[CabinetTemplateAccessory]:
        """List all accessories linked to a cabinet template."""
        stmt = select(CabinetTemplateAccessory).filter(
            CabinetTemplateAccessory.cabinet_type_id == cabinet_type_id
        )
        return list(self.db.scalars(stmt).all())

    def delete_accessory(self, cabinet_type_id: int, accessory_id: int) -> bool:
        """Remove an accessory link from a cabinet template."""
        link = self.db.get(CabinetTemplateAccessory, (cabinet_type_id, accessory_id))
        if not link:
            return False
        self.db.delete(link)
        self.db.commit()
        return True
