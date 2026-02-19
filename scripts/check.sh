#!/bin/bash

export PYTHONPATH="src"

if command -v uv >/dev/null 2>&1; then
  RUNNER=(uv run)
else
  RUNNER=()
fi

run_cmd() {
  if [ ${#RUNNER[@]} -gt 0 ]; then
    "${RUNNER[@]}" "$@"
  else
    "$@"
  fi
}

echo "Auto-fixing code formatting with Ruff..."
run_cmd ruff format src tests
if [ $? -ne 0 ]; then exit $?; fi

echo "Running Ruff lint check (with auto-fix)..."
run_cmd ruff check --fix src tests
if [ $? -ne 0 ]; then exit $?; fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$SCRIPT_DIR/check_encoding.sh"
if [ $? -ne 0 ]; then exit $?; fi

echo "Running tests with pytest..."
run_cmd python -m pytest
if [ $? -ne 0 ]; then exit $?; fi

echo "All checks passed."
