import os
import pytest
from datetime import date
from docx import Document
from src.services.report_generator import ReportGenerator
from src.db_schema.orm_models import (
    Project,
    CabinetType,
    ProjectCabinet,
    ProjectCabinetAccessory,
    Accessory,
)


@pytest.fixture
def sample_project_orm():
    """
    Given: a SQLAlchemy Project with one cabinet and one accessory
    """
    # Project setup
    project = Project(
        name="ORM Project",
        kitchen_type="LOFT",
        order_number="ORM001",
        client_name="ORM Client",
        client_address="456 ORM Ave",
        client_phone="555-ORM",
        client_email="orm@example.com",
        blaty=True,
        blaty_note="Blaty test",
        cokoly=True,
        cokoly_note="Cokoły test",
        uwagi=True,
        uwagi_note="Uwagi test",
    )
    # CabinetType with various counts and dimensions
    ct = CabinetType(
        kitchen_type="LOFT",
        nazwa="Standard",
        hdf_plecy=True,
        bok_count=1,
        bok_w_mm=400,
        bok_h_mm=800,
        wieniec_count=1,
        wieniec_w_mm=400,
        wieniec_h_mm=50,
        polka_count=2,
        polka_w_mm=300,
        polka_h_mm=20,
        listwa_count=0,
        front_count=1,
        front_w_mm=400,
        front_h_mm=800,
    )
    # One cabinet of quantity 2
    cab = ProjectCabinet(
        sequence_number=1,
        body_color="Oak",
        front_color="Maple",
        handle_type="KROMA",
        quantity=2,
    )
    # assign relationships
    cab.project = project
    cab.cabinet_type = ct
    project.cabinets = [cab]

    # Accessory and link
    acc = Accessory(name="Hinge X", sku="HX123")
    link = ProjectCabinetAccessory(count=4)
    # assign relationships
    link.project_cabinet = cab
    link.accessory = acc
    cab.accessories = [link]

    return project


def test_generate_creates_file(tmp_path, sample_project_orm):
    """
    Given: a ReportGenerator and ORM project
    When: generate is called
    Then: output file exists with correct name
    """
    rg = ReportGenerator()
    output = rg.generate(sample_project_orm, output_dir=str(tmp_path), auto_open=False)
    assert os.path.isfile(output)
    assert output.endswith("projekt_ORM001.docx")


def test_header_contains_orm_metadata(tmp_path, sample_project_orm):
    """
    Given: a generated report
    When: reading the header table
    Then: it contains ORM project metadata and today's date
    """
    rg = ReportGenerator()
    output = rg.generate(sample_project_orm, output_dir=str(tmp_path), auto_open=False)
    doc = Document(output)
    header = doc.sections[0].header
    text = header.tables[0].cell(0, 0).text
    assert "Client Name: ORM Client" in text
    assert "Order Number: ORM001" in text
    assert date.today().isoformat() in text


def test_body_tables_count_and_headers(tmp_path, sample_project_orm):
    """
    Given: a report with derived parts
    When: collecting body tables
    Then: there are four tables titled FORMATKI, FRONTY, HDF, AKCESORIA
    """
    rg = ReportGenerator()
    output = rg.generate(sample_project_orm, output_dir=str(tmp_path), auto_open=False)
    doc = Document(output)

    # ---- Given / When: generated the document ----

    # Then: there should be exactly four Heading 2 titles in this order
    headings = [p.text for p in doc.paragraphs if p.style.name == "Heading 2"]
    assert headings == ["FORMATKI", "FRONTY", "HDF", "AKCESORIA"]

    # And: the four body tables have the correct column headers
    header_tables = doc.sections[0].header.tables
    footer_tables = doc.sections[0].footer.tables
    body_tables = [t for t in doc.tables if t not in header_tables + footer_tables]

    expected_hdr = [
        ["Lp.", "Nazwa", "Ilość", "Wymiary (mm)", "Kolor/Materiał", "Uwagi"],
        ["Lp.", "Nazwa", "Ilość", "Wymiary (mm)", "Kolor/Materiał", "Uwagi"],
        ["Lp.", "Nazwa", "Ilość", "Wymiary (mm)", "Kolor/Materiał", "Uwagi"],
        ["Lp.", "Nazwa akcesorium", "SKU/Kod", "Ilość", "Uwagi"],
    ]
    for table, hdr in zip(body_tables, expected_hdr):
        assert [cell.text for cell in table.rows[0].cells] == hdr


def test_derived_formatki_quantities(tmp_path, sample_project_orm):
    """
    Given: derived FORMATKI table
    When: reading its rows
    Then: the quantities reflect count * cabinet.quantity
    """
    rg = ReportGenerator()
    output = rg.generate(sample_project_orm, output_dir=str(tmp_path), auto_open=False)
    doc = Document(output)

    header_tables = doc.sections[0].header.tables
    footer_tables = doc.sections[0].footer.tables
    body_tables = [t for t in doc.tables if t not in header_tables + footer_tables]
    fmt_table = body_tables[0]

    # Header + 3 data rows (bok, wieniec, polka)
    assert len(fmt_table.rows) == 4

    # Quantity is now in cell index 2 (after "Lp." and "Nazwa")
    quantities = [int(row.cells[2].text) for row in fmt_table.rows[1:]]
    assert quantities == [2, 2, 4]  # (1*2), (1*2), (2*2)


def test_accessories_section(tmp_path, sample_project_orm):
    """
    Given: derived AKCESORIA table
    When: reading its single row
    Then: it matches accessory name, sku, and total count
    """
    rg = ReportGenerator()
    output = rg.generate(sample_project_orm, output_dir=str(tmp_path), auto_open=False)
    doc = Document(output)
    header_tables = doc.sections[0].header.tables
    footer_tables = doc.sections[0].footer.tables
    body_tables = [t for t in doc.tables if t not in header_tables + footer_tables]
    acc_table = body_tables[3]
    assert len(acc_table.rows) == 2
    cells = acc_table.rows[1].cells
    # Name has shifted to index 1, SKU to 2, quantity to 3
    assert cells[1].text == "Hinge X"
    assert cells[2].text == "HX123"
    assert cells[3].text == str(4 * sample_project_orm.cabinets[0].quantity)


def test_notes_and_footer(tmp_path, sample_project_orm):
    """
    Given: a generated report with notes
    When: reading paragraphs and footer
    Then: notes and page field exist
    """
    rg = ReportGenerator()
    output = rg.generate(sample_project_orm, output_dir=str(tmp_path), auto_open=False)
    doc = Document(output)
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Blaty: Blaty test" in text
    assert "Cokoły: Cokoły test" in text
    assert "Uwagi: Uwagi test" in text
    footer = doc.sections[0].footer
    xml = footer.tables[0].cell(0, 1).paragraphs[0]._p.xml
    assert "fldSimple" in xml and "PAGE" in xml
