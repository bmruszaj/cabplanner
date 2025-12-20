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

    def update_template_name(self, template_id: int, new_name: str) -> bool:
        """Update the name of a cabinet template."""
        tpl = self.get_template(template_id)
        if not tpl:
            return False
        tpl.name = new_name
        try:
            self.db.commit()
            return True
        except IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(
                    f"Typ szafki o nazwie '{new_name}' już istnieje. Wybierz inną nazwę."
                )
            raise ValueError(f"Błąd bazy danych: {str(e)}")

    def duplicate_template(self, template_id: int) -> Optional[CabinetTemplate]:
        """
        Duplicate a cabinet template with all its parts and accessories.

        Creates a copy with a unique name (adds " (kopia)" suffix).

        Args:
            template_id: ID of the template to duplicate

        Returns:
            The newly created template, or None if source template not found
        """
        source = self.get_template(template_id)
        if not source:
            return None

        # Generate unique name
        base_name = source.name
        new_name = f"{base_name} (kopia)"

        # Check if name exists and add number if needed
        counter = 1
        while True:
            existing = self.db.scalar(
                select(CabinetTemplate).where(CabinetTemplate.name == new_name)
            )
            if not existing:
                break
            counter += 1
            new_name = f"{base_name} (kopia {counter})"

        # Create new template
        new_template = CabinetTemplate(
            kitchen_type=source.kitchen_type,
            name=new_name,
        )
        self.db.add(new_template)
        self.db.flush()  # Get the ID

        # Duplicate all parts
        for part in source.parts:
            new_part = CabinetPart(
                cabinet_type_id=new_template.id,
                part_name=part.part_name,
                height_mm=part.height_mm,
                width_mm=part.width_mm,
                pieces=part.pieces,
                material=part.material,
                wrapping=part.wrapping,
                comments=part.comments,
                processing_json=part.processing_json,
            )
            self.db.add(new_part)

        # Duplicate all accessory links
        for acc_link in source.accessories:
            new_link = CabinetTemplateAccessory(
                cabinet_type_id=new_template.id,
                accessory_id=acc_link.accessory_id,
                count=acc_link.count,
            )
            self.db.add(new_link)

        self.db.commit()
        self.db.refresh(new_template)
        return new_template

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

    def update_part(self, part_id: int, **kwargs) -> Optional[CabinetPart]:
        """Update a cabinet part."""
        part = self.db.get(CabinetPart, part_id)
        if not part:
            return None
        for key, value in kwargs.items():
            if hasattr(part, key):
                setattr(part, key, value)
        self.db.commit()
        self.db.refresh(part)
        return part

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
