import os
import pytest
from datetime import date
from docx import Document
from src.services.report_generator import ReportGenerator
from src.db_schema.orm_models import (
    Project,
    CabinetTemplate,
    CabinetPart,
    ProjectCabinet,
    ProjectCabinetAccessory,
    ProjectCabinetPart,
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
    # CabinetTemplate with basic info
    ct = CabinetTemplate(
        kitchen_type="LOFT",
        name="Standard",
    )

    # Add cabinet parts with different materials to trigger all report sections
    parts = [
        CabinetPart(
            part_name="bok lewy",
            height_mm=720,
            width_mm=500,
            pieces=1,
            material="PLYTA",
            thickness_mm=18,
            wrapping="D",
        ),
        CabinetPart(
            part_name="bok prawy",
            height_mm=720,
            width_mm=500,
            pieces=1,
            material="PLYTA",
            thickness_mm=18,
            wrapping="D",
        ),
        CabinetPart(
            part_name="polka",
            height_mm=480,
            width_mm=500,
            pieces=2,
            material="PLYTA",
            thickness_mm=18,
            wrapping="D",
        ),
        CabinetPart(
            part_name="front",
            height_mm=700,
            width_mm=596,
            pieces=1,
            material="FRONT",
            thickness_mm=16,
            wrapping="DDKK",
        ),
        CabinetPart(
            part_name="plecy",
            height_mm=715,
            width_mm=580,
            pieces=1,
            material="HDF",
            thickness_mm=3,
        ),
    ]
    ct.parts = parts

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
    assert "Klient: ORM Client" in text  # Polish localization
    assert "Nr zamówienia: ORM001" in text  # Polish localization
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
        ["Lp.", "Nazwa", "Ilość", "Wymiary (mm)", "Grub.", "Okleina", "Kolor", "Uwagi"],
        ["Lp.", "Nazwa", "Ilość", "Wymiary (mm)", "Grub.", "Okleina", "Kolor", "Uwagi"],
        ["Lp.", "Nazwa", "Ilość", "Wymiary (mm)", "Grub.", "Okleina", "Kolor", "Uwagi"],
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


@pytest.fixture
def project_with_custom_cabinets():
    """
    Given: a Project with both catalog and custom cabinets
    """
    # Project setup
    project = Project(
        name="Mixed Cabinet Project",
        kitchen_type="LOFT",
        order_number="MIX001",
        client_name="Mixed Client",
        client_address="789 Custom Ave",
        client_phone="555-MIX",
        client_email="mixed@example.com",
        blaty=False,
        cokoly=False,
        uwagi=False,
    )

    # Create catalog template for regular cabinet
    catalog_template = CabinetTemplate(
        kitchen_type="LOFT",
        name="D40",
    )

    # Add parts to catalog template
    catalog_parts = [
        CabinetPart(
            part_name="Catalog Panel",
            height_mm=600,
            width_mm=400,
            pieces=2,
            material="PLYTA",
            thickness_mm=18,
        ),
        CabinetPart(
            part_name="Catalog Front",
            height_mm=598,
            width_mm=398,
            pieces=1,
            material="FRONT",
            thickness_mm=18,
        ),
    ]
    catalog_template.parts = catalog_parts

    # Create catalog cabinet
    catalog_cabinet = ProjectCabinet(
        sequence_number=1,
        body_color="White",
        front_color="Oak",
        handle_type="Standard",
        quantity=1,
        cabinet_type=catalog_template,
    )

    # Create custom cabinet (type_id=NULL)
    custom_cabinet = ProjectCabinet(
        sequence_number=2,
        body_color="Gray",
        front_color="Black",
        handle_type="Push-to-open",
        quantity=2,
        cabinet_type=None,  # Custom cabinet
    )

    # Add custom parts
    custom_parts = [
        ProjectCabinetPart(
            part_name="Custom Side Panel",
            height_mm=720,
            width_mm=560,
            pieces=2,
            material="PLYTA",
            thickness_mm=18,
            comments="Custom side panels",
        ),
        ProjectCabinetPart(
            part_name="Custom Front Door",
            height_mm=718,
            width_mm=558,
            pieces=1,
            material="FRONT",
            thickness_mm=20,
            comments="Custom front door",
        ),
        ProjectCabinetPart(
            part_name="Custom Back Panel",
            height_mm=710,
            width_mm=550,
            pieces=1,
            material="HDF",
            thickness_mm=3,
            comments="Custom HDF back",
        ),
    ]
    custom_cabinet.parts = custom_parts

    # Link cabinets to project
    project.cabinets = [catalog_cabinet, custom_cabinet]

    return project


def test_custom_cabinets_in_report(tmp_path, project_with_custom_cabinets):
    """
    Given: a project with both catalog and custom cabinets
    When: generating a report
    Then: both catalog and custom cabinet parts appear in appropriate sections
    """
    project = project_with_custom_cabinets
    rg = ReportGenerator()
    output = rg.generate(project, output_dir=str(tmp_path), auto_open=False)
    doc = Document(output)

    # Get body tables (excluding header/footer)
    header_tables = doc.sections[0].header.tables
    footer_tables = doc.sections[0].footer.tables
    body_tables = [t for t in doc.tables if t not in header_tables + footer_tables]

    # Should have 3 sections with tables: FORMATKI, FRONTY, HDF
    # (AKCESORIA has no table when empty, just "Brak pozycji." text)
    assert len(body_tables) == 3

    # Check section headings
    headings = [p.text for p in doc.paragraphs if p.style.name == "Heading 2"]
    assert "FORMATKI" in headings
    assert "FRONTY" in headings
    assert "HDF" in headings
    assert "AKCESORIA" in headings

    # Test FORMATKI section (panels)
    formatki_table = body_tables[0]

    # Should have catalog panel + custom side panels
    # Row 1: catalog panel (2 pieces * 1 quantity = 2)
    # Row 2: custom side panels (2 pieces * 2 quantity = 4)
    assert len(formatki_table.rows) >= 3  # Header + at least 2 data rows

    # Find catalog panel row (sequence ①)
    catalog_panel_found = False
    custom_panel_found = False

    for row in formatki_table.rows[1:]:  # Skip header
        cells = row.cells
        seq = cells[0].text.strip()
        name = cells[1].text.strip()
        quantity = cells[2].text.strip()

        if seq == "①" and "Catalog Panel" in name:
            catalog_panel_found = True
            assert quantity == "2"  # 2 pieces * 1 cabinet
        elif seq == "②" and "Custom Side Panel" in name:
            custom_panel_found = True
            assert quantity == "4"  # 2 pieces * 2 cabinets

    assert catalog_panel_found, "Catalog panel not found in FORMATKI"
    assert custom_panel_found, "Custom side panel not found in FORMATKI"

    # Test FRONTY section (fronts)
    fronty_table = body_tables[1]

    # Should have catalog front + custom front
    catalog_front_found = False
    custom_front_found = False

    for row in fronty_table.rows[1:]:  # Skip header
        cells = row.cells
        seq = cells[0].text.strip()
        name = cells[1].text.strip()
        quantity = cells[2].text.strip()
        color = cells[
            6
        ].text.strip()  # Color column (index changed: Lp, Nazwa, Ilość, Wymiary, Grub., Okleina, Kolor, Uwagi)

        if seq == "①" and "Catalog Front" in name:
            catalog_front_found = True
            assert quantity == "1"  # 1 piece * 1 cabinet
            assert "Oak" in color
        elif seq == "②" and "Custom Front Door" in name:
            custom_front_found = True
            assert quantity == "2"  # 1 piece * 2 cabinets
            assert "Black" in color

    assert catalog_front_found, "Catalog front not found in FRONTY"
    assert custom_front_found, "Custom front door not found in FRONTY"

    # Test HDF section
    hdf_table = body_tables[2]

    # Should have custom HDF back panel only
    custom_hdf_found = False

    for row in hdf_table.rows[1:]:  # Skip header
        cells = row.cells
        seq = cells[0].text.strip()
        name = cells[1].text.strip()
        quantity = cells[2].text.strip()

        if seq == "②" and "Custom Back Panel" in name:
            custom_hdf_found = True
            assert quantity == "2"  # 1 piece * 2 cabinets

    assert custom_hdf_found, "Custom HDF back panel not found in HDF section"


def test_custom_cabinet_sequence_numbers(tmp_path, project_with_custom_cabinets):
    """
    Given: a project with custom cabinets having sequence numbers
    When: generating a report
    Then: custom cabinet parts have correct sequence number symbols
    """
    project = project_with_custom_cabinets
    rg = ReportGenerator()
    output = rg.generate(project, output_dir=str(tmp_path), auto_open=False)
    doc = Document(output)

    # Get body tables
    header_tables = doc.sections[0].header.tables
    footer_tables = doc.sections[0].footer.tables
    body_tables = [t for t in doc.tables if t not in header_tables + footer_tables]

    # Check that sequence numbers are properly displayed
    formatki_table = body_tables[0]

    seq_1_found = False  # Catalog cabinet (sequence 1)
    seq_2_found = False  # Custom cabinet (sequence 2)

    for row in formatki_table.rows[1:]:  # Skip header
        cells = row.cells
        seq = cells[0].text.strip()

        if seq == "①":  # Sequence 1
            seq_1_found = True
        elif seq == "②":  # Sequence 2
            seq_2_found = True

    assert seq_1_found, "Sequence number ① not found (catalog cabinet)"
    assert seq_2_found, "Sequence number ② not found (custom cabinet)"
