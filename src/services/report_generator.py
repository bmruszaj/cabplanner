import os
import re
import sys
import subprocess
import logging
from pathlib import Path
from datetime import date
from typing import List, Tuple, Optional, Any, Dict
from types import SimpleNamespace

from docx import Document
from docx.document import Document as DocxDocument
from docx.section import Section
from docx.shared import Pt, Inches, Mm
from docx.table import Table
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.shared import qn

from src.app.paths import get_base_path
from src.constants import (
    REPORT_COLUMN_GAP_MM_DEFAULT,
    REPORT_COLUMN_GAP_MM_MAX,
    REPORT_COLUMN_GAP_MM_MIN,
    REPORT_LEFT_MARGIN_MM_DEFAULT,
    REPORT_MARGIN_MM_MAX,
    REPORT_MARGIN_MM_MIN,
    REPORT_NOTES_COLUMN_WIDTH_PERCENT_DEFAULT,
    REPORT_NOTES_COLUMN_WIDTH_PERCENT_MAX,
    REPORT_NOTES_COLUMN_WIDTH_PERCENT_MIN,
    REPORT_ROW_SPACING_PT_DEFAULT,
    REPORT_ROW_SPACING_PT_MAX,
    REPORT_ROW_SPACING_PT_MIN,
    REPORT_RIGHT_MARGIN_MM_DEFAULT,
)
from src.db_schema.orm_models import Project
from src.services.project_service import ProjectService
from src.services.settings_service import SettingsService
from sqlalchemy.orm import Session

