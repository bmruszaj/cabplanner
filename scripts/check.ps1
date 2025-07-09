$env:PYTHONPATH = "src"

Write-Host "Running Ruff lint check..."
ruff check src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Checking Ruff formatting..."
ruff format --check src tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running tests with pytest..."
python -m pytest
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "All checks passed."
