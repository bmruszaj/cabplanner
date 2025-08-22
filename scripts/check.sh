#!/bin/bash

export PYTHONPATH="src"

echo "Auto-fixing code formatting with Ruff..."
ruff format src tests
if [ $? -ne 0 ]; then exit $?; fi

echo "Running Ruff lint check (with auto-fix)..."
ruff check --fix src tests
if [ $? -ne 0 ]; then exit $?; fi

echo "Running tests with pytest..."
python -m pytest
if [ $? -ne 0 ]; then exit $?; fi

echo "All checks passed."
