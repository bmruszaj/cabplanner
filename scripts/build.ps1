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
  '--onedir'
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
    Write-Error "Build failed with exit code $LASTEXITCODE"
    # Return to original directory before exiting
    Pop-Location
    Pop-Location
    exit $LASTEXITCODE
}

Write-Host "PyInstaller build succeeded!"

# Create shortcut for cabplanner.exe
Write-Host "Creating shortcut..."

$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("dist\cabplanner\Cabplanner.lnk")
$Shortcut.TargetPath = (Resolve-Path "dist\cabplanner\cabplanner.exe").Path
$Shortcut.WorkingDirectory = (Resolve-Path "dist\cabplanner").Path
$Shortcut.IconLocation = (Resolve-Path "dist\cabplanner\cabplanner.exe").Path + ",0"
$Shortcut.Description = "Cabplanner Application"
$Shortcut.Save()

Write-Host "Build completed! See dist\cabplanner folder with:"
Write-Host "   - cabplanner.exe (main executable)"
Write-Host "   - _internal\ (supporting files)"
Write-Host "   - Cabplanner.lnk (shortcut)"

# Return to original directory
Pop-Location
Pop-Location
