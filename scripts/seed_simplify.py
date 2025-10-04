import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = ROOT_DIR / "src" / "db_schema"
SEED_PATH = SEED_DIR / "seed_cabinets_option_b.sql"
OUTPUT_PATH = SEED_DIR / "seed_cabinets_option_b.simple.sql"


def parse_seed_parts_raw_inserts(sql_text: str):
    pattern = re.compile(
        r"INSERT INTO\s+seed_parts_raw\s*\(nazwa,\s*part_name,\s*height_mm,\s*width_mm,\s*pieces,\s*wrapping,\s*comments\)\s*VALUES\s*\((.*?)\);",
        re.IGNORECASE | re.DOTALL,
    )
    rows = []
    for m in pattern.finditer(sql_text):
        values_str = m.group(1)
        # split top-level commas respecting quotes
        parts = []
        buf = []
        in_quote = False
        i = 0
        while i < len(values_str):
            ch = values_str[i]
            if ch == "'":
                in_quote = not in_quote
                buf.append(ch)
            elif ch == "," and not in_quote:
                parts.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
            i += 1
        if buf:
            parts.append("".join(buf).strip())
        if len(parts) != 7:
            continue
        nazwa, part_name, h, w, pcs, wrap, comm = parts
        rows.append({
            "nazwa": nazwa,
            "part_name": part_name,
            "height_mm": h,
            "width_mm": w,
            "pieces": pcs,
            "wrapping": wrap,
            "comments": comm,
        })
    return rows


def main():
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    sql_text = SEED_PATH.read_text(encoding="utf-8")
    rows = parse_seed_parts_raw_inserts(sql_text)

    # Build unique type inserts (INSERT OR IGNORE)
    seen = set()
    type_inserts = []
    for r in rows:
        nazwa = r["nazwa"]
        if nazwa not in seen:
            seen.add(nazwa)
            type_inserts.append(
                f"INSERT OR IGNORE INTO cabinet_types (kitchen_type, nazwa, created_at, updated_at) VALUES ('LOFT', {nazwa}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);"
            )

    # Build part inserts using subselect for type id
    part_inserts = []
    for r in rows:
        part_inserts.append(
            "INSERT INTO cabinet_parts (cabinet_type_id, part_name, height_mm, width_mm, pieces, wrapping, comments, material, thickness_mm, processing_json, created_at, updated_at) VALUES "
            f"((SELECT id FROM cabinet_types WHERE nazwa = {r['nazwa']}), {r['part_name']}, {r['height_mm']}, {r['width_mm']}, {r['pieces']}, {r['wrapping']}, {r['comments']}, NULL, NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);"
        )

    OUTPUT_PATH.write_text("\n".join(type_inserts + part_inserts) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {len(type_inserts)} type inserts and {len(part_inserts)} part inserts")


if __name__ == "__main__":
    main()


