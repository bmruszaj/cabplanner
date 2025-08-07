# scripts/build.ps1

# Figure out where this script lives
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Move into the project root (one level up from scripts/)
Push-Location $scriptDir
Push-Location ..

Write-Host "🧰 Building Cabplanner with PyInstaller…"

# Build arguments
$piArgs = @(
  '--clean'
  '--onefile'
  '--windowed'
  '--icon'; 'icon.ico'
  '--add-data'; 'alembic.ini;.'
  '--add-data'; 'src/db_alembic/migrations;src/db_alembic/migrations'
  '--add-data'; '.version;.'
  '--add-data'; 'src/gui/resources;src/gui/resources'
  '--add-data'; 'src;src'
  '--hidden-import'; 'docx'
  '--hidden-import'; 'logging.config'
  '--collect-submodules'; 'alembic'
  '--name'; 'cabplanner'
  'src/gui/main_app.py'
)

# Run PyInstaller
& pyinstaller @piArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Build failed with exit code $LASTEXITCODE"
    # Return to original directory before exiting
    Pop-Location
    Pop-Location
    exit $LASTEXITCODE
}

Write-Host "✅ Build succeeded! See dist\cabplanner.exe"

# Return to original directory
Pop-Location
Pop-Location
