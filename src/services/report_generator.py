import os
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
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.shared import qn

from src.db_schema.orm_models import Project
from src.services.project_service import ProjectService
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
        # Make sure paths are either None or proper Path objects
        self.program_logo_path = (
            program_logo_path
            if program_logo_path and not isinstance(program_logo_path, Session)
            else None
        )
        self.company_logo_path = (
            company_logo_path
            if company_logo_path and not isinstance(company_logo_path, Session)
            else None
        )
        self.db_session = db_session

        # Initialize ProjectService if session is provided
        self.project_service = ProjectService(db_session) if db_session else None

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

            # Header and footer on every page
            self._add_header(section, project)
            self._add_footer(section)

            # Get sorting preference from settings
            sort_by_color = self._get_sort_preference()

            # Get data for report
            if self.project_service and project.id:
                # Get aggregated elements from service
                logger.debug("Using project service to get aggregated elements")
                elements = self.project_service.get_aggregated_project_elements(
                    project.id
                )
                formatki = self._dict_to_namespace_list(elements["formatki"])
                fronty = self._dict_to_namespace_list(elements["fronty"])
                hdf = self._dict_to_namespace_list(elements["hdf"])
                akcesoria = self._dict_to_namespace_list(elements["akcesoria"])
            else:
                # Fallback to direct data extraction if service not available
                logger.warning(
                    "Project service not available, using direct data extraction"
                )
                formatki, fronty, hdf, akcesoria = self._extract_elements_directly(
                    project
                )

            # Sort parts based on preference
            if sort_by_color:
                formatki = self._sort_by_color(formatki)
                fronty = self._sort_by_color(fronty)
                hdf = self._sort_by_color(hdf)
            # else: keep original order (by LP/sequence)

            # Split formatki by material type
            formatki_plyta_12 = [
                p for p in formatki if getattr(p, "material", "") == "PLYTA 12"
            ]
            formatki_plyta_16 = [
                p for p in formatki if getattr(p, "material", "") == "PLYTA 16"
            ]
            formatki_plyta_18 = [
                p for p in formatki if getattr(p, "material", "") == "PLYTA 18"
            ]
            # Other formatki (legacy or without specific material)
            formatki_other = [
                p
                for p in formatki
                if getattr(p, "material", "")
                not in ("PLYTA 12", "PLYTA 16", "PLYTA 18")
            ]

            # Add sections - split FORMATKI by material type
            if formatki_plyta_12:
                self._add_parts_section(doc, "FORMATKI (PLYTA 12)", formatki_plyta_12)
            if formatki_plyta_16:
                self._add_parts_section(doc, "FORMATKI (PLYTA 16)", formatki_plyta_16)
            if formatki_plyta_18:
                self._add_parts_section(doc, "FORMATKI (PLYTA 18)", formatki_plyta_18)
            if formatki_other:
                self._add_parts_section(doc, "FORMATKI", formatki_other)
            self._add_parts_section(doc, "FRONTY", fronty)
            self._add_parts_section(doc, "HDF", hdf)
            self._add_parts_section(doc, "AKCESORIA", akcesoria, accessory=True)

            # Optional notes
            self._add_notes(doc, project)

            # Save with handling for open files
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            base_name = f"projekt_{project.order_number}"
            output_path = self._get_available_filename(out_dir, base_name)
            doc.save(str(output_path))
            logger.info(f"Report saved to: {output_path}")

            if auto_open:
                self._open_file(output_path)

            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")

    def _get_sort_preference(self) -> bool:
        """Get sorting preference from settings. Returns True if sorting by color."""
        if not self.db_session:
            return True  # Default to color sorting

        try:
            from src.services.settings_service import SettingsService

            settings = SettingsService(self.db_session)
            sort_setting = settings.get_setting_value("report_sort_by", "Kolor")
            return sort_setting == "Kolor"
        except Exception as e:
            logger.warning(f"Could not get sort preference: {e}, defaulting to color")
            return True

    def _sort_by_color(self, items: List[SimpleNamespace]) -> List[SimpleNamespace]:
        """Sort items by color, then by name within each color group."""
        return sorted(
            items,
            key=lambda x: (getattr(x, "color", "") or "", getattr(x, "name", "") or ""),
        )

    def _dict_to_namespace_list(self, dict_list: List[Dict]) -> List[SimpleNamespace]:
        """Convert a list of dictionaries to a list of SimpleNamespace objects"""
        return [SimpleNamespace(**item) for item in dict_list]

    def _extract_elements_directly(
        self, project: Project
    ) -> Tuple[
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
        hdf = []
        akcesoria = []

        # This is a minimal implementation - ideally this logic should be in the service layer
        if not hasattr(project, "cabinets"):
            logger.warning("Project has no cabinets, returning empty lists")
            return formatki, fronty, hdf, akcesoria

        for cab in project.cabinets:
            qty = cab.quantity

            # Process both catalog and custom cabinets
            self._process_cabinet(cab, qty, formatki, fronty, hdf)

            # Process accessories for all cabinet types
            self._process_accessories(cab, qty, akcesoria)

        return formatki, fronty, hdf, akcesoria

    def _process_cabinet(self, cab, qty, formatki, fronty, hdf):
        """Process a cabinet (catalog or custom) and add its parts to the appropriate lists"""
        # Get the sequence number for this cabinet
        seq_num = getattr(cab, "sequence_number", 0)
        from src.services.project_service import get_circled_number

        seq_symbol = get_circled_number(seq_num)

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
                    if "front" in part.part_name.lower():
                        material = "FRONT"
                    elif "hdf" in part.part_name.lower():
                        material = "HDF"
                    else:
                        material = "PLYTA"  # Default for panels
                else:
                    # For custom cabinets, default to PLYTA
                    material = "PLYTA"

            # Determine category based on material (use startswith for variants like "FRONT 18", "HDF 3")
            if material and material.upper().startswith("FRONT"):
                fronty.append(
                    SimpleNamespace(
                        seq=seq_symbol,
                        name=part.part_name,
                        quantity=part_qty,
                        width=part.width_mm,
                        height=part.height_mm,
                        color=cab.front_color,
                        wrapping=getattr(part, "wrapping", "") or "",
                        notes=f"Handle: {cab.handle_type}",
                    )
                )
            elif material and material.upper().startswith("HDF"):
                hdf.append(
                    SimpleNamespace(
                        seq=seq_symbol,
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
        # Get the sequence number for this cabinet
        seq_num = getattr(cab, "sequence_number", 0)
        from src.services.project_service import get_circled_number

        seq_symbol = get_circled_number(seq_num)

        for link in getattr(cab, "accessories", []):
            acc = link.accessory
            total = link.count * qty
            akcesoria.append(
                SimpleNamespace(
                    seq=seq_symbol, name=acc.name, sku=acc.sku, quantity=total, notes=""
                )
            )

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

        # Right: company logo
        cell_logo = table.rows[0].cells[1]
        if self.company_logo_path and os.path.exists(self.company_logo_path):
            run_logo = cell_logo.paragraphs[0].add_run()
            run_logo.add_picture(self.company_logo_path, width=Inches(1))

        # Program logo below
        if self.program_logo_path and os.path.exists(self.program_logo_path):
            p_logo = header.add_paragraph()
            p_logo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run_p = p_logo.add_run()
            run_p.add_picture(self.program_logo_path, width=Inches(0.75))

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
        self, doc: DocxDocument, title: str, parts: List[Any], accessory: bool = False
    ) -> None:
        # Check if we need a page break before adding section
        if parts and self._should_break_page_for_section(doc, len(parts)):
            doc.add_page_break()

        doc.add_heading(title, level=2)
        if not parts:
            doc.add_paragraph("Brak pozycji.")
            return

        cols = (
            ["Lp.", "Nazwa akcesorium", "SKU/Kod", "Ilość", "Uwagi"]
            if accessory
            else [
                "Lp.",
                "Nazwa",
                "Ilość",
                "Wymiary (mm)",
                "Okleina",
                "Kolor",
                "Uwagi",
            ]
        )
        table = doc.add_table(rows=1, cols=len(cols))
        hdr = table.rows[0].cells
        for i, col in enumerate(cols):
            hdr[i].text = col

        for part in parts:
            cells = table.add_row().cells
            # Add sequence number as the first column
            cells[0].text = getattr(part, "seq", "")

            if accessory:
                cells[1].text = part.name
                cells[2].text = getattr(part, "sku", "") or ""
                cells[3].text = str(part.quantity)
                cells[4].text = getattr(part, "notes", "") or ""
            else:
                cells[1].text = part.name
                cells[2].text = str(part.quantity)
                cells[3].text = f"{part.width} x {part.height}"
                cells[4].text = getattr(part, "wrapping", "") or ""
                cells[5].text = getattr(part, "color", "") or ""
                cells[6].text = getattr(part, "notes", "") or ""

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
        """Get an available filename, handling case when file is already open."""
        original_path = output_dir / f"{base_name}.docx"

        # Try to save to original path first
        try:
            # Test if we can write to the file by opening it
            with open(original_path, "ab"):
                pass  # Just test write access
            return original_path
        except (PermissionError, OSError):
            # File is likely open, try alternative names
            for i in range(1, 100):  # Try up to 99 alternatives
                alt_path = output_dir / f"{base_name}_({i}).docx"
                try:
                    with open(alt_path, "ab"):
                        pass  # Test write access
                    logger.info(
                        f"Original file appears to be open, using alternative: {alt_path.name}"
                    )
                    return alt_path
                except (PermissionError, OSError):
                    continue

            # If all alternatives fail, raise the original error
            raise PermissionError(
                f"Nie można zapisać raportu. Plik '{base_name}.docx' "
                "jest prawdopodobnie otwarty w innym programie. "
                "Zamknij plik i spróbuj ponownie."
            )

    def _should_break_page_for_section(
        self, doc: DocxDocument, items_count: int
    ) -> bool:
        """Check if we should add a page break before a new section."""
        if items_count == 0:
            return False

        # Rough calculation: if we have less than 6 lines remaining on page
        # (header + 2 table header rows + at least 1 data row + some margin)
        # This is a simple heuristic - Word's actual pagination is more complex
        current_elements = len(doc.paragraphs) + sum(
            len(table.rows) for table in doc.tables
        )

        # Assume ~50 lines per page, break if we have less than 6 lines left
        lines_used = current_elements % 50
        lines_remaining = 50 - lines_used

        # Need at least: title (1) + table header (1) + 1 data row (1) + margin (3) = 6 lines
        min_lines_needed = 6

        return lines_remaining < min_lines_needed

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
