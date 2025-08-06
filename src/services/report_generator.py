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

            # Add sections
            self._add_parts_section(doc, "FORMATKI", formatki)
            self._add_parts_section(doc, "FRONTY", fronty)
            self._add_parts_section(doc, "HDF", hdf)
            self._add_parts_section(doc, "AKCESORIA", akcesoria, accessory=True)

            # Optional notes
            self._add_notes(doc, project)

            # Save
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            file_name = f"projekt_{project.order_number}.docx"
            output_path = out_dir / file_name
            doc.save(str(output_path))
            logger.info(f"Report saved to: {output_path}")

            if auto_open:
                self._open_file(output_path)

            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")

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
            ct = cab.cabinet_type
            qty = cab.quantity

            # Handle standard catalog cabinets
            if ct:
                self._process_catalog_cabinet(cab, ct, qty, formatki, fronty, hdf)
            # Handle ad-hoc cabinets
            elif cab.adhoc_width_mm and cab.adhoc_height_mm and cab.adhoc_depth_mm:
                self._process_adhoc_cabinet(cab, qty, formatki, fronty, hdf)

            # Process accessories for all cabinet types
            self._process_accessories(cab, qty, akcesoria)

        return formatki, fronty, hdf, akcesoria

    def _process_catalog_cabinet(self, cab, ct, qty, formatki, fronty, hdf):
        """Process a catalog cabinet and add its elements to the appropriate lists"""
        # Get the sequence number for this cabinet
        seq_num = getattr(cab, "sequence_number", 0)
        from src.services.project_service import get_circled_number

        seq_symbol = get_circled_number(seq_num)

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
                formatki.append(
                    SimpleNamespace(
                        seq=seq_symbol,
                        name=name,
                        quantity=count * qty,
                        width=int(width),
                        height=int(height),
                        color=cab.body_color,
                        notes="",
                    )
                )

        # Process fronts
        fcount = getattr(ct, "front_count", 0) or 0
        fw = getattr(ct, "front_w_mm", None)
        fh = getattr(ct, "front_h_mm", None)
        if fcount > 0 and fw and fh:
            fronty.append(
                SimpleNamespace(
                    seq=seq_symbol,
                    name="Front",
                    quantity=fcount * qty,
                    width=int(fw),
                    height=int(fh),
                    color=cab.front_color,
                    notes=f"Handle: {cab.handle_type}",
                )
            )

        # Process HDF backs
        if getattr(ct, "hdf_plecy", False):
            bw = getattr(ct, "bok_w_mm", 0)
            bh = getattr(ct, "bok_h_mm", 0)
            hdf.append(
                SimpleNamespace(
                    seq=seq_symbol,
                    name="HDF Plecy",
                    quantity=qty,
                    width=int(bw or 0),
                    height=int(bh or 0),
                    color="",
                    notes="",
                )
            )

    def _process_adhoc_cabinet(self, cab, qty, formatki, fronty, hdf):
        """Process an ad-hoc cabinet and add its elements to the appropriate lists"""
        # Get the sequence number for this cabinet
        seq_num = getattr(cab, "sequence_number", 0)
        from src.services.project_service import get_circled_number

        seq_symbol = get_circled_number(seq_num)

        width = cab.adhoc_width_mm
        height = cab.adhoc_height_mm
        depth = cab.adhoc_depth_mm

        # Sides (boki)
        formatki.append(
            SimpleNamespace(
                seq=seq_symbol,
                name="Bok",
                quantity=2 * qty,
                width=int(depth),
                height=int(height),
                color=cab.body_color,
                notes="Ad-hoc",
            )
        )

        # Top/bottom (wieńce)
        formatki.append(
            SimpleNamespace(
                seq=seq_symbol,
                name="Wieniec",
                quantity=2 * qty,
                width=int(width),
                height=int(depth),
                color=cab.body_color,
                notes="Ad-hoc",
            )
        )

        # Shelf (półka)
        formatki.append(
            SimpleNamespace(
                seq=seq_symbol,
                name="Półka",
                quantity=qty,
                width=int(width - 36),  # Account for sides
                height=int(depth - 20),  # Account for back clearance
                color=cab.body_color,
                notes="Ad-hoc",
            )
        )

        # Front
        fronty.append(
            SimpleNamespace(
                seq=seq_symbol,
                name="Front",
                quantity=qty,
                width=int(width),
                height=int(height),
                color=cab.front_color,
                notes=f"Handle: {cab.handle_type} (Ad-hoc)",
            )
        )

        # HDF back
        hdf.append(
            SimpleNamespace(
                seq=seq_symbol,
                name="HDF Plecy",
                quantity=qty,
                width=int(width - 6),  # Slight adjustment
                height=int(height - 6),  # Slight adjustment
                color="",
                notes="Ad-hoc",
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

        # Left: metadata
        cell_meta = table.rows[0].cells[0]
        p = cell_meta.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        lines = [
            f"Client Name: {project.client_name}",
            f"Client Address: {project.client_address}",
            f"Client Phone: {project.client_phone}",
            f"Client Email: {project.client_email}",
            f"Order Number: {project.order_number}",
            f"Kitchen Type: {project.kitchen_type}",
            f"Report Date: {date.today().isoformat()}",
        ]
        for line in lines:
            run = p.add_run(line + "\n")
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
        doc.add_heading(title, level=2)
        if not parts:
            doc.add_paragraph("Brak pozycji.")
            return

        cols = (
            ["Lp.", "Nazwa akcesorium", "SKU/Kod", "Ilość", "Uwagi"]
            if accessory
            else ["Lp.", "Nazwa", "Ilość", "Wymiary (mm)", "Kolor/Materiał", "Uwagi"]
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
                cells[4].text = getattr(part, "color", "") or ""
                cells[5].text = getattr(part, "notes", "") or ""

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
