#!/bin/bash

echo "Checking for encoding issues (BOM / mojibake)..."

if command -v uv >/dev/null 2>&1; then
  PYTHON_CMD=(uv run python)
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=(python3)
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=(python)
elif command -v py >/dev/null 2>&1; then
  PYTHON_CMD=(py -3)
else
  echo "ERROR: Python interpreter not found (uv/python3/python/py)."
  exit 1
fi

"${PYTHON_CMD[@]}" - <<'PY'
from pathlib import Path
import re
import sys

# Runtime source and packaged source.
TARGETS = [Path('src'), Path('dist')]
EXCLUDED_SUFFIXES = ("/gui/constants/colors.py",)
TEXT_EXTS = {
    '.py', '.qss', '.txt', '.md', '.json', '.yaml', '.yml', '.ini', '.cfg'
}

# Typical mojibake chars after wrong re-encoding.
MOJIBAKE_RE = re.compile(r"[\uFFFD\u00C3\u00C5\u00C4\u0139\u0102\u00E2]")

failed = False
fixed_files = 0


def suspect_score(text: str) -> int:
    return len(MOJIBAKE_RE.findall(text))


def is_excluded(path: Path) -> bool:
    normalized = path.as_posix()
    return any(normalized.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def fix_mojibake_line(line: str) -> str:
    """
    Try to repair mojibake produced by cp1250<->utf-8 confusion.
    Applies up to 3 iterations while improving suspect score.
    """
    current = line
    for _ in range(3):
        if not MOJIBAKE_RE.search(current):
            break
        try:
            candidate = current.encode("cp1250").decode("utf-8")
        except UnicodeError:
            break
        if candidate == current:
            break
        if suspect_score(candidate) > suspect_score(current):
            break
        current = candidate
    return current

for target in TARGETS:
    if not target.exists():
        continue

    for path in target.rglob('*'):
        if not path.is_file():
            continue
        if is_excluded(path):
            continue

        # Restrict to source-like text files.
        if path.suffix.lower() not in TEXT_EXTS:
            continue

        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError as exc:
            print(f"ERROR: Non-UTF-8 file: {path} ({exc})")
            failed = True
            continue

        original = text
        changed = False

        if text.startswith('\ufeff'):
            text = text.lstrip('\ufeff')
            changed = True
            print(f"FIXED: Removed UTF-8 BOM in {path}")

        lines = text.splitlines(keepends=True)
        fixed_lines = []
        for lineno, line in enumerate(lines, 1):
            core = line.rstrip('\r\n')
            newline = line[len(core):]
            fixed_core = fix_mojibake_line(core)
            if fixed_core != core:
                changed = True
                print(
                    f"FIXED: Mojibake in {path}:{lineno}\n"
                    f"  before: {core}\n"
                    f"  after : {fixed_core}"
                )
            fixed_lines.append(fixed_core + newline)

        text = ''.join(fixed_lines)
        if changed and text != original:
            with path.open('w', encoding='utf-8', newline='') as f:
                f.write(text)
            fixed_files += 1
            print(f"FIXED: Rewrote {path}")

        # Final verification pass (after auto-fix).
        for lineno, line in enumerate(text.splitlines(), 1):
            if MOJIBAKE_RE.search(line):
                print(f"ERROR: Possible mojibake in {path}:{lineno}: {line}")
                failed = True

if fixed_files:
    print(f"Auto-fixed encoding in {fixed_files} file(s).")

if failed:
    print("Fix encoding issues and rerun checks.")
    sys.exit(1)
PY
