from __future__ import annotations

from typing import Optional, List, Dict, Any

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

    def save_template_editor_changes(
        self,
        template_id: int,
        *,
        new_name: Optional[str] = None,
        parts_changes: Optional[Dict[str, Any]] = None,
        accessories_changes: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Persist template editor changes atomically in a single transaction.

        This method is used by CabinetEditorDialog to avoid partial saves when
        one section succeeds and another fails.
        """
        template = self.get_template(template_id)
        if not template:
            return False

        def _require_positive(value: Any) -> int:
            count = int(value)
            if count <= 0:
                raise ValueError("Count must be positive")
            return count

        try:
            if new_name is not None:
                cleaned_name = new_name.strip()
                if not cleaned_name:
                    raise ValueError("Nazwa szafki jest wymagana.")
                template.name = cleaned_name

            if parts_changes is not None:
                for part_id in parts_changes.get("parts_to_remove", []):
                    part = self.db.get(CabinetPart, int(part_id))
                    if not part or part.cabinet_type_id != template_id:
                        raise ValueError("Invalid part removal request")
                    self.db.delete(part)

                for part_id, part_data in parts_changes.get(
                    "parts_changes", {}
                ).items():
                    part = self.db.get(CabinetPart, int(part_id))
                    if not part or part.cabinet_type_id != template_id:
                        raise ValueError("Invalid part update request")
                    for key, value in part_data.items():
                        if hasattr(part, key):
                            setattr(part, key, value)

                for part_data in parts_changes.get("parts_to_add", []):
                    self.db.add(
                        CabinetPart(
                            cabinet_type_id=template_id,
                            part_name=part_data.get("part_name", ""),
                            height_mm=part_data.get("height_mm", 0),
                            width_mm=part_data.get("width_mm", 0),
                            pieces=part_data.get("pieces", 1),
                            material=part_data.get("material"),
                            wrapping=part_data.get("wrapping"),
                            comments=part_data.get("comments"),
                            processing_json=part_data.get("processing_json"),
                        )
                    )

            if accessories_changes is not None:
                for acc_data in accessories_changes.get("accessories_to_add", []):
                    cleaned_name = (acc_data.get("name", "") or "").strip()
                    if not cleaned_name:
                        raise ValueError("Nazwa akcesorium jest wymagana.")
                    target_count = _require_positive(acc_data.get("count", 1))

                    accessory = self.db.scalar(
                        select(Accessory).where(Accessory.name == cleaned_name)
                    )
                    if not accessory:
                        accessory = Accessory(name=cleaned_name)
                        self.db.add(accessory)
                        self.db.flush()

                    existing_link = self.db.get(
                        CabinetTemplateAccessory, (template_id, accessory.id)
                    )
                    if existing_link:
                        existing_link.count = target_count
                    else:
                        self.db.add(
                            CabinetTemplateAccessory(
                                cabinet_type_id=template_id,
                                accessory_id=accessory.id,
                                count=target_count,
                            )
                        )

                for acc_id in accessories_changes.get("accessories_to_remove", []):
                    link = self.db.get(
                        CabinetTemplateAccessory, (template_id, int(acc_id))
                    )
                    if not link:
                        raise ValueError("Invalid accessory removal request")
                    self.db.delete(link)

                for acc_id, update_data in accessories_changes.get(
                    "accessories_changes", {}
                ).items():
                    current_accessory_id = int(acc_id)
                    link = self.db.get(
                        CabinetTemplateAccessory, (template_id, current_accessory_id)
                    )
                    if not link:
                        raise ValueError("Invalid accessory update request")

                    target_accessory_id = current_accessory_id
                    target_count = _require_positive(
                        update_data.get("count", link.count)
                    )

                    if "name" in update_data and update_data.get("name") is not None:
                        cleaned_name = update_data.get("name", "").strip()
                        if not cleaned_name:
                            raise ValueError("Nazwa akcesorium jest wymagana.")

                        accessory = self.db.scalar(
                            select(Accessory).where(Accessory.name == cleaned_name)
                        )
                        if not accessory:
                            accessory = Accessory(name=cleaned_name)
                            self.db.add(accessory)
                            self.db.flush()
                        target_accessory_id = accessory.id

                    if target_accessory_id == current_accessory_id:
                        link.count = target_count
                    else:
                        existing_target = self.db.get(
                            CabinetTemplateAccessory, (template_id, target_accessory_id)
                        )
                        if existing_target:
                            existing_target.count = target_count
                        else:
                            self.db.add(
                                CabinetTemplateAccessory(
                                    cabinet_type_id=template_id,
                                    accessory_id=target_accessory_id,
                                    count=target_count,
                                )
                            )
                        self.db.delete(link)

            self.db.commit()
            self.db.refresh(template)
            return True
        except IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(
                    f"Typ szafki o nazwie '{new_name or template.name}' już istnieje. Wybierz inną nazwę."
                )
            raise ValueError(f"Błąd bazy danych: {str(e)}")
        except ValueError:
            self.db.rollback()
            return False
        except Exception:
            self.db.rollback()
            return False

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
            accessory = Accessory(name=name)
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

    def update_accessory(
        self,
        *,
        cabinet_type_id: int,
        accessory_id: int,
        name: Optional[str] = None,
        count: Optional[int] = None,
    ) -> bool:
        """Update accessory link in a cabinet template (name and/or count)."""
        link = self.db.get(CabinetTemplateAccessory, (cabinet_type_id, accessory_id))
        if not link:
            return False

        target_accessory_id = link.accessory_id
        target_count = count if count is not None else link.count

        if target_count <= 0:
            return False

        if name is not None:
            cleaned_name = name.strip()
            if not cleaned_name:
                return False

            accessory = self.db.scalar(
                select(Accessory).where(Accessory.name == cleaned_name)
            )
            if not accessory:
                accessory = Accessory(name=cleaned_name)
                self.db.add(accessory)
                self.db.flush()

            target_accessory_id = accessory.id

        try:
            if target_accessory_id == link.accessory_id:
                link.count = target_count
            else:
                existing_target = self.db.get(
                    CabinetTemplateAccessory, (cabinet_type_id, target_accessory_id)
                )
                if existing_target:
                    existing_target.count = target_count
                else:
                    new_link = CabinetTemplateAccessory(
                        cabinet_type_id=cabinet_type_id,
                        accessory_id=target_accessory_id,
                        count=target_count,
                    )
                    self.db.add(new_link)

                self.db.delete(link)

            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
