import os
import sys
import subprocess
from pathlib import Path
from datetime import date
from typing import List, Tuple, Optional, Any
from types import SimpleNamespace

from docx import Document
from docx.document import Document as DocxDocument
from docx.section import Section
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.shared import qn

from src.db_schema.orm_models import Project, Accessory


class ReportGenerator:
    """
    Generates a .docx report for a Cabplanner project entirely via code.
    Supports optional program and company logos, repeating headers/footers with page numbers.
    Automatically derives parts from SQLAlchemy ORM instances.
    """

    def __init__(
        self,
        program_logo_path: Optional[Path] = None,
        company_logo_path: Optional[Path] = None,
    ) -> None:
        self.program_logo_path: Optional[Path] = program_logo_path
        self.company_logo_path: Optional[Path] = company_logo_path

    def generate(
        self,
        project: Project,
        output_dir: str = "documents/reports",
        auto_open: bool = True,
    ) -> str:
        """
        Generate the .docx report and return its file path.
        """
        doc: DocxDocument = Document()
        section: Section = doc.sections[0]
        section.different_first_page_header_footer = False

        # Header and footer on every page
        self._add_header(section, project)
        self._add_footer(section)

        # Derive parts either from ORM or from attributes
        if hasattr(project, "cabinets"):
            formatki, fronty, hdf, akcesoria = self._derive_from_orm(project)
        else:
            formatki = getattr(project, "formatki", []) or []
            fronty = getattr(project, "fronty", []) or []
            hdf = getattr(project, "hdf", []) or []
            akcesoria = getattr(project, "akcesoria", []) or []

        # Add sections
        self._add_parts_section(doc, "FORMATKI", formatki)
        self._add_parts_section(doc, "FRONTY", fronty)
        self._add_parts_section(doc, "HDF", hdf)
        self._add_parts_section(doc, "AKCESORIA", akcesoria, accessory=True)

        # Optional notes
        self._add_notes(doc, project)

        # Save
        out_dir: Path = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        file_name: str = f"projekt_{project.order_number}.docx"
        output_path: Path = out_dir / file_name
        doc.save(str(output_path))

        if auto_open:
            self._open_file(output_path)
        return str(output_path)

    def _derive_from_orm(
        self, project: Project
    ) -> Tuple[
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
        List[SimpleNamespace],
    ]:
        """
        Extract parts lists from SQLAlchemy project.cabinets relationship.
        """
        formatki: List[SimpleNamespace] = []
        fronty: List[SimpleNamespace] = []
        hdf: List[SimpleNamespace] = []
        akcesoria: List[SimpleNamespace] = []

        for cab in project.cabinets:
            ct = cab.cabinet_type
            qty = cab.quantity

            # Main panels
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
                            name=name,
                            quantity=count * qty,
                            width=int(width),
                            height=int(height),
                            color=cab.body_color,
                            notes="",
                        )
                    )

            # Fronts
            fcount = getattr(ct, "front_count", 0) or 0
            fw = getattr(ct, "front_w_mm", None)
            fh = getattr(ct, "front_h_mm", None)
            if fcount > 0 and fw and fh:
                fronty.append(
                    SimpleNamespace(
                        name="Front",
                        quantity=fcount * qty,
                        width=int(fw),
                        height=int(fh),
                        color=cab.front_color,
                        notes=f"Handle: {cab.handle_type}",
                    )
                )

            # HDF backs
            if getattr(ct, "hdf_plecy", False):
                bw = cab.adhoc_width_mm or getattr(ct, "bok_w_mm", 0)
                bh = cab.adhoc_height_mm or getattr(ct, "bok_h_mm", 0)
                hdf.append(
                    SimpleNamespace(
                        name="HDF Plecy",
                        quantity=qty,
                        width=int(bw or 0),
                        height=int(bh or 0),
                        color="",
                        notes="",
                    )
                )

            # Accessories
            for link in getattr(cab, "accessories", []):
                acc: Accessory = link.accessory
                total: int = link.count * qty
                akcesoria.append(
                    SimpleNamespace(
                        name=acc.name, sku=acc.sku, quantity=total, notes=""
                    )
                )

        return formatki, fronty, hdf, akcesoria

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
            ["Nazwa akcesorium", "SKU/Kod", "Ilość", "Uwagi"]
            if accessory
            else ["Nazwa", "Ilość", "Wymiary (mm)", "Kolor/Materiał", "Uwagi"]
        )
        table = doc.add_table(rows=1, cols=len(cols))
        hdr = table.rows[0].cells
        for i, col in enumerate(cols):
            hdr[i].text = col

        for part in parts:
            cells = table.add_row().cells
            if accessory:
                cells[0].text = part.name
                cells[1].text = getattr(part, "sku", "") or ""
                cells[2].text = str(part.quantity)
                cells[3].text = getattr(part, "notes", "") or ""
            else:
                cells[0].text = part.name
                cells[1].text = str(part.quantity)
                cells[2].text = f"{part.width} x {part.height}"
                cells[3].text = getattr(part, "color", "") or ""
                cells[4].text = getattr(part, "notes", "") or ""

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
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
