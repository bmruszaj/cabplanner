$env:PYTHONPATH = "src"

Write-Host "Auto-fixing code formatting with Ruff..."
ruff format src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running Ruff lint check (with auto-fix)... "
ruff check --fix src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running tests with pytest..."
python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "All checks passed."
