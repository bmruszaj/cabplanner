# scripts/build.ps1

# Figure out where this script lives
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Move into the project root (one level up from scripts/)
Push-Location $scriptDir
Push-Location ..

Write-Host "Building Cabplanner with PyInstaller…"

# Build arguments
$piArgs = @(
  '--clean'
  '--noconfirm'
  '--onedir'
  '--windowed'
  '--icon'; 'icon.ico'
  '--add-data'; 'icon.ico;.'
  '--add-data'; 'alembic.ini;.'
  '--add-data'; 'scripts;scripts'
  '--add-data'; '.version;.'
  '--add-data'; 'src;src'
  '--hidden-import'; 'docx'
  '--hidden-import'; 'logging.config'
  '--hidden-import'; 'requests'
  '--collect-submodules'; 'alembic'
  '--name'; 'cabplanner'
  'src/main_app.py'
)

# Run PyInstaller
& pyinstaller @piArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed with exit code $LASTEXITCODE"
    # Return to original directory before exiting
    Pop-Location
    Pop-Location
    exit $LASTEXITCODE
}

Write-Host "PyInstaller build succeeded!"

Write-Host "Build completed! See dist\cabplanner folder with:"
Write-Host "   - cabplanner.exe (main executable)"
Write-Host "   - _internal\ (supporting files)"

# Return to original directory
Pop-Location
Pop-Location
