from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db_schema.orm_models import Project, ProjectCabinet


class ProjectService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def list_projects(self) -> List[Project]:
        stmt = select(Project).order_by(Project.created_at)
        return list(self.db.scalars(stmt).all())

    def get_project(self, project_id: int) -> Optional[Project]:
        return self.db.get(Project, project_id)

    def create_project(self, **fields) -> Project:
        project = Project(**fields)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update_project(self, project_id: int, **fields) -> Optional[Project]:
        project = self.get_project(project_id)
        if not project:
            return None
        for attr, val in fields.items():
            setattr(project, attr, val)
        project.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        self.db.delete(project)
        self.db.commit()
        return True

    def list_cabinets(self, project_id: int) -> List[ProjectCabinet]:
        stmt = (
            select(ProjectCabinet)
            .filter_by(project_id=project_id)
            .order_by(ProjectCabinet.sequence_number)
        )
        return list(self.db.scalars(stmt).all())

    def get_cabinet(self, cabinet_id: int) -> Optional[ProjectCabinet]:
        return self.db.get(ProjectCabinet, cabinet_id)

    def add_cabinet(
        self,
        project_id: int,
        *,
        sequence_number: int,
        type_id: Optional[int],
        body_color: str,
        front_color: str,
        handle_type: str,
        quantity: int = 1,
        adhoc_width_mm: Optional[float] = None,
        adhoc_height_mm: Optional[float] = None,
        adhoc_depth_mm: Optional[float] = None,
        formula_offset_mm: Optional[float] = None,
    ) -> ProjectCabinet:
        cab = ProjectCabinet(
            project_id=project_id,
            sequence_number=sequence_number,
            type_id=type_id,
            body_color=body_color,
            front_color=front_color,
            handle_type=handle_type,
            quantity=quantity,
            adhoc_width_mm=adhoc_width_mm,
            adhoc_height_mm=adhoc_height_mm,
            adhoc_depth_mm=adhoc_depth_mm,
            formula_offset_mm=formula_offset_mm,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(cab)
        self.db.commit()
        self.db.refresh(cab)
        return cab

    def update_cabinet(self, cabinet_id: int, **fields) -> Optional[ProjectCabinet]:
        cab = self.get_cabinet(cabinet_id)
        if not cab:
            return None
        for attr, val in fields.items():
            setattr(cab, attr, val)
        cab.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(cab)
        return cab

    def delete_cabinet(self, cabinet_id: int) -> bool:
        cab = self.get_cabinet(cabinet_id)
        if not cab:
            return False
        self.db.delete(cab)
        self.db.commit()
        return True

    def get_next_cabinet_sequence(self, project_id: int) -> int:
        current_max = (
            self.db
            .scalar(
                select(func.max(ProjectCabinet.sequence_number))
                .filter_by(project_id=project_id)
            )
            or 0
        )
        return current_max + 1
