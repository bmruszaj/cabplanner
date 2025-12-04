from __future__ import annotations

from typing import Optional, Iterable

from sqlalchemy.orm import Session

from src.services.template_service import TemplateService


KNOWN_PART_TOKENS = [
    "wieniec",
    "boki",
    "bok",
    "półka",
    "polka",
    "front",
    "hdf",
    "HDF",
]


def _split_name_and_part(tokens: list[str]) -> tuple[str, str, list[str]]:
    """
    Split tokens into (name, part_name, rest_tokens_starting_with_first_number).

    Heuristic:
    - Find index i where tokens[i] starts a known part token (case-insensitive match on prefix).
    - Name = tokens[0:i]
    - Part name = tokens[i:j] where j is index of first numeric token
    - Rest = tokens[j:]
    """
    lowered = [t.lower() for t in tokens]
    part_start = None
    for i, t in enumerate(lowered):
        if any(t.startswith(pfx.lower()) for pfx in KNOWN_PART_TOKENS):
            part_start = i
            break
    if part_start is None:
        # fallback: assume first two tokens make up name (e.g., "D15 cargo")
        part_start = min(2, len(tokens))
    j = part_start
    while j < len(tokens) and not tokens[j].isdigit():
        # stop at first pure digit token (height)
        # handle numbers with punctuation by stripping non-digits at ends
        tok = tokens[j]
        if tok.isdigit():
            break
        try:
            float(tok.replace(",", "."))
            break
        except Exception:
            j += 1

    name = " ".join(tokens[:part_start]).strip()
    part_name = " ".join(tokens[part_start:j]).strip()
    rest = tokens[j:]
    return name, part_name, rest


def _parse_numbers_and_meta(
    rest: list[str],
) -> tuple[Optional[float], Optional[float], int, Optional[str], Optional[str]]:
    """
    Parse rest tokens into (height_mm, width_mm, pieces, wrapping, comments)
    Expected order: height width pieces wrapping comments...
    Some fields may be missing; handle gracefully.
    """

    def _to_float(tok: str) -> Optional[float]:
        try:
            return float(tok.replace(",", "."))
        except Exception:
            return None

    height = _to_float(rest[0]) if len(rest) > 0 else None
    width = _to_float(rest[1]) if len(rest) > 1 else None
    pieces = 1
    if len(rest) > 2:
        try:
            pieces = int(rest[2])
        except Exception:
            pieces = 1
    wrapping = rest[3] if len(rest) > 3 else None
    comments = " ".join(rest[4:]).strip() if len(rest) > 4 else None
    if comments == "":
        comments = None
    return height, width, pieces, wrapping, comments


def import_presets_from_lines(
    session: Session, lines: Iterable[str], default_kitchen_type: str = "LOFT"
) -> None:
    """
    Import preset cabinet definitions from an iterable of lines.
    Recognizes group headers like 'SZAFKI DOLNE' or 'SZAFKI GÓRNE' and uses them as group_name.
    """
    svc = TemplateService(session)

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("SZAFKI "):
            # Group header line; keep only the group name portion
            # e.g., "SZAFKI DOLNE" or "SZAFKI GÓRNE"
            continue
        # Skip column headers lines if present
        if "Nazwa" in line and "partName" in line:
            continue

        tokens = line.split()
        if len(tokens) < 4:
            continue

        cabinet_name, part_name, rest = _split_name_and_part(tokens)
        if not cabinet_name or not part_name or not rest:
            continue

        height, width, pieces, wrapping, comments = _parse_numbers_and_meta(rest)

        # Normalize HDF
        is_hdf = part_name.strip().lower() == "hdf"

        # Get or create cabinet type by name
        # Simple approach: try exact name match; otherwise create new
        existing = None
        for ct in svc.list_templates():
            if ct.name == cabinet_name:
                existing = ct
                break
        if existing is None:
            existing = svc.create_template(
                kitchen_type=default_kitchen_type,
                name=cabinet_name,
            )

        # Use material based on is_hdf flag
        material = "HDF" if is_hdf else "PLYTA"

        svc.add_part(
            cabinet_type_id=existing.id,
            part_name=part_name,
            height_mm=height,
            width_mm=width,
            pieces=pieces,
            material=material,
            wrapping=wrapping,
            comments=comments,
        )


def import_presets_from_text(
    session: Session, text: str, default_kitchen_type: str = "LOFT"
) -> None:
    import_presets_from_lines(session, text.splitlines(), default_kitchen_type)
