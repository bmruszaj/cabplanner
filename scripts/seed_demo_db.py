from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db_migration import upgrade_database
from src.db_schema.orm_models import Project
from src.services.color_palette_service import ColorPaletteService
from src.services.formula_constants_service import FormulaConstantsService
from src.services.formula_service import FormulaService
from src.services.project_service import ProjectService
from src.services.report_generator import ReportGenerator
from src.services.settings_service import SettingsService
from src.services.template_service import TemplateService


DB_PATH = ROOT / "cabplanner.db"


def seed_settings(session: Session) -> None:
    settings = SettingsService(session)
    demo_values = {
        "auto_update_enabled": True,
        "auto_update_frequency": "Co tydzie\u0144",
        "create_shortcut_on_start": True,
        "default_kitchen_type": "LOFT",
        "default_project_path": str(ROOT / "documents"),
        "report_page_break_strictness": "Standardowa",
        "report_program_logo_variant": "Kolorowe",
        "dark_mode": False,
        "company_name": "Pracownia Mebli Forma",
        "company_address": "ul. Przemyslowa 14, 02-231 Warszawa",
        "company_phone": "+48 601 234 567",
        "company_email": "kontakt@forma-meble.pl",
        "company_website": "https://forma-meble.pl",
        "company_tax_id": "5252874103",
        "company_logo_path": "",
    }
    for key, value in demo_values.items():
        settings.set_setting(key, value)


def seed_formula_constants(session: Session) -> None:
    service = FormulaConstantsService(session)
    constants = [
        ("plyta_thickness", 18.0, "float", "thickness", "Standard board thickness"),
        ("hdf_thickness", 3.0, "float", "thickness", "HDF back thickness"),
        ("base_height", 720.0, "float", "dimensions", "Base cabinet height"),
        ("base_depth", 560.0, "float", "dimensions", "Base cabinet depth"),
        ("upper_height", 720.0, "float", "dimensions", "Upper cabinet height"),
        ("upper_depth", 320.0, "float", "dimensions", "Upper cabinet depth"),
        ("tall_height", 2020.0, "float", "dimensions", "Tall cabinet height"),
        ("tall_depth", 560.0, "float", "dimensions", "Tall cabinet depth"),
        ("front_gap_top", 2.0, "float", "gaps", "Top front gap"),
        ("front_gap_bottom", 2.0, "float", "gaps", "Bottom front gap"),
        ("front_gap_side", 2.0, "float", "gaps", "Side front gap"),
        ("back_play_h", 0.0, "float", "clearance", "Back panel height play"),
        ("back_play_w", 0.0, "float", "clearance", "Back panel width play"),
        ("board_back_play_h", 2.0, "float", "clearance", "Board back height play"),
        ("board_back_play_w", 2.0, "float", "clearance", "Board back width play"),
        ("shelf_back_clear", 10.0, "float", "clearance", "Shelf back clearance"),
        ("rail_height", 100.0, "float", "dimensions", "Rail height"),
        ("drawer_inter_gap", 2.0, "float", "gaps", "Gap between drawer fronts"),
        ("s1_drawer_h", 572.0, "float", "drawers", "Single drawer front height"),
        ("s2_top_h", 141.0, "float", "drawers", "S2 top drawer height"),
        ("s2_bottom_h", 572.0, "float", "drawers", "S2 bottom drawer height"),
        ("s3_top_h", 140.0, "float", "drawers", "S3 top drawer height"),
        ("s3_middle_h", 283.0, "float", "drawers", "S3 middle drawer height"),
        ("s3_bottom_h", 572.0, "float", "drawers", "S3 bottom drawer height"),
        ("min_cut_mm", 10.0, "float", "validation", "Minimum cut size"),
    ]
    for row in constants:
        service.set(*row)


def seed_colors(session: Session) -> None:
    palette = ColorPaletteService(session)
    palette.ensure_seeded()

    demo_colors = [
        ("Kaszmir Mat", "#D7CFC7"),
        ("Szalwia Mat", "#9EAD97"),
        ("Dab Hamilton", "#9B7653"),
        ("Orzech Naturalny", "#7B563C"),
        ("Granat Nocny", "#243B5A"),
        ("Greige", "#C8BFB2"),
    ]
    for name, hex_code in demo_colors:
        try:
            palette.add_user_color(name, hex_code)
        except ValueError:
            continue
    palette.sync_runtime_color_map()


