"""
Update script generator for Cabplanner.
This module provides the update script content as a Python string to avoid
PyInstaller permission issues when reading .ps1 files from temporary directories.
"""


def get_update_script() -> str:
    """
    Get the PowerShell update script content as a string.
    This script handles the folder-based update process after the main application exits.

    Returns:
        str: The complete PowerShell script content for Windows updates
    """
    return r"""param(
  [string]$InstallDir,
  [string]$NewDir
)

$ErrorActionPreference = "Continue"
$LogFile = "$env:TEMP\cab_update.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "[$timestamp] $Message"
}

$exe = Join-Path $InstallDir 'cabplanner.exe'
$db  = Join-Path $InstallDir 'cabplanner.db'
$lnk = Join-Path $InstallDir 'Cabplanner.lnk'
$successMarker = Join-Path $InstallDir '.update_success'

Write-Log "[UPDATER] starting in-place update process"
Write-Log "[UPDATER] install dir: $InstallDir"
Write-Log "[UPDATER] new package dir: $NewDir"

Write-Log "[UPDATER] waiting for cabplanner.exe to exit"
for ($i=0; $i -lt 15; $i++) {
  $p = Get-Process -Name 'cabplanner' -ErrorAction SilentlyContinue
  if (-not $p) { 
    Write-Log "[UPDATER] process has exited"
    break 
  }
  Write-Log "[UPDATER] waiting... attempt $($i+1)/15"
  Start-Sleep -Seconds 1
}

# 1) Ensure we will NOT bring a db from the new package
$pkgDb = Join-Path $NewDir 'cabplanner.db'
if (Test-Path $pkgDb) {
  Write-Log "[UPDATER] removing package DB to preserve user data"
  Remove-Item $pkgDb -Force -ErrorAction SilentlyContinue
}

# 2) Back up current critical pieces (do not touch cabplanner.db)
$exeBak = Join-Path $InstallDir 'cabplanner.exe.bak'
$intDir = Join-Path $InstallDir '_internal'
$intBak = Join-Path $InstallDir '_internal.bak'

if (Test-Path $exe) { 
  Write-Log "[UPDATER] backing up executable"
  Rename-Item $exe $exeBak -Force -EA SilentlyContinue 
}
if (Test-Path $intDir) { 
  Write-Log "[UPDATER] backing up _internal directory"
  Rename-Item $intDir $intBak -Force -EA SilentlyContinue 
}

# 3) Install new files
$newExe = Join-Path $NewDir 'cabplanner.exe'
$newInt = Join-Path $NewDir '_internal'
$newLnk = Join-Path $NewDir 'Cabplanner.lnk'

if (-not (Test-Path $newExe)) { 
  Write-Log "[UPDATER] ERROR: cabplanner.exe missing in package"
  exit 1 
}

Write-Log "[UPDATER] installing new executable"
Copy-Item $newExe $exe -Force

if (Test-Path $intBak) { 
  Write-Log "[UPDATER] removing old _internal backup"
  Remove-Item $intBak -Recurse -Force -EA SilentlyContinue 
}
Write-Log "[UPDATER] installing new _internal directory"
Copy-Item $newInt $InstallDir -Recurse -Force

# Always recreate shortcut with proper icon
if (Test-Path $lnk) { 
  Write-Log "[UPDATER] removing old shortcut"
  Remove-Item $lnk -Force -EA SilentlyContinue 
}

Write-Log "[UPDATER] creating new shortcut with icon"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($lnk)
$Shortcut.TargetPath = $exe
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.IconLocation = "$exe,0"
$Shortcut.Description = "Cabplanner Application"
$Shortcut.Save()

# 4) Launch and quick health check
Write-Log "[UPDATER] launching updated application"
$p = Start-Process -FilePath $exe -WorkingDirectory $InstallDir -PassThru
Start-Sleep -Seconds 2

if ($p.HasExited) {
  Write-Log "[UPDATER] launch failed, rolling back"
  if (Test-Path $exeBak) { 
    Write-Log "[UPDATER] restoring executable backup"
    Move-Item $exeBak $exe -Force -EA SilentlyContinue 
  }
  if (Test-Path $intBak) {
    Write-Log "[UPDATER] restoring _internal backup"
    if (Test-Path $intDir) { Remove-Item $intDir -Recurse -Force -EA SilentlyContinue }
    Move-Item $intBak $intDir -Force -EA SilentlyContinue
  }
  exit 1
}

# 5) Success; cleanup and create success marker
Write-Log "[UPDATER] update successful, cleaning up"
if (Test-Path $exeBak) { 
  Write-Log "[UPDATER] removing executable backup"
  Remove-Item $exeBak -Force -EA SilentlyContinue 
}
# $intBak removed earlier already

Write-Log "[UPDATER] creating success marker file"
"" | Out-File -FilePath $successMarker -Encoding UTF8

Write-Log "[UPDATER] removing temporary package directory"
Remove-Item $NewDir -Recurse -Force -EA SilentlyContinue

Write-Log "[UPDATER] update process completed successfully"
exit 0
"""


if __name__ == "__main__":
    # For testing - write the script to a file
    script_content = get_update_script()
    with open("update_test.ps1", "w", encoding="utf-8") as f:
        f.write(script_content)
    print("Update script written to update_test.ps1")