# Configure logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates a .docx report for a Cabplanner project.

    This class is responsible only for document generation and formatting.
    All data access and business logic is delegated to service classes.
    """

    def __init__(
        self,
        program_logo_path: Optional[Path] = None,
        company_logo_path: Optional[Path] = None,
        db_session: Optional[Session] = None,
    ) -> None:
        # Backward compatibility:
        # some callers passed Session as first positional argument.
        resolved_db_session = db_session
        if resolved_db_session is None and isinstance(program_logo_path, Session):
            resolved_db_session = program_logo_path
            program_logo_path = None
        elif resolved_db_session is None and isinstance(company_logo_path, Session):
            resolved_db_session = company_logo_path
            company_logo_path = None

        # Make sure paths are either None or proper Path objects
        self.program_logo_path = (
            Path(program_logo_path)
            if program_logo_path and not isinstance(program_logo_path, Session)
            else None
        )
        self.company_logo_path = (
            Path(company_logo_path)
            if company_logo_path and not isinstance(company_logo_path, Session)
            else None
        )
        self.db_session = resolved_db_session

        # Initialize ProjectService if session is provided
        self.project_service = (
            ProjectService(resolved_db_session) if resolved_db_session else None
        )
        self.settings_service = (
            SettingsService(resolved_db_session) if resolved_db_session else None
        )

    def generate(
        self,
        project: Project,
        output_dir: str = "documents/reports",
        auto_open: bool = True,
    ) -> str:
        """
        Generate the .docx report and return its file path.
        """
        try:
            logger.info(
                f"Generating report for project: {project.name} (ID: {project.id})"
            )
            doc = Document()
            section = doc.sections[0]
            section.different_first_page_header_footer = False
            self._apply_page_layout(section)

            # Header and footer on every page
            self._add_header(section, project)
            self._add_footer(section)

            # Get data for report
            if self.project_service and project.id:
                # Get aggregated elements from service
                logger.debug("Using project service to get aggregated elements")
                elements = self.project_service.get_aggregated_project_elements(
                    project.id
                )
                formatki = self._dict_to_namespace_list(elements["formatki"])
                fronty = self._dict_to_namespace_list(elements["fronty"])
                witryny = self._dict_to_namespace_list(elements.get("witryny", []))
                polki_szklane = self._dict_to_namespace_list(
                    elements.get("polki_szklane", [])
                )
                hdf = self._dict_to_namespace_list(elements["hdf"])
                akcesoria = self._dict_to_namespace_list(elements["akcesoria"])
            else:
                # Fallback to direct data extraction if service not available
                logger.warning(
                    "Project service not available, using direct data extraction"
                )
                formatki, fronty, witryny, polki_szklane, hdf, akcesoria = (
                    self._extract_elements_directly_with_witryny(project)
                )

            # Default sort by cabinet number first, then by color.
            formatki = self._sort_by_cabinet_and_color(formatki)
            fronty = self._sort_by_cabinet_and_color(fronty)
            witryny = self._sort_by_cabinet_and_color(witryny)
            polki_szklane = self._sort_by_cabinet_and_color(polki_szklane)
            hdf = self._sort_by_cabinet_and_color(hdf)
            akcesoria = self._aggregate_accessories(akcesoria)

            self._add_grouped_primary_sections(doc, formatki, fronty)
            if witryny:
                self._add_parts_section(
                    doc,
                    "WITRYNY",
                    witryny,
                    show_color_column=False,
                    show_notes_column=False,
                )
            if polki_szklane:
                self._add_parts_section(
                    doc,
                    "PÓŁKI SZKLANE",
                    polki_szklane,
                    show_color_column=False,
                    show_notes_column=False,
                )
            self._add_parts_section(doc, "HDF", hdf)
            self._add_parts_section(doc, "AKCESORIA", akcesoria, accessory=True)

            # Optional notes
            self._add_notes(doc, project)

            # Save with handling for open files
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            base_name = self._sanitize_filename_component(
                f"projekt_{project.order_number}"
            )
            output_path = self._get_available_filename(out_dir, base_name)
            doc.save(str(output_path))
            logger.info(f"Report saved to: {output_path}")

            if auto_open:
                self._open_file(output_path)

            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")

    def _sort_by_cabinet_and_color(
        self, items: List[SimpleNamespace]
    ) -> List[SimpleNamespace]:
        """Sort items by cabinet sequence number and then by color."""
        return sorted(
            items,
            key=lambda item: (
                item.sequence,
                (getattr(item, "color", "") or "").strip().lower(),
                getattr(item, "name", "") or "",
            ),
        )

    def _add_grouped_primary_sections(
        self,
        doc: DocxDocument,
        formatki: List[SimpleNamespace],
        fronty: List[SimpleNamespace],
    ) -> None:
        """
        Keep matching FORMATKI and FRONTY blocks adjacent for the same cabinet bundle.

        A bundle is defined by the body/front colors copied from the originating
        cabinet, which lets us keep related sections together without guessing from
        the rendered document layout alone.
        """
        bundles: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for part in formatki:
            bundle = self._get_or_create_primary_bundle(bundles, part)
            material = (getattr(part, "material", "") or "").strip().upper()
            if material == "PLYTA 18":
                bundle["formatki_plyta_18"].append(part)
            elif material == "PLYTA 12":
                bundle["formatki_plyta_12"].append(part)
            elif material == "PLYTA 16":
                bundle["formatki_plyta_16"].append(part)
            else:
                bundle["formatki_other"].append(part)

        for part in fronty:
            bundle = self._get_or_create_primary_bundle(bundles, part)
            bundle["fronty"].append(part)

        ordered_bundles = sorted(
            bundles.values(),
            key=lambda bundle: (
                bundle["first_sequence"],
                bundle["body_color_label"].lower(),
                bundle["front_color_label"].lower(),
            ),
        )
        plyta_16_bundle_count = sum(
            1 for bundle in ordered_bundles if bundle["formatki_plyta_16"]
        )

        for bundle in ordered_bundles:
            body_color_label = bundle["body_color_label"]
            front_color_label = bundle["front_color_label"]

            formatki_plyta_18 = self._sort_parts_for_section(
                bundle["formatki_plyta_18"]
            )
            if formatki_plyta_18:
                self._add_parts_section(
                    doc,
                    f"FORMATKI (PLYTA 18) - {body_color_label}",
                    formatki_plyta_18,
                )

            formatki_plyta_12 = self._sort_parts_for_section(
                bundle["formatki_plyta_12"]
            )
            if formatki_plyta_12:
                self._add_parts_section(
                    doc,
                    f"FORMATKI (PLYTA 12) - {body_color_label}",
                    formatki_plyta_12,
                )

            formatki_other = self._sort_parts_for_section(bundle["formatki_other"])
            if formatki_other:
                self._add_parts_section(
                    doc,
                    f"FORMATKI - {body_color_label}",
                    formatki_other,
                )

            grouped_fronty = self._sort_parts_for_section(bundle["fronty"])
            if grouped_fronty:
                self._add_parts_section(
                    doc,
                    f"FRONTY - {front_color_label}",
                    grouped_fronty,
                    show_notes_column=False,
                )

            formatki_plyta_16 = self._sort_parts_for_section(
                bundle["formatki_plyta_16"]
            )
            if formatki_plyta_16:
                plyta_16_title = "FORMATKI (PLYTA 16)"
                if plyta_16_bundle_count > 1:
                    plyta_16_title = f"{plyta_16_title} - {body_color_label}"
                self._add_parts_section(
                    doc,
                    plyta_16_title,
                    formatki_plyta_16,
                    hide_color_values=True,
                )

    def _get_or_create_primary_bundle(
        self,
        bundles: Dict[Tuple[str, str], Dict[str, Any]],
        part: SimpleNamespace,
    ) -> Dict[str, Any]:
        body_color_key, body_color_label = self._get_bundle_color(part, "body")
        front_color_key, front_color_label = self._get_bundle_color(part, "front")
        bundle_key = (body_color_key, front_color_key)

        if bundle_key not in bundles:
            bundles[bundle_key] = {
                "first_sequence": getattr(part, "sequence", 0),
                "body_color_label": body_color_label,
                "front_color_label": front_color_label,
                "formatki_plyta_18": [],
                "formatki_plyta_12": [],
                "formatki_plyta_16": [],
                "formatki_other": [],
                "fronty": [],
            }
        else:
            bundles[bundle_key]["first_sequence"] = min(
                int(bundles[bundle_key]["first_sequence"]),
                getattr(part, "sequence", 0),
            )

        return bundles[bundle_key]

    def _get_bundle_color(
        self, part: SimpleNamespace, color_role: str
    ) -> Tuple[str, str]:
        raw_color = getattr(part, f"{color_role}_color", None)
        if raw_color is None:
            raw_color = getattr(part, "color", "")

        label = (raw_color or "").strip() or "BRAK KOLORU"
        return label.lower(), label

    def _sort_parts_for_section(self, parts: List[Any]) -> List[Any]:
        return sorted(
            parts,
            key=lambda item: (
                getattr(item, "sequence", 0),
                (getattr(item, "color", "") or "").strip().lower(),
                getattr(item, "name", "") or "",
            ),
        )

    def _add_parts_sections_grouped_by_color(
        self, doc: DocxDocument, base_title: str, parts: List[Any]
    ) -> None:
        """Render separate sections for each color: '<base title> - <color>'."""
        if not parts:
            self._add_parts_section(doc, base_title, parts)
            return

        grouped: Dict[str, List[Any]] = {}
        color_labels: Dict[str, str] = {}

        for part in parts:
            raw_color = (getattr(part, "color", "") or "").strip()
            color_key = raw_color.lower()
            grouped.setdefault(color_key, []).append(part)
            color_labels.setdefault(color_key, raw_color or "BRAK KOLORU")

        for color_key in sorted(grouped.keys(), key=lambda key: (key == "", key)):
            grouped_parts = sorted(
                grouped[color_key],
                key=lambda item: (
                    getattr(item, "sequence", 0),
                    getattr(item, "name", "") or "",
                ),
            )
            self._add_parts_section(
                doc,
                f"{base_title} - {color_labels[color_key]}",
                grouped_parts,
            )

    def _dict_to_namespace_list(self, dict_list: List[Dict]) -> List[SimpleNamespace]:
        """Convert a list of dictionaries to a list of SimpleNamespace objects"""
        return [SimpleNamespace(**item) for item in dict_list]

    def _aggregate_accessories(
        self, accessories: List[SimpleNamespace]
    ) -> List[SimpleNamespace]:
        """
        Aggregate accessories across cabinets.
        Group by source_accessory_id when available, otherwise by normalized name.
        """
        aggregated: Dict[tuple, SimpleNamespace] = {}

        for accessory in accessories:
            source_accessory_id = getattr(accessory, "source_accessory_id", None)
            name = (getattr(accessory, "name", "") or "").strip()
            notes = (getattr(accessory, "notes", "") or "").strip()
            quantity = int(getattr(accessory, "quantity", 0) or 0)

            if source_accessory_id is not None:
                key = ("id", source_accessory_id)
            else:
                key = ("name", name.lower())

            if key not in aggregated:
                aggregated[key] = SimpleNamespace(
                    source_accessory_id=source_accessory_id,
                    name=name,
                    quantity=0,
                    notes=notes,
                )

            aggregated[key].quantity += quantity

            if not aggregated[key].notes and notes:
                aggregated[key].notes = notes

        return sorted(
            aggregated.values(),
            key=lambda accessory: (accessory.name or "").lower(),
        )

    def _extract_elements_directly(
        self, project: Project
    ) -> Tuple[
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
    ]:
        """
        Backward-compatible extraction used by existing tests/callers.
        Returns: formatki, fronty, hdf, akcesoria.
        """
        formatki, fronty, witryny, polki_szklane, hdf, akcesoria = (
            self._extract_elements_directly_with_witryny(project)
        )
        # Legacy API had no separate WITRYNY / PÓŁKI SZKLANE buckets.
        return formatki + polki_szklane, fronty + witryny, hdf, akcesoria

    def _extract_elements_directly_with_witryny(
        self, project: Project
    ) -> Tuple[
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
    ]:
        """
        Extract parts lists directly from project object.
        This is a fallback method when ProjectService is not available.
        """
        formatki = []
        fronty = []
        witryny = []
        polki_szklane = []
        hdf = []
        akcesoria = []

        # This is a minimal implementation - ideally this logic should be in the service layer
        if not hasattr(project, "cabinets"):
            logger.warning("Project has no cabinets, returning empty lists")
            return formatki, fronty, witryny, polki_szklane, hdf, akcesoria

        for cab in project.cabinets:
            qty = cab.quantity

            # Process both catalog and custom cabinets
            self._process_cabinet(
                cab, qty, formatki, fronty, hdf, witryny, polki_szklane
            )

            # Process accessories for all cabinet types
            self._process_accessories(cab, qty, akcesoria)

        return formatki, fronty, witryny, polki_szklane, hdf, akcesoria

    def _process_cabinet(self, cab, qty, formatki, fronty, hdf, witryny, polki_szklane):
        """Process a cabinet (catalog or custom) and add its parts to the appropriate lists"""
        # Get the sequence number for this cabinet
        seq_num = getattr(cab, "sequence_number", 0)
        seq_symbol = str(seq_num)

        # Determine parts source based on cabinet type
        ct = cab.cabinet_type
        if ct:
            # Catalog cabinet: get parts from template
            parts = ct.parts
        else:
            # Custom cabinet: get parts directly from cabinet (snapshot architecture)
            parts = getattr(cab, "parts", [])

        # Process all parts
        for part in parts:
            part_qty = part.pieces * qty

            # Determine material
            material = part.material
            if not material:
                # For catalog cabinets, infer material from part name if not set
                if ct and not material:
                    part_name_lc = part.part_name.lower()
                    if "półka szkl" in part_name_lc or "polka szkl" in part_name_lc:
                        material = "PÓŁKA SZKLANA"
                    elif "witryn" in part_name_lc:
                        material = "WITRYNA"
                    elif "front" in part_name_lc:
                        material = "FRONT"
                    elif "hdf" in part_name_lc:
                        material = "HDF"
                    else:
                        material = "PLYTA"  # Default for panels
                else:
                    # For custom cabinets, default to PLYTA
                    material = "PLYTA"

            # Determine category based on material
            material_upper = material.upper() if material else ""
            if material_upper.startswith("PÓŁKA SZKLANA") or material_upper.startswith(
                "POLKA SZKLANA"
            ):
                polki_szklane.append(
                    SimpleNamespace(
                        seq=seq_symbol,
                        sequence=seq_num,
                        body_color=cab.body_color,
                        front_color=cab.front_color,
                        name=part.part_name,
                        quantity=part_qty,
                        width=part.width_mm,
                        height=part.height_mm,
                        color=cab.body_color,
                        wrapping=getattr(part, "wrapping", "") or "",
                        notes=part.comments or "",
                    )
                )
            elif material_upper.startswith("WITRYNA"):
                witryny.append(
                    SimpleNamespace(
                        seq=seq_symbol,
                        sequence=seq_num,
                        body_color=cab.body_color,
                        front_color=cab.front_color,
                        name=part.part_name,
                        quantity=part_qty,
                        width=part.width_mm,
                        height=part.height_mm,
                        color=cab.front_color,
                        wrapping=getattr(part, "wrapping", "") or "",
                        notes=f"Handle: {cab.handle_type}",
                    )
                )
            elif material_upper.startswith("FRONT"):
                fronty.append(
                    SimpleNamespace(
                        seq=seq_symbol,
                        sequence=seq_num,
                        body_color=cab.body_color,
                        front_color=cab.front_color,
                        name=part.part_name,
                        quantity=part_qty,
                        width=part.width_mm,
                        height=part.height_mm,
                        color=cab.front_color,
                        wrapping=getattr(part, "wrapping", "") or "",
                        notes=f"Handle: {cab.handle_type}",
                    )
                )
            elif material_upper.startswith("HDF"):
                hdf.append(
                    SimpleNamespace(
                        seq=seq_symbol,
                        sequence=seq_num,
                        body_color=cab.body_color,
                        front_color=cab.front_color,
                        name=part.part_name,
                        quantity=part_qty,
                        width=part.width_mm,
                        height=part.height_mm,
                        color="",
                        wrapping=getattr(part, "wrapping", "") or "",
                        notes=part.comments or "",
                    )
                )
            else:
                # Default to formatki (panels)
                formatki.append(
                    SimpleNamespace(
                        seq=seq_symbol,
                        sequence=seq_num,
                        body_color=cab.body_color,
                        front_color=cab.front_color,
                        name=part.part_name,
                        quantity=part_qty,
                        width=part.width_mm,
                        height=part.height_mm,
                        color=cab.body_color,
                        material=material,
                        wrapping=getattr(part, "wrapping", "") or "",
                        notes=part.comments or "",
                    )
                )

    def _process_accessories(self, cab, qty, akcesoria):
        """Process accessories for a cabinet and add them to the accessories list"""
        for link in getattr(cab, "accessories", []):
            acc = link.accessory
            total = link.count * qty
            akcesoria.append(
                SimpleNamespace(
                    name=acc.name,
                    source_accessory_id=getattr(acc, "id", None),
                    quantity=total,
                    notes="",
                )
            )

    def _get_numeric_setting(
        self, key: str, default: int, minimum: int, maximum: int
    ) -> int:
        """Return a clamped integer setting, tolerating string/float storage."""
        if not self.settings_service:
            return default

        try:
            raw_value = self.settings_service.get_setting_value(key, default)
            if raw_value in (None, ""):
                return default
            numeric_value = int(round(float(raw_value)))
        except (TypeError, ValueError) as exc:
            logger.warning("Failed to read numeric setting '%s': %s", key, exc)
            return default

        return max(minimum, min(maximum, numeric_value))

    def _get_float_setting(
        self, key: str, default: float, minimum: float, maximum: float
    ) -> float:
        """Return a clamped float setting, tolerating string/int storage."""
        if not self.settings_service:
            return default

        try:
            raw_value = self.settings_service.get_setting_value(key, default)
            if raw_value in (None, ""):
                return default
            numeric_value = float(raw_value)
        except (TypeError, ValueError) as exc:
            logger.warning("Failed to read float setting '%s': %s", key, exc)
            return default

        return max(minimum, min(maximum, numeric_value))

    def _get_report_left_margin_mm(self) -> int:
        """Get the configured left page margin for generated reports."""
        return self._get_numeric_setting(
            "report_left_margin_mm",
            REPORT_LEFT_MARGIN_MM_DEFAULT,
            REPORT_MARGIN_MM_MIN,
            REPORT_MARGIN_MM_MAX,
        )

    def _get_report_right_margin_mm(self) -> int:
        """Get the configured right page margin for generated reports."""
        return self._get_numeric_setting(
            "report_right_margin_mm",
            REPORT_RIGHT_MARGIN_MM_DEFAULT,
            REPORT_MARGIN_MM_MIN,
            REPORT_MARGIN_MM_MAX,
        )

    def _get_report_notes_column_width_percent(self) -> int:
        """Get the configured width share of the common 'Uwagi' column."""
        return self._get_numeric_setting(
            "report_notes_column_width_percent",
            REPORT_NOTES_COLUMN_WIDTH_PERCENT_DEFAULT,
            REPORT_NOTES_COLUMN_WIDTH_PERCENT_MIN,
            REPORT_NOTES_COLUMN_WIDTH_PERCENT_MAX,
        )

    def _get_report_column_gap_mm(self) -> float:
        """Get the configured fixed gap between report table columns."""
        return self._get_float_setting(
            "report_column_gap_mm",
            REPORT_COLUMN_GAP_MM_DEFAULT,
            REPORT_COLUMN_GAP_MM_MIN,
            REPORT_COLUMN_GAP_MM_MAX,
        )

    def _get_report_row_spacing_pt(self) -> int:
        """Get the configured extra spacing after each table row paragraph."""
        return self._get_numeric_setting(
            "report_row_spacing_pt",
            REPORT_ROW_SPACING_PT_DEFAULT,
            REPORT_ROW_SPACING_PT_MIN,
            REPORT_ROW_SPACING_PT_MAX,
        )

    def _apply_page_layout(self, section: Section) -> None:
        """Apply page layout settings before adding report content."""
        section.left_margin = Mm(self._get_report_left_margin_mm())
        section.right_margin = Mm(self._get_report_right_margin_mm())

    def _scale_column_widths(
        self, total_width: int, fixed_weights: List[int], notes_percent: int
    ) -> List[int]:
        """Convert relative weights into table column widths."""
        notes_ratio = notes_percent / 100
        remaining_ratio = 1 - notes_ratio
        fixed_total = sum(fixed_weights)
        ratios = [(weight / fixed_total) * remaining_ratio for weight in fixed_weights]
        ratios.append(notes_ratio)

        widths = [int(total_width * ratio) for ratio in ratios]
        widths[-1] += total_width - sum(widths)
        return widths

    def _scale_fixed_column_widths(
        self, total_width: int, weights: List[int]
    ) -> List[int]:
        """Convert fixed relative weights into table column widths."""
        total_weight = sum(weights)
        widths = [int(total_width * (weight / total_weight)) for weight in weights]
        widths[-1] += total_width - sum(widths)
        return widths

    def _get_parts_table_column_widths(
        self,
        doc: DocxDocument,
        accessory: bool = False,
        show_color_column: bool = True,
        show_notes_column: bool = True,
    ) -> List[int]:
        """Calculate fixed widths for report body tables."""
        section = doc.sections[-1]
        column_gap = int(Mm(self._get_report_column_gap_mm()))
        notes_percent = self._get_report_notes_column_width_percent()

        if accessory:
            usable_width = int(
                section.page_width
                - section.left_margin
                - section.right_margin
                - (3 * column_gap)
            )
            return self._scale_column_widths(usable_width, [10, 64, 10], notes_percent)

        # Keep shared columns aligned across sections, even when some trailing
        # columns are omitted. This avoids visually larger "gaps" in shorter tables.
        full_usable_width = int(
            section.page_width
            - section.left_margin
            - section.right_margin
            - (6 * column_gap)
        )
        full_widths = self._scale_column_widths(
            full_usable_width, [7, 32, 20, 10, 13, 12], notes_percent
        )
        visible_indices = [0, 1, 2, 3, 4]

        if show_color_column:
            visible_indices.append(5)
        if show_notes_column:
            visible_indices.append(6)

        return [full_widths[index] for index in visible_indices]

    def _apply_table_column_widths(self, table: Table, widths: List[int]) -> None:
        """Lock report table columns so the notes column stays readable."""
        table.autofit = False
        for column_index, width in enumerate(widths):
            table.columns[column_index].width = width
            for cell in table.columns[column_index].cells:
                cell.width = width

    def _apply_table_column_gap(self, table: Table) -> None:
        """Apply a fixed spacing between table columns."""
        tbl_pr = table._tbl.tblPr
        tbl_cell_spacing = tbl_pr.find(qn("w:tblCellSpacing"))
        if tbl_cell_spacing is None:
            tbl_cell_spacing = OxmlElement("w:tblCellSpacing")
            tbl_pr.append(tbl_cell_spacing)

        tbl_cell_spacing.set(
            qn("w:w"), str(int(Mm(self._get_report_column_gap_mm()).twips))
        )
        tbl_cell_spacing.set(qn("w:type"), "dxa")

    def _apply_table_row_spacing(self, table: Table) -> None:
        """Apply compact paragraph spacing so report rows stay user-configurable."""
        row_spacing = Pt(self._get_report_row_spacing_pt())
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before = Pt(0)
                    paragraph.paragraph_format.space_after = row_spacing
                    paragraph.paragraph_format.line_spacing = 1.0

    def _get_report_logo_variant(self) -> str:
        """
        Get report logo variant from settings.

        Returns one of: "bw", "color".
        """
        if not self.settings_service:
            return "bw"

        try:
            raw_value = (
                self.settings_service.get_setting_value(
                    "report_program_logo_variant", "Czarno-białe"
                )
                or "Czarno-białe"
            )
            normalized = (
                str(raw_value)
                .strip()
                .lower()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
            )
        except Exception as exc:
            logger.warning("Failed to read report logo variant setting: %s", exc)
            return "bw"

        if normalized in ("kolorowe", "kolor", "color", "colour"):
            return "color"
        if normalized in (
            "czarnobiale",
            "czarnobiałe",
            "blackwhite",
            "bw",
            "mono",
            "monochrome",
            "grayscale",
            "greyscale",
        ):
            return "bw"
        return "bw"

    def _resolve_bundled_logo_path(self, filename: str) -> Optional[Path]:
        """Resolve bundled logo path in dev and frozen app layouts."""
        base = get_base_path()
        local_icons_dir = (
            Path(__file__).resolve().parents[1] / "gui" / "resources" / "icons"
        )
        candidates = [
            base / "src" / "gui" / "resources" / "icons" / filename,
            base / "_internal" / "src" / "gui" / "resources" / "icons" / filename,
            local_icons_dir / filename,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _get_program_logo_path(self) -> Optional[Path]:
        """Get program logo path (explicit path first, bundled fallback)."""
        if self.program_logo_path and self.program_logo_path.exists():
            return self.program_logo_path

        preferred_name = (
            "logo.png" if self._get_report_logo_variant() == "color" else "logo_bw.png"
        )
        fallback_name = "logo_bw.png" if preferred_name == "logo.png" else "logo.png"

        resolved = self._resolve_bundled_logo_path(preferred_name)
        if resolved:
            return resolved
        return self._resolve_bundled_logo_path(fallback_name)

    def _get_company_logo_path(self) -> Optional[Path]:
        """Get company logo path (explicit path first, then settings)."""
        if self.company_logo_path and self.company_logo_path.exists():
            return self.company_logo_path

        if not self.settings_service:
            return None

        try:
            raw_path = self.settings_service.get_setting_value("company_logo_path", "")
            if not raw_path:
                return None
            candidate = Path(str(raw_path))
            return candidate if candidate.exists() else None
        except Exception as exc:
            logger.warning("Failed to read company logo path from settings: %s", exc)
            return None

    def _add_header(self, section: Section, project: Project) -> None:
        header = section.header
        usable_width = section.page_width - section.left_margin - section.right_margin
        table = header.add_table(1, 2, usable_width)
        table.autofit = True

        # Left: metadata in single line with Polish labels
        cell_meta = table.rows[0].cells[0]
        p = cell_meta.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Single line format with Polish labels
        info_text = (
            f"Klient: {project.client_name} | "
            f"Adres: {project.client_address} | "
            f"Tel.: {project.client_phone} | "
            f"Email: {project.client_email} | "
            f"Nr zamówienia: {project.order_number} | "
            f"Typ kuchni: {project.kitchen_type} | "
            f"Data raportu: {date.today().isoformat()}"
        )

        run = p.add_run(info_text)
        run.font.size = Pt(10)

        # Right: logos (company + Cabplanner)
        cell_logo = table.rows[0].cells[1]
        paragraph_logo = cell_logo.paragraphs[0]
        paragraph_logo.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        company_logo_path = self._get_company_logo_path()
        if company_logo_path:
            run_logo = paragraph_logo.add_run()
            run_logo.add_picture(str(company_logo_path), width=Inches(1))

        program_logo_path = self._get_program_logo_path()
        if program_logo_path:
            # Keep program logo below company logo if both are present.
            if company_logo_path:
                paragraph_logo = cell_logo.add_paragraph()
                paragraph_logo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run_program_logo = paragraph_logo.add_run()
            run_program_logo.add_picture(str(program_logo_path), width=Inches(0.52))

    def _add_footer(self, section: Section) -> None:
        footer = section.footer
        usable_width = section.page_width - section.left_margin - section.right_margin
        table = footer.add_table(1, 2, usable_width)
        table.autofit = True

        # Branding
        cell_brand = table.rows[0].cells[0]
        p_brand = cell_brand.paragraphs[0]
        p_brand.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p_brand.add_run("Wygenerowano przez Cabplanner")
        run.italic = True

        # Page number
        cell_page = table.rows[0].cells[1]
        p_page = cell_page.paragraphs[0]
        p_page.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), "PAGE")
        p_page._p.append(fld)

    def _add_parts_section(
        self,
        doc: DocxDocument,
        title: str,
        parts: List[Any],
        accessory: bool = False,
        hide_color_values: bool = False,
        show_color_column: bool = True,
        show_notes_column: bool = True,
    ) -> None:
        # Check if we need a page break before adding section
        if parts and self._should_break_page_for_section(doc, len(parts)):
            doc.add_page_break()

        heading = doc.add_heading(title, level=2)
        # Keep heading with the following content to avoid orphaned section titles.
        heading.paragraph_format.keep_with_next = True
        if not parts:
            doc.add_paragraph("Brak pozycji.")
            return

        cols = (
            ["Poz.", "Nazwa akcesorium", "Ilość", "Uwagi"]
            if accessory
            else self._get_parts_table_headers(show_color_column, show_notes_column)
        )
        table = doc.add_table(rows=1, cols=len(cols))
        hdr = table.rows[0].cells
        for i, col in enumerate(cols):
            hdr[i].text = col
        qty_col_idx = 2 if accessory else 3
        hdr[qty_col_idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        seen_sequences = set()

        for row_index, part in enumerate(parts, start=1):
            cells = table.add_row().cells

            if accessory:
                # Accessories are project-wide aggregate; use row index, not cabinet sequence.
                cells[0].text = str(row_index)
                cells[1].text = part.name
                cells[2].text = str(part.quantity)
                cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cells[3].text = getattr(part, "notes", "") or ""
            else:
                sequence = getattr(part, "sequence", None)
                seq_value = getattr(part, "seq", "")
                if sequence in seen_sequences:
                    seq_value = ""
                elif sequence is not None:
                    seen_sequences.add(sequence)

                # Parts keep cabinet sequence marker.
                row_values = [
                    seq_value,
                    part.name,
                    f"{part.width} x {part.height}",
                    str(part.quantity),
                    getattr(part, "wrapping", "") or "",
                ]
                if show_color_column:
                    row_values.append(
                        "" if hide_color_values else getattr(part, "color", "") or ""
                    )
                if show_notes_column:
                    row_values.append(getattr(part, "notes", "") or "")

                for index, value in enumerate(row_values):
                    cells[index].text = value
                cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        self._apply_table_column_widths(
            table,
            self._get_parts_table_column_widths(
                doc,
                accessory=accessory,
                show_color_column=show_color_column,
                show_notes_column=show_notes_column,
            ),
        )
        self._apply_table_column_gap(table)
        self._apply_table_row_spacing(table)

    def _get_parts_table_headers(
        self, show_color_column: bool, show_notes_column: bool
    ) -> List[str]:
        headers = ["Lp.", "Nazwa", "Wymiary (mm)", "Ilość", "Okleina"]
        if show_color_column:
            headers.append("Kolor")
        if show_notes_column:
            headers.append("Uwagi")
        return headers

    def _add_notes(self, doc: DocxDocument, project: Project) -> None:
        if getattr(project, "blaty_note", None):
            p = doc.add_paragraph()
            p.add_run("Blaty: ").bold = True
            p.add_run(project.blaty_note)
        if getattr(project, "cokoly_note", None):
            p = doc.add_paragraph()
            p.add_run("Cokoły: ").bold = True
            p.add_run(project.cokoly_note)
        if getattr(project, "uwagi_note", None):
            p = doc.add_paragraph()
            p.add_run("Uwagi: ").bold = True
            p.add_run(project.uwagi_note)

    def _get_available_filename(self, output_dir: Path, base_name: str) -> Path:
        """
        Return the first free filename.
        Examples: raport.docx, raport (1).docx, raport (2).docx.
        """
        safe_base_name = self._sanitize_filename_component(base_name)

        for i in range(0, 100):
            suffix = "" if i == 0 else f" ({i})"
            candidate = output_dir / f"{safe_base_name}{suffix}.docx"
            if not candidate.exists():
                if i > 0:
                    logger.info(
                        f"Report file already exists, using alternative name: {candidate.name}"
                    )
                return candidate

        raise OSError(
            f"Nie można utworzyć unikalnej nazwy raportu dla '{safe_base_name}.docx'."
        )

    def _sanitize_filename_component(self, name: str) -> str:
        """Normalize file name to be safe on common file systems."""
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", (name or "").strip())
        sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
        return sanitized or "raport"

    def _get_page_break_strictness(self) -> str:
        """
        Get report pagination strictness from settings.

        Returns one of: "lagodna", "standardowa", "ostra".
        """
        if not self.settings_service:
            return "standardowa"

        try:
            raw_value = (
                self.settings_service.get_setting_value(
                    "report_page_break_strictness", "Standardowa"
                )
                or "Standardowa"
            )
            normalized = str(raw_value).strip().lower()
        except Exception as exc:
            logger.warning("Failed to read report pagination strictness: %s", exc)
            return "standardowa"

        if normalized in ("lagodna", "łagodna", "soft", "low"):
            return "lagodna"
        if normalized in ("ostra", "strict", "high"):
            return "ostra"
        return "standardowa"

    def _should_break_page_for_section(
        self, doc: DocxDocument, items_count: int
    ) -> bool:
        """Check if we should add a page break before a new section."""
        if items_count <= 0:
            return False

        strictness = self._get_page_break_strictness()
        current_elements = len(doc.paragraphs) + sum(
            len(table.rows) for table in doc.tables
        )

        # "Ostra": every next section starts on a new page.
        if strictness == "ostra":
            return current_elements > 0

        policy = {
            "lagodna": {"section_margin": 0, "min_start_lines": 3},
            "standardowa": {"section_margin": 2, "min_start_lines": 4},
            "ostra": {"section_margin": 4, "min_start_lines": 6},
        }
        current_policy = policy[strictness]

        # Simple pagination heuristic based on already generated paragraphs and table rows.
        # It is not exact, but it helps keep each section on one page whenever feasible.
        lines_per_page = 45
        lines_used = current_elements % lines_per_page
        lines_remaining = lines_per_page - lines_used if lines_used else lines_per_page

        # Full section estimate: heading + table header + all rows + policy margin.
        section_lines_needed = items_count + 3 + current_policy["section_margin"]
        if section_lines_needed <= lines_per_page:
            return lines_remaining < section_lines_needed

        # Very large sections cannot fit entirely on one page.
        # In that case, require enough space for heading + table header + first rows.
        return lines_remaining < current_policy["min_start_lines"]

    def _open_file(self, path: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
            logger.debug(f"Successfully opened file: {path}")
        except Exception as e:
            logger.error(f"Error opening file {path}: {str(e)}")
            # Don't raise - this is a non-critical operation


class ReportGenerationError(Exception):
    """Exception raised when report generation fails"""

    pass
