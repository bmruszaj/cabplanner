# scripts/build.ps1

# Figure out where this script lives
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Move into the project root (one level up from scripts/)
Push-Location $scriptDir
Push-Location ..

Write-Host "Building Cabplanner with PyInstaller…"

$backupRuntimeHook = $null

# Build arguments
$piArgs = @(
  '--clean'
  '--noconfirm'
  '--onedir'
  '--windowed'

  # App assets
  '--icon'; 'icon.ico'
  '--add-data'; 'icon.ico;.'
  '--add-data'; 'alembic.ini;.'
  '--add-data'; 'scripts;scripts'
  '--add-data'; '.version;.'
  '--add-data'; 'src;src'

  # Include entire packages
  '--hidden-import'; 'PySide6'
  '--hidden-import'; 'PySide6.QtCore'
  '--hidden-import'; 'PySide6.QtGui'
  '--hidden-import'; 'PySide6.QtWidgets'
  '--hidden-import'; 'shiboken6'


  # Hidden imports
  '--hidden-import'; 'docx'
  '--collect-data'; 'docx'
  '--hidden-import'; 'logging.config'
  '--hidden-import'; 'requests'

  # Submodules
  '--collect-submodules'; 'alembic'

  # Version info
  '--version-file'; 'cabplanner_version_info.txt'

  # Output
  '--name'; 'cabplanner'
  'src/main_app.py'
)

if ($env:CABPLANNER_BACKUP_TOKEN) {
    $backupRuntimeHook = Join-Path $env:TEMP 'cabplanner_backup_runtime_hook.py'
    $backupTokenLiteral = $env:CABPLANNER_BACKUP_TOKEN | ConvertTo-Json -Compress
    @"
import os

os.environ.setdefault("CABPLANNER_BACKUP_TOKEN", $backupTokenLiteral)
"@ | Set-Content -Path $backupRuntimeHook -Encoding UTF8

    $piArgs += @('--runtime-hook', $backupRuntimeHook)
    Write-Host "Embedding backup token runtime hook into build."
}
else {
    Write-Host "CABPLANNER_BACKUP_TOKEN not set. Build will not embed backup uploads."
}

try {
    # Run PyInstaller
    & pyinstaller @piArgs
}
finally {
    if ($backupRuntimeHook -and (Test-Path $backupRuntimeHook)) {
        Remove-Item $backupRuntimeHook -Force -ErrorAction SilentlyContinue
    }
}

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
