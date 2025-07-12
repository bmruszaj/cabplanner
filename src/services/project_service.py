from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db_schema.orm_models import Project, ProjectCabinet


def get_circled_number(n: int) -> str:
    if 1 <= n <= 20:
        return chr(9311 + n)
    return f"({n})"


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
            self.db.scalar(
                select(func.max(ProjectCabinet.sequence_number)).filter_by(
                    project_id=project_id
                )
            )
            or 0
        )
        return current_max + 1

    def get_aggregated_project_elements(self, project_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all elements in a project, preserving each individual cabinet and its sequence number.
        Returns a dictionary with lists for formatki, fronty, hdf, and akcesoria.
        """
        project = self.get_project(project_id)
        if not project:
            return {
                "formatki": [],
                "fronty": [],
                "hdf": [],
                "akcesoria": []
            }

        formatki = []
        fronty = []
        hdf = []
        akcesoria = []

        for cab in project.cabinets:
            ct = cab.cabinet_type
            qty = cab.quantity
            seq = cab.sequence_number  # Keep sequence number for reference
            seq_symbol = get_circled_number(seq)

            # Handle standard catalog cabinets
            if ct:
                self._process_catalog_cabinet(cab, ct, qty, seq, seq_symbol, formatki, fronty, hdf)
            # Handle ad-hoc cabinets
            elif cab.adhoc_width_mm and cab.adhoc_height_mm and cab.adhoc_depth_mm:
                self._process_adhoc_cabinet(cab, qty, seq, seq_symbol, formatki, fronty, hdf)

            # Process accessories for all cabinet types
            self._process_accessories(cab, qty, seq, seq_symbol, akcesoria)

        return {
            "formatki": formatki,
            "fronty": fronty,
            "hdf": hdf,
            "akcesoria": akcesoria
        }

    def _process_catalog_cabinet(
        self, cab, ct, qty, seq, seq_symbol, formatki, fronty, hdf
    ):
        """Process elements from a catalog cabinet, preserving individual cabinet identity"""
        # Process panels (formatki)
        for attr, name in [
            ("bok", "Bok"),
            ("wieniec", "Wieniec"),
            ("polka", "Półka"),
            ("listwa", "Listwa"),
        ]:
            count = getattr(ct, f"{attr}_count", 0) or 0
            width = getattr(ct, f"{attr}_w_mm", None)
            height = getattr(ct, f"{attr}_h_mm", None)
            if count > 0 and width and height:
                formatki.append({
                    "seq": seq_symbol,
                    "name": name,
                    "quantity": count * qty,
                    "width": int(width),
                    "height": int(height),
                    "color": cab.body_color,
                    "notes": ""
                })

        # Process fronts
        fcount = getattr(ct, "front_count", 0) or 0
        fw = getattr(ct, "front_w_mm", None)
        fh = getattr(ct, "front_h_mm", None)
        if fcount > 0 and fw and fh:
            fronty.append({
                "seq": seq_symbol,
                "name": "Front",
                "quantity": fcount * qty,
                "width": int(fw),
                "height": int(fh),
                "color": cab.front_color,
                "notes": f"Handle: {cab.handle_type}"
            })

        # Process HDF backs
        if getattr(ct, "hdf_plecy", False):
            bw = getattr(ct, "bok_w_mm", 0)
            bh = getattr(ct, "bok_h_mm", 0)
            hdf.append({
                "seq": seq_symbol,
                "name": "HDF Plecy",
                "quantity": qty,
                "width": int(bw or 0),
                "height": int(bh or 0),
                "color": "",
                "notes": ""
            })

    def _process_adhoc_cabinet(
        self, cab, qty, seq, seq_symbol, formatki, fronty, hdf
    ):
        """Process elements from an ad-hoc cabinet, preserving individual cabinet identity"""
        width = cab.adhoc_width_mm
        height = cab.adhoc_height_mm
        depth = cab.adhoc_depth_mm

        # Sides (boki)
        formatki.append({
            "seq": seq_symbol,
            "name": "Bok",
            "quantity": 2 * qty,
            "width": int(depth),
            "height": int(height),
            "color": cab.body_color,
            "notes": "Ad-hoc"
        })

        # Top/bottom (wieńce)
        formatki.append({
            "seq": seq_symbol,
            "name": "Wieniec",
            "quantity": 2 * qty,
            "width": int(width),
            "height": int(depth),
            "color": cab.body_color,
            "notes": "Ad-hoc"
        })

        # Shelf (półka)
        formatki.append({
            "seq": seq_symbol,
            "name": "Półka",
            "quantity": qty,
            "width": int(width - 36),  # Account for sides
            "height": int(depth - 20),  # Account for back clearance
            "color": cab.body_color,
            "notes": "Ad-hoc"
        })

        # Front
        fronty.append({
            "seq": seq_symbol,
            "name": "Front",
            "quantity": qty,
            "width": int(width),
            "height": int(height),
            "color": cab.front_color,
            "notes": f"Handle: {cab.handle_type} (Ad-hoc)"
        })

        # HDF back
        hdf.append({
            "seq": seq_symbol,
            "name": "HDF Plecy",
            "quantity": qty,
            "width": int(width - 6),  # Slight adjustment
            "height": int(height - 6),  # Slight adjustment
            "color": "",
            "notes": "Ad-hoc"
        })

    def _process_accessories(
        self, cab, qty, seq, seq_symbol, akcesoria
    ):
        """Process accessories for a cabinet, preserving individual cabinet identity"""
        seq_label = f"Lp. {seq}"
        for link in getattr(cab, "accessories", []):
            acc = link.accessory
            total = link.count * qty
            akcesoria.append({
                "name": acc.name,
                "sku": acc.sku,
                "quantity": total,
                "notes": seq_label,
                "sequence": seq
            })
