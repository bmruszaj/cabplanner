from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from src.db_schema.orm_models import (
    Project,
    ProjectCabinet,
    ProjectCabinetPart,
    ProjectCabinetAccessorySnapshot,
    CabinetTemplate,
)


def get_circled_number(n: int) -> str:
    if 1 <= n <= 20:
        return chr(9311 + n)
    return f"({n})"


class ProjectService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def list_projects(self) -> List[Project]:
        stmt = select(Project).order_by(Project.created_at.desc(), Project.id.desc())
        return list(self.db.scalars(stmt).all())

    def get_project(self, project_id: int) -> Optional[Project]:
        return self.db.get(Project, project_id)

    def get_project_by_order_number(self, order_number: str) -> Optional[Project]:
        """Get project by order number (used for uniqueness checking)"""
        stmt = select(Project).where(Project.order_number == order_number)
        return self.db.scalar(stmt)

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
            .options(joinedload(ProjectCabinet.parts))  # Load snapshot parts
            .options(
                joinedload(ProjectCabinet.accessory_snapshots)
            )  # Load snapshot accessories
            .order_by(ProjectCabinet.sequence_number)
        )
        return list(self.db.scalars(stmt).unique().all())

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
    ) -> ProjectCabinet:
        cab = ProjectCabinet(
            project_id=project_id,
            sequence_number=sequence_number,
            type_id=type_id,
            body_color=body_color,
            front_color=front_color,
            handle_type=handle_type,
            quantity=quantity,
        )
        self.db.add(cab)
        self.db.flush()  # Get the ID without committing

        # Materialize parts from catalog template if it's a standard cabinet
        if type_id:
            self._materialize_standard_cabinet_parts(cab, type_id)
            self._materialize_standard_cabinet_accessories(cab, type_id)

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

    def add_custom_cabinet(
        self,
        project_id: int,
        *,
        sequence_number: int,
        body_color: str,
        front_color: str,
        handle_type: str,
        quantity: int = 1,
        custom_parts: List[Dict[str, Any]],
        custom_accessories: List[Dict[str, Any]] = None,
        calc_context: Dict[str, Any] = None,
    ) -> ProjectCabinet:
        """Add a custom cabinet with calculated parts."""
        cab = ProjectCabinet(
            project_id=project_id,
            sequence_number=sequence_number,
            type_id=None,  # Custom cabinet
            body_color=body_color,
            front_color=front_color,
            handle_type=handle_type,
            quantity=quantity,
        )
        self.db.add(cab)
        self.db.flush()  # Get the ID without committing

        # Materialize custom parts
        self._materialize_custom_cabinet_parts(cab, custom_parts, calc_context)

        # Materialize custom accessories if provided
        if custom_accessories:
            self._materialize_custom_cabinet_accessories(cab, custom_accessories)

        self.db.commit()
        self.db.refresh(cab)
        return cab

    def _materialize_standard_cabinet_parts(
        self, cabinet: ProjectCabinet, type_id: int
    ):
        """Materialize parts from a catalog template into ProjectCabinetPart snapshots."""
        template = self.db.get(CabinetTemplate, type_id)
        if not template:
            return

        for part in template.parts:
            snapshot_part = ProjectCabinetPart(
                project_cabinet_id=cabinet.id,
                part_name=part.part_name,
                height_mm=part.height_mm,
                width_mm=part.width_mm,
                pieces=part.pieces,
                wrapping=part.wrapping,
                comments=part.comments,
                material=part.material,
                thickness_mm=part.thickness_mm,
                processing_json=part.processing_json,
                source_template_id=template.id,
                source_part_id=part.id,
                calc_context_json=None,  # Not needed for standard cabinets
            )
            self.db.add(snapshot_part)

    def _materialize_standard_cabinet_accessories(
        self, cabinet: ProjectCabinet, type_id: int
    ):
        """Materialize accessories from a catalog template into ProjectCabinetAccessorySnapshot."""
        try:
            template = self.db.get(CabinetTemplate, type_id)
            if not template:
                return

            # Check if template has accessories relationship and it's not empty
            if not hasattr(template, "accessories") or not template.accessories:
                return

            # Iterate over accessories - use list() to materialize the query
            accessories_list = list(template.accessories)
            for template_accessory in accessories_list:
                # Get accessory details from the linked Accessory object
                accessory = template_accessory.accessory
                if not accessory:
                    continue

                snapshot_accessory = ProjectCabinetAccessorySnapshot(
                    project_cabinet_id=cabinet.id,
                    name=accessory.name,
                    sku=accessory.sku,
                    count=template_accessory.count,
                    source_accessory_id=accessory.id,
                )
                self.db.add(snapshot_accessory)
        except Exception as e:
            # Log but don't fail - accessories are optional
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to materialize accessories: {e}"
            )

    def _materialize_custom_cabinet_parts(
        self,
        cabinet: ProjectCabinet,
        parts_data: List[Dict[str, Any]],
        calc_context: Dict[str, Any] = None,
    ):
        """Materialize custom calculated parts into ProjectCabinetPart snapshots."""
        for part_data in parts_data:
            snapshot_part = ProjectCabinetPart(
                project_cabinet_id=cabinet.id,
                part_name=part_data.get("part_name", ""),
                height_mm=part_data.get("height_mm", 0),
                width_mm=part_data.get("width_mm", 0),
                pieces=part_data.get("pieces", 1),
                wrapping=part_data.get("wrapping"),
                comments=part_data.get("comments"),
                material=part_data.get("material"),
                thickness_mm=part_data.get("thickness_mm"),
                processing_json=part_data.get("processing_json"),
                source_template_id=None,  # Custom cabinet
                source_part_id=None,  # Custom cabinet
                calc_context_json=calc_context,  # Store calculation context
            )
            self.db.add(snapshot_part)

    def _materialize_custom_cabinet_accessories(
        self, cabinet: ProjectCabinet, accessories_data: List[Dict[str, Any]]
    ):
        """Materialize custom accessories into ProjectCabinetAccessorySnapshot."""
        for acc_data in accessories_data:
            snapshot_accessory = ProjectCabinetAccessorySnapshot(
                project_cabinet_id=cabinet.id,
                name=acc_data.get("name", ""),
                sku=acc_data.get("sku", ""),
                count=acc_data.get("count", 1),
                source_accessory_id=acc_data.get("source_accessory_id"),  # Can be None
            )
            self.db.add(snapshot_accessory)

    def update_cabinet_parts(
        self, cabinet_id: int, parts_data: List[Dict[str, Any]]
    ) -> bool:
        """Update the parts for a cabinet (edit the snapshot)."""
        cabinet = self.get_cabinet(cabinet_id)
        if not cabinet:
            return False

        # Remove existing parts
        for part in cabinet.parts:
            self.db.delete(part)

        # Add updated parts
        for part_data in parts_data:
            snapshot_part = ProjectCabinetPart(
                project_cabinet_id=cabinet.id,
                part_name=part_data.get("part_name", ""),
                height_mm=part_data.get("height_mm", 0),
                width_mm=part_data.get("width_mm", 0),
                pieces=part_data.get("pieces", 1),
                wrapping=part_data.get("wrapping"),
                comments=part_data.get("comments"),
                material=part_data.get("material"),
                thickness_mm=part_data.get("thickness_mm"),
                processing_json=part_data.get("processing_json"),
                source_template_id=part_data.get("source_template_id"),
                source_part_id=part_data.get("source_part_id"),
                calc_context_json=part_data.get("calc_context_json"),
            )
            self.db.add(snapshot_part)

        cabinet.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def add_accessory_to_cabinet(
        self,
        cabinet_id: int,
        name: str,
        sku: str = None,
        count: int = 1,
        source_accessory_id: int = None,
    ) -> bool:
        """Add an accessory to a cabinet."""
        cabinet = self.get_cabinet(cabinet_id)
        if not cabinet:
            return False

        # Validate input parameters
        if count <= 0:
            return False  # Only positive counts allowed

        if not name:
            return False  # Name is required

        # Create accessory snapshot
        snapshot_accessory = ProjectCabinetAccessorySnapshot(
            project_cabinet_id=cabinet.id,
            name=name,
            sku=sku or "",
            count=count,
            source_accessory_id=source_accessory_id,
        )
        self.db.add(snapshot_accessory)

        cabinet.updated_at = datetime.now(timezone.utc)

        try:
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def remove_accessory_from_cabinet(self, accessory_snapshot_id: int) -> bool:
        """Remove an accessory from a cabinet."""
        accessory_snapshot = (
            self.db.query(ProjectCabinetAccessorySnapshot)
            .filter_by(id=accessory_snapshot_id)
            .first()
        )

        if not accessory_snapshot:
            return False

        cabinet = accessory_snapshot.project_cabinet
        self.db.delete(accessory_snapshot)

        cabinet.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def update_accessory_quantity(
        self, accessory_snapshot_id: int, new_count: int
    ) -> bool:
        """Update the quantity of an accessory in a cabinet."""
        accessory_snapshot = (
            self.db.query(ProjectCabinetAccessorySnapshot)
            .filter_by(id=accessory_snapshot_id)
            .first()
        )

        if not accessory_snapshot:
            return False

        # Validate new count
        if new_count <= 0:
            return False  # Only positive counts allowed

        accessory_snapshot.count = new_count
        accessory_snapshot.project_cabinet.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        return True

    def get_aggregated_project_elements(
        self, project_id: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all elements in a project from snapshot data.
        Returns a dictionary with lists for formatki, fronty, hdf, and akcesoria.
        """
        project = self.get_project(project_id)
        if not project:
            return {"formatki": [], "fronty": [], "hdf": [], "akcesoria": []}

        formatki = []
        fronty = []
        hdf = []
        akcesoria = []

        for cab in project.cabinets:
            qty = cab.quantity
            seq = cab.sequence_number
            seq_symbol = get_circled_number(seq)

            # Process all parts from snapshot (works for both standard and custom)
            self._process_cabinet_parts_snapshot(
                cab, qty, seq, seq_symbol, formatki, fronty, hdf
            )

            # Process accessories from snapshot
            self._process_accessories_snapshot(cab, qty, seq, seq_symbol, akcesoria)

        return {
            "formatki": formatki,
            "fronty": fronty,
            "hdf": hdf,
            "akcesoria": akcesoria,
        }

    def _process_cabinet_parts_snapshot(
        self, cab, qty, seq, seq_symbol, formatki, fronty, hdf
    ):
        """Process elements from cabinet parts snapshot (works for both standard and custom)"""
        # Process all parts from the snapshot
        for part in cab.parts:
            part_qty = part.pieces * qty

            # Determine material from part data (with fallback logic)
            material = part.material
            if not material:
                if "front" in part.part_name.lower():
                    material = "FRONT"
                elif "hdf" in part.part_name.lower():
                    material = "HDF"
                else:
                    material = "PLYTA"  # Default for panels

            # Determine category based on material
            if material == "FRONT":
                fronty.append(
                    {
                        "seq": seq_symbol,
                        "name": part.part_name,
                        "quantity": part_qty,
                        "width": part.width_mm,
                        "height": part.height_mm,
                        "color": cab.front_color,
                        "notes": f"Handle: {cab.handle_type}",
                    }
                )
            elif material == "HDF":
                hdf.append(
                    {
                        "seq": seq_symbol,
                        "name": part.part_name,
                        "quantity": part_qty,
                        "width": part.width_mm,
                        "height": part.height_mm,
                        "color": "",
                        "notes": part.comments or "",
                    }
                )
            else:
                # Default to formatki (panels)
                formatki.append(
                    {
                        "seq": seq_symbol,
                        "name": part.part_name,
                        "quantity": part_qty,
                        "width": part.width_mm,
                        "height": part.height_mm,
                        "color": cab.body_color,
                        "notes": part.comments or "",
                    }
                )

    def _process_accessories_snapshot(self, cab, qty, seq, seq_symbol, akcesoria):
        """Process accessories from snapshot (works for both standard and custom)"""
        seq_label = f"Lp. {seq}"

        # Process accessory snapshots
        for acc_snapshot in cab.accessory_snapshots:
            total = acc_snapshot.count * qty
            akcesoria.append(
                {
                    "name": acc_snapshot.name,
                    "sku": acc_snapshot.sku,
                    "quantity": total,
                    "notes": seq_label,
                    "sequence": seq,
                }
            )

        # Legacy support: also process old-style accessories if they exist
        for link in getattr(cab, "accessories", []):
            acc = link.accessory
            total = link.count * qty
            akcesoria.append(
                {
                    "name": acc.name,
                    "sku": acc.sku,
                    "quantity": total,
                    "notes": seq_label,
                    "sequence": seq,
                }
            )