def create_template(
    template_service: TemplateService,
    name: str,
    parts: list[dict],
    accessories: list[tuple[str, int]],
    kitchen_type: str = "LOFT",
) -> None:
    template = template_service.create_template(kitchen_type=kitchen_type, name=name)
    for part in parts:
        template_service.add_part(cabinet_type_id=template.id, **part)
    for accessory_name, count in accessories:
        template_service.add_accessory_by_name(
            cabinet_type_id=template.id, name=accessory_name, count=count
        )


def make_base_template(
    width_mm: int,
    *,
    depth_mm: int = 560,
    height_mm: int = 720,
    front_heights: list[int] | None = None,
    front_count: int = 1,
    shelf_count: int = 1,
    sink: bool = False,
    glass: bool = False,
    body_material: str = "PLYTA 18",
    accessories: list[tuple[str, int]] | None = None,
) -> tuple[list[dict], list[tuple[str, int]]]:
    front_heights = front_heights or [713]
    accessories = list(accessories or [])
    inner_width = max(width_mm - 36, 100)
    panel_depth = max(depth_mm - 3, 100)
    back_height = max(height_mm - 5, 100)
    back_width = max(width_mm - 5, 100)

    parts = [
        {
            "part_name": "bok lewy",
            "height_mm": height_mm,
            "width_mm": panel_depth,
            "pieces": 1,
            "material": body_material,
            "wrapping": "D",
            "comments": None,
        },
        {
            "part_name": "bok prawy",
            "height_mm": height_mm,
            "width_mm": panel_depth,
            "pieces": 1,
            "material": body_material,
            "wrapping": "D",
            "comments": None,
        },
        {
            "part_name": "wieniec dolny",
            "height_mm": inner_width,
            "width_mm": panel_depth,
            "pieces": 1,
            "material": body_material,
            "wrapping": "D",
            "comments": None,
        },
        {
            "part_name": "wieniec gorny",
            "height_mm": inner_width,
            "width_mm": panel_depth,
            "pieces": 1,
            "material": body_material,
            "wrapping": "D",
            "comments": None,
        },
        {
            "part_name": "listwa przednia",
            "height_mm": inner_width,
            "width_mm": 100,
            "pieces": 1,
            "material": body_material,
            "wrapping": "D",
            "comments": None,
        },
        {
            "part_name": "listwa tylna",
            "height_mm": inner_width,
            "width_mm": 100,
            "pieces": 1,
            "material": body_material,
            "wrapping": "D",
            "comments": None,
        },
        {
            "part_name": "HDF",
            "height_mm": back_height,
            "width_mm": back_width,
            "pieces": 1,
            "material": "HDF",
            "wrapping": None,
            "comments": None,
        },
    ]

    if not sink:
        for index in range(shelf_count):
            parts.append(
                {
                    "part_name": "polka" if shelf_count == 1 else f"polka {index + 1}",
                    "height_mm": inner_width,
                    "width_mm": max(depth_mm - 13, 80),
                    "pieces": 1,
                    "material": body_material,
                    "wrapping": "D",
                    "comments": None,
                }
            )

    if glass:
        glass_front_width = max((width_mm - 8) // 2, 120)
        parts.extend(
            [
                {
                    "part_name": "witryna lewa",
                    "height_mm": 713,
                    "width_mm": glass_front_width,
                    "pieces": 1,
                    "material": "WITRYNA",
                    "wrapping": "DDKK",
                    "comments": "Rama aluminiowa czarna",
                },
                {
                    "part_name": "witryna prawa",
                    "height_mm": 713,
                    "width_mm": glass_front_width,
                    "pieces": 1,
                    "material": "WITRYNA",
                    "wrapping": "DDKK",
                    "comments": "Rama aluminiowa czarna",
                },
                {
                    "part_name": "polka szklana",
                    "height_mm": inner_width,
                    "width_mm": max(depth_mm - 20, 80),
                    "pieces": 2,
                    "material": "POLKA SZKLANA",
                    "wrapping": None,
                    "comments": "Szklo hartowane",
                },
            ]
        )
    else:
        if front_count == 1 and len(front_heights) == 1:
            parts.append(
                {
                    "part_name": "front",
                    "height_mm": front_heights[0],
                    "width_mm": max(width_mm - 4, 80),
                    "pieces": 1,
                    "material": "FRONT",
                    "wrapping": "DDKK",
                    "comments": None,
                }
            )
        elif front_count == 2 and len(front_heights) == 1:
            front_width = max((width_mm - 6) // 2, 80)
            parts.extend(
                [
                    {
                        "part_name": "front lewy",
                        "height_mm": front_heights[0],
                        "width_mm": front_width,
                        "pieces": 1,
                        "material": "FRONT",
                        "wrapping": "DDKK",
                        "comments": None,
                    },
                    {
                        "part_name": "front prawy",
                        "height_mm": front_heights[0],
                        "width_mm": front_width,
                        "pieces": 1,
                        "material": "FRONT",
                        "wrapping": "DDKK",
                        "comments": None,
                    },
                ]
            )
        else:
            for index, front_height in enumerate(front_heights, start=1):
                parts.append(
                    {
                        "part_name": f"front szuflady {index}",
                        "height_mm": front_height,
                        "width_mm": max(width_mm - 4, 80),
                        "pieces": 1,
                        "material": "FRONT",
                        "wrapping": "DDKK",
                        "comments": None,
                    }
                )

    return parts, accessories


def make_upper_template(
    width_mm: int,
    *,
    height_mm: int = 720,
    depth_mm: int = 320,
    shelf_count: int = 1,
    glass: bool = False,
    body_material: str = "PLYTA 18",
    accessories: list[tuple[str, int]] | None = None,
) -> tuple[list[dict], list[tuple[str, int]]]:
    return make_base_template(
        width_mm,
        depth_mm=depth_mm,
        height_mm=height_mm,
        front_heights=[height_mm - 4],
        front_count=1 if not glass else 2,
        shelf_count=shelf_count,
        sink=False,
        glass=glass,
        body_material=body_material,
        accessories=accessories,
    )


def seed_templates(session: Session) -> None:
    template_service = TemplateService(session)

    catalog = [
        (
            "D30",
            *make_base_template(
                300,
                accessories=[
                    ("Zawias Blum Clip Top 110", 2),
                    ("Noga regulowana 100 mm", 4),
                    ("Uchwyt krawedziowy 160 mm", 1),
                ],
            ),
        ),
        (
            "D45",
            *make_base_template(
                450,
                accessories=[
                    ("Zawias Blum Clip Top 110", 2),
                    ("Noga regulowana 100 mm", 4),
                    ("Uchwyt krawedziowy 160 mm", 1),
                ],
            ),
        ),
        (
            "D60",
            *make_base_template(
                600,
                accessories=[
                    ("Zawias Blum Clip Top 110", 2),
                    ("Noga regulowana 100 mm", 4),
                    ("Uchwyt krawedziowy 160 mm", 1),
                    ("Polkownik metalowy", 4),
                ],
            ),
        ),
        (
            "D80",
            *make_base_template(
                800,
                front_count=2,
                accessories=[
                    ("Zawias Blum Clip Top 110", 4),
                    ("Noga regulowana 100 mm", 4),
                    ("Uchwyt krawedziowy 160 mm", 2),
                    ("Polkownik metalowy", 4),
                ],
            ),
        ),
        (
            "D90",
            *make_base_template(
                900,
                front_count=2,
                accessories=[
                    ("Zawias Blum Clip Top 110", 4),
                    ("Noga regulowana 100 mm", 4),
                    ("Uchwyt krawedziowy 160 mm", 2),
                ],
            ),
        ),
        (
            "D60Z",
            *make_base_template(
                600,
                front_count=2,
                shelf_count=0,
                sink=True,
                accessories=[
                    ("Zawias Blum Clip Top 110", 4),
                    ("Noga regulowana 100 mm", 4),
                    ("Syfon oszczedzajacy miejsce", 1),
                    ("Mata aluminiowa pod zlew", 1),
                ],
            ),
        ),
        (
            "D60S3",
            *make_base_template(
                600,
                front_heights=[140, 283, 283],
                front_count=3,
                shelf_count=0,
                accessories=[
                    ("Prowadnica TandemBox 500 mm", 3),
                    ("Noga regulowana 100 mm", 4),
                    ("Uchwyt krawedziowy 160 mm", 3),
                    ("Wklad na sztucce 600", 1),
                ],
            ),
        ),
        (
            "D80S2 comfortbox",
            *make_base_template(
                800,
                front_heights=[284, 429],
                front_count=2,
                shelf_count=0,
                accessories=[
                    ("Prowadnica ComfortBox 500 mm", 2),
                    ("Reling wewnetrzny do szuflady", 2),
                    ("Noga regulowana 100 mm", 4),
                    ("Uchwyt krawedziowy 160 mm", 2),
                ],
            ),
        ),
        (
            "DNZ105",
            *make_base_template(
                1050,
                height_mm=2020,
                depth_mm=560,
                front_count=2,
                shelf_count=4,
                accessories=[
                    ("Zawias Blum Clip Top 110", 6),
                    ("Noga regulowana 100 mm", 6),
                    ("Uchwyt krawedziowy 160 mm", 2),
                ],
            ),
        ),
        (
            "G30",
            *make_upper_template(
                300,
                accessories=[
                    ("Zawias Blum Clip Top 110", 2),
                    ("Zawieszka scienna Camar", 2),
                    ("Uchwyt krawedziowy 160 mm", 1),
                ],
            ),
        ),
        (
            "G40",
            *make_upper_template(
                400,
                accessories=[
                    ("Zawias Blum Clip Top 110", 2),
                    ("Zawieszka scienna Camar", 2),
                    ("Uchwyt krawedziowy 160 mm", 1),
                ],
            ),
        ),
        (
            "G60",
            *make_upper_template(
                600,
                shelf_count=2,
                accessories=[
                    ("Zawias Blum Clip Top 110", 2),
                    ("Zawieszka scienna Camar", 2),
                    ("Uchwyt krawedziowy 160 mm", 1),
                ],
            ),
        ),
        (
            "G60G",
            *make_upper_template(
                600,
                glass=True,
                shelf_count=0,
                accessories=[
                    ("Zawias Blum Clip Top 110", 4),
                    ("Zawieszka scienna Camar", 2),
                    ("Uchwyt krawedziowy 160 mm", 2),
                ],
            ),
        ),
        (
            "G80",
            *make_upper_template(
                800,
                shelf_count=2,
                accessories=[
                    ("Zawias Blum Clip Top 110", 4),
                    ("Zawieszka scienna Camar", 2),
                    ("Uchwyt krawedziowy 160 mm", 2),
                ],
            ),
        ),
        (
            "G80 ociekacz",
            *make_upper_template(
                800,
                shelf_count=0,
                accessories=[
                    ("Zawias Blum Clip Top 110", 4),
                    ("Zawieszka scienna Camar", 2),
                    ("Ociekacz aluminiowy 800", 1),
                    ("Uchwyt krawedziowy 160 mm", 2),
                ],
            ),
        ),
        (
            "N60 nadstawka",
            *make_upper_template(
                600,
                height_mm=360,
                depth_mm=320,
                shelf_count=1,
                body_material="PLYTA 16",
                accessories=[("Podnosnik Aventos HK-S", 1)],
            ),
        ),
    ]

    for name, parts, accessories in catalog:
        create_template(template_service, name, parts, accessories)


def set_project_dates(session: Session, order_number: str, created_at: datetime) -> None:
    project = session.scalar(select(Project).where(Project.order_number == order_number))
    if not project:
        raise RuntimeError(f"Project {order_number} was not created")
    project.created_at = created_at
    project.updated_at = created_at + timedelta(days=1)
    session.commit()


def template_id_map(session: Session) -> dict[str, int]:
    from src.db_schema.orm_models import CabinetTemplate

    return {
        name: template_id
        for template_id, name in session.execute(
            select(CabinetTemplate.id, CabinetTemplate.name)
        ).all()
    }


def seed_projects(session: Session) -> None:
    project_service = ProjectService(session)
    formula_service = FormulaService(session)
    templates = template_id_map(session)

    projects = [
        {
            "project": {
                "name": "Apartament Mokotow - kuchnia z wyspa",
                "order_number": "CP-2026-001",
                "kitchen_type": "LOFT",
                "client_name": "Anna i Michal Kowalscy",
                "client_address": "ul. Bokserska 8/41, Warszawa",
                "client_phone": "+48 600 201 202",
                "client_email": "kowalscy@example.com",
                "blaty": True,
                "blaty_note": "Spiek kwarcowy 20 mm, kolor jasny piaskowy.",
                "cokoly": True,
                "cokoly_note": "Cokol aluminiowy czarny, wysokosc 100 mm.",
                "uwagi": True,
                "uwagi_note": "Montaz na dwa etapy: korpusy i po tygodniu AGD.",
                "flag_notes": "Priorytet do zdjec i prezentacji handlowych.",
            },
            "created_at": datetime(2026, 3, 4, 10, 15, tzinfo=timezone.utc),
            "standard_cabinets": [
                ("D60Z", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
                ("D80S2 comfortbox", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
                ("D60S3", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
                ("D90", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
                ("D45", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
                ("G80 ociekacz", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
                ("G60G", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
                ("G60", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 2),
                ("N60 nadstawka", "Kaszmir Mat", "Orzech Naturalny", "Uchwyt frezowany", 1),
            ],
            "custom_cabinets": [
                {
                    "template_name": "D90",
                    "width_mm": 900,
                    "height_mm": 760,
                    "depth_mm": 580,
                    "body_color": "Kaszmir Mat",
                    "front_color": "Orzech Naturalny",
                    "handle_type": "Push-to-open",
                    "quantity": 1,
                    "accessories": [
                        {"name": "Odbojnik Push-to-Open", "count": 2},
                        {"name": "Listwa cokolowa czarna", "count": 1},
                    ],
                }
            ],
        },
        {
            "project": {
                "name": "Dom Wilanow - kuchnia klasy premium",
                "order_number": "CP-2026-002",
                "kitchen_type": "PARIS",
                "client_name": "Monika Zielinska Design",
                "client_address": "ul. Hlonda 12, Warszawa",
                "client_phone": "+48 502 111 909",
                "client_email": "monika.zielinska@example.com",
                "blaty": True,
                "blaty_note": "Blat konglomerat 12 mm i panel scienny przy wyspie.",
                "cokoly": True,
                "cokoly_note": "Cokol lakierowany w kolorze frontu.",
                "uwagi": True,
                "uwagi_note": "Wymagana dokladna koordynacja z oswietleniem LED.",
                "flag_notes": "Projekt pokazowy z mocnym kontrastem kolorystycznym.",
            },
            "created_at": datetime(2026, 2, 25, 9, 30, tzinfo=timezone.utc),
            "standard_cabinets": [
                ("D60", "Bialy", "Grafit", "Czarny reling", 2),
                ("D80", "Bialy", "Grafit", "Czarny reling", 1),
                ("D60S3", "Bialy", "Grafit", "Czarny reling", 1),
                ("D30", "Bialy", "Grafit", "Czarny reling", 1),
                ("G80", "Bialy", "Grafit", "Czarny reling", 1),
                ("G60G", "Bialy", "Grafit", "Czarny reling", 1),
                ("G40", "Bialy", "Grafit", "Czarny reling", 2),
            ],
            "custom_cabinets": [],
        },
        {
            "project": {
                "name": "Studio Praga - kompaktowy aneks",
                "order_number": "CP-2026-003",
                "kitchen_type": "WINO",
                "client_name": "Karolina Nowak",
                "client_address": "ul. Szwedzka 6/18, Warszawa",
                "client_phone": "+48 664 810 202",
                "client_email": "karolina.nowak@example.com",
                "blaty": True,
                "blaty_note": "Laminat supermat odporny na odciski.",
                "cokoly": True,
                "cokoly_note": "Cokol PCV grafit.",
                "uwagi": False,
                "uwagi_note": "",
                "flag_notes": "Kompaktowy projekt pod male mieszkanie inwestycyjne.",
            },
            "created_at": datetime(2026, 2, 12, 14, 0, tzinfo=timezone.utc),
            "standard_cabinets": [
                ("D45", "Szalwia Mat", "Bialy", "Push-to-open", 1),
                ("D60S3", "Szalwia Mat", "Bialy", "Push-to-open", 1),
                ("D60Z", "Szalwia Mat", "Bialy", "Push-to-open", 1),
                ("G60", "Szalwia Mat", "Bialy", "Push-to-open", 2),
                ("G30", "Szalwia Mat", "Bialy", "Push-to-open", 1),
            ],
            "custom_cabinets": [],
        },
        {
            "project": {
                "name": "Rezydencja Konstancin - zabudowa gospodarcza",
                "order_number": "CP-2026-004",
                "kitchen_type": "LOFT",
                "client_name": "B2B Home Investment",
                "client_address": "ul. Pilsudskiego 17, Konstancin-Jeziorna",
                "client_phone": "+48 501 998 445",
                "client_email": "koordynacja@b2bhome.example.com",
                "blaty": False,
                "blaty_note": "",
                "cokoly": True,
                "cokoly_note": "Cokol w kolorze korpusu, z maskownica pralni.",
                "uwagi": True,
                "uwagi_note": "Wymagana wentylacja dla suszarki w slupku.",
                "flag_notes": "Projekt techniczny z przewaga wysokich korpusow.",
            },
            "created_at": datetime(2026, 1, 28, 11, 10, tzinfo=timezone.utc),
            "standard_cabinets": [
                ("DNZ105", "Dab Hamilton", "Greige", "Uchwyt krawedziowy 160 mm", 1),
                ("D80", "Dab Hamilton", "Greige", "Uchwyt krawedziowy 160 mm", 1),
                ("D60", "Dab Hamilton", "Greige", "Uchwyt krawedziowy 160 mm", 1),
                ("G80", "Dab Hamilton", "Greige", "Uchwyt krawedziowy 160 mm", 1),
                ("N60 nadstawka", "Dab Hamilton", "Greige", "Uchwyt krawedziowy 160 mm", 2),
            ],
            "custom_cabinets": [
                {
                    "template_name": "DNZ105",
                    "width_mm": 1100,
                    "height_mm": 2100,
                    "depth_mm": 580,
                    "body_color": "Dab Hamilton",
                    "front_color": "Greige",
                    "handle_type": "Push-to-open",
                    "quantity": 1,
                    "accessories": [{"name": "Odbojnik Push-to-Open", "count": 4}],
                }
            ],
        },
        {
            "project": {
                "name": "Showroom Cabplanner - zestaw demonstracyjny",
                "order_number": "CP-2026-005",
                "kitchen_type": "LOFT",
                "client_name": "Cabplanner Demo",
                "client_address": "ul. Cybernetyki 3, Warszawa",
                "client_phone": "+48 600 000 999",
                "client_email": "demo@cabplanner.app",
                "blaty": True,
                "blaty_note": "Trzy probki blatow do porownania kolorystycznego.",
                "cokoly": True,
                "cokoly_note": "Dwie wersje: czarny mat i aluminium szczotkowane.",
                "uwagi": True,
                "uwagi_note": "Projekt przeznaczony do screenshotow i prezentacji handlowych.",
                "flag_notes": "Najbardziej reprezentacyjny projekt w bazie demo.",
            },
            "created_at": datetime(2026, 1, 9, 15, 45, tzinfo=timezone.utc),
            "standard_cabinets": [
                ("D60", "Kaszmir Mat", "Granat Nocny", "Uchwyt krawedziowy 160 mm", 1),
                ("D80S2 comfortbox", "Kaszmir Mat", "Granat Nocny", "Uchwyt krawedziowy 160 mm", 1),
                ("G60G", "Kaszmir Mat", "Granat Nocny", "Uchwyt krawedziowy 160 mm", 1),
                ("G80 ociekacz", "Kaszmir Mat", "Granat Nocny", "Uchwyt krawedziowy 160 mm", 1),
                ("N60 nadstawka", "Kaszmir Mat", "Granat Nocny", "Uchwyt krawedziowy 160 mm", 1),
            ],
            "custom_cabinets": [
                {
                    "template_name": "D60",
                    "width_mm": 640,
                    "height_mm": 760,
                    "depth_mm": 600,
                    "body_color": "Kaszmir Mat",
                    "front_color": "Granat Nocny",
                    "handle_type": "Push-to-open",
                    "quantity": 1,
                    "accessories": [
                        {"name": "Odbojnik Push-to-Open", "count": 2},
                        {"name": "Polkownik metalowy", "count": 4},
                    ],
                }
            ],
        },
    ]

    for payload in projects:
        project = project_service.create_project(**payload["project"])

        for template_name, body_color, front_color, handle_type, quantity in payload[
            "standard_cabinets"
        ]:
            project_service.add_cabinet(
                project.id,
                sequence_number=project_service.get_next_cabinet_sequence(project.id),
                type_id=templates[template_name],
                body_color=body_color,
                front_color=front_color,
                handle_type=handle_type,
                quantity=quantity,
            )

        for custom in payload["custom_cabinets"]:
            parts = [
                {
                    "part_name": plan.part_name,
                    "height_mm": plan.height_mm,
                    "width_mm": plan.width_mm,
                    "pieces": plan.pieces,
                    "material": plan.material,
                    "wrapping": plan.wrapping,
                    "comments": plan.comments,
                }
                for plan in formula_service.compute_parts(
                    custom["template_name"],
                    custom["width_mm"],
                    custom["height_mm"],
                    custom["depth_mm"],
                )
            ]
            project_service.add_custom_cabinet(
                project.id,
                sequence_number=project_service.get_next_cabinet_sequence(project.id),
                body_color=custom["body_color"],
                front_color=custom["front_color"],
                handle_type=custom["handle_type"],
                quantity=custom["quantity"],
                custom_parts=parts,
                custom_accessories=custom["accessories"],
                calc_context={
                    "template_name": custom["template_name"],
                    "width_mm": custom["width_mm"],
                    "height_mm": custom["height_mm"],
                    "depth_mm": custom["depth_mm"],
                },
            )

        set_project_dates(session, project.order_number, payload["created_at"])


def validate_seeded_db(db_path: Path) -> None:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    smoke_dir = Path(tempfile.gettempdir()) / "cabplanner_demo_report_smoke"
    if smoke_dir.exists():
        shutil.rmtree(smoke_dir)
    smoke_dir.mkdir(parents=True, exist_ok=True)

    try:
        from src.db_schema.orm_models import CabinetTemplate, FormulaConstant, ProjectCabinet

        project_count = session.scalar(select(func.count()).select_from(Project))
        cabinet_count = session.scalar(select(func.count()).select_from(ProjectCabinet))
        template_count = session.scalar(select(func.count()).select_from(CabinetTemplate))
        constant_count = session.scalar(select(func.count()).select_from(FormulaConstant))

        if project_count < 5:
            raise RuntimeError(f"Expected at least 5 projects, got {project_count}")
        if cabinet_count < 25:
            raise RuntimeError(f"Expected at least 25 cabinets, got {cabinet_count}")
        if template_count < 12:
            raise RuntimeError(f"Expected at least 12 templates, got {template_count}")
        if constant_count < 20:
            raise RuntimeError(f"Expected at least 20 constants, got {constant_count}")

        flagship = session.scalar(
            select(Project).where(Project.order_number == "CP-2026-001")
        )
        if not flagship:
            raise RuntimeError("Flagship project CP-2026-001 is missing")

        generator = ReportGenerator(db_session=session)
        output_path = generator.generate(
            flagship, output_dir=str(smoke_dir), auto_open=False
        )
        if not Path(output_path).exists():
            raise RuntimeError("Report smoke test did not create a DOCX file")
    finally:
        session.close()
        engine.dispose()
        shutil.rmtree(smoke_dir, ignore_errors=True)


def build_demo_database(temp_db_path: Path) -> None:
    if temp_db_path.exists():
        temp_db_path.unlink()

    upgrade_database(temp_db_path)

    engine = create_engine(f"sqlite:///{temp_db_path}", future=True)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()

    try:
        seed_settings(session)
        seed_formula_constants(session)
        seed_colors(session)
        seed_templates(session)
        seed_projects(session)
    finally:
        session.close()
        engine.dispose()

    validate_seeded_db(temp_db_path)


def replace_live_database(temp_db_path: Path) -> Path | None:
    backup_path = None
    if DB_PATH.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = DB_PATH.with_name(f"cabplanner.db.backup-{timestamp}")
        shutil.copy2(DB_PATH, backup_path)
        DB_PATH.unlink()

    temp_db_path.replace(DB_PATH)
    return backup_path


def main() -> None:
    temp_db_path = ROOT / "cabplanner.demo-seed.tmp.db"
    if temp_db_path.exists():
        temp_db_path.unlink()

    build_demo_database(temp_db_path)
    backup_path = replace_live_database(temp_db_path)

    print(f"Demo database ready: {DB_PATH}")
    if backup_path:
        print(f"Previous database backup: {backup_path}")


if __name__ == "__main__":
    main()
