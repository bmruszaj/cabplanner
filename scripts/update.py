"""
Update script generator for Cabplanner.
This module provides the update script content as a Python string to avoid
PyInstaller permission issues when reading .ps1 files from temporary directories.
"""


def get_update_script() -> str:
    """
    Get the PowerShell update script content as a string.
    This script handles the onedir-based update process after the main application exits.
    Backs up cabplanner.exe and _internal/, installs new versions, preserves cabplanner.db.

    Returns:
        str: The complete PowerShell script content for Windows updates
    """
    return r"""param(
  [string]$InstallDir,
  [string]$NewDir
)

$ErrorActionPreference = "Continue"
$LogFile = "$env:TEMP\cabplanner_update.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "[$timestamp] $Message"
}

function Backup-Item {
    param([string]$Path, [string]$BackupSuffix = ".bak")
    if (Test-Path $Path) {
        $backupPath = "$Path$BackupSuffix"
        if (Test-Path $backupPath) {
            Remove-Item $backupPath -Recurse -Force -ErrorAction SilentlyContinue
        }
        Move-Item $Path $backupPath -Force
        Write-Log "Backed up $Path to $backupPath"
        return $backupPath
    }
    return $null
}

function Restore-Backup {
    param([string]$BackupPath, [string]$OriginalPath)
    if (Test-Path $BackupPath) {
        if (Test-Path $OriginalPath) {
            Remove-Item $OriginalPath -Recurse -Force -ErrorAction SilentlyContinue
        }
        Move-Item $BackupPath $OriginalPath -Force
        Write-Log "Restored $OriginalPath from backup"
    }
}

$exe = Join-Path $InstallDir 'cabplanner.exe'
$internal = Join-Path $InstallDir '_internal'
$db = Join-Path $InstallDir 'cabplanner.db'
$successMarker = Join-Path $InstallDir '.update_success'

$newExe = Join-Path $NewDir 'cabplanner.exe'
$newInternal = Join-Path $NewDir '_internal'

Write-Log "Starting onedir update process"
Write-Log "Install dir: $InstallDir"
Write-Log "New package dir: $NewDir"

# Wait for application to exit
Write-Log "Waiting for cabplanner.exe to exit"
for ($i = 0; $i -lt 15; $i++) {
    $process = Get-Process -Name 'cabplanner' -ErrorAction SilentlyContinue
    if (-not $process) { 
        Write-Log "Process has exited"
        break 
    }
    Write-Log "Waiting... attempt $($i+1)/15"
    Start-Sleep -Seconds 1
}

# Verify new package structure
if (-not (Test-Path $newExe)) {
    Write-Log "ERROR: New executable not found: $newExe"
    exit 1
}

if (-not (Test-Path $newInternal)) {
    Write-Log "ERROR: New _internal directory not found: $newInternal"
    exit 1
}

# Remove any packaged database to preserve user data
$newDb = Join-Path $NewDir 'cabplanner.db'
if (Test-Path $newDb) {
    Write-Log "Removing packaged database to preserve user data"
    Remove-Item $newDb -Force -ErrorAction SilentlyContinue
}

# Backup current installation
$exeBackup = Backup-Item $exe
$internalBackup = Backup-Item $internal

try {
    # Install new executable
    Write-Log "Installing new executable"
    Copy-Item $newExe $exe -Force
    
    # Install new _internal directory
    Write-Log "Installing new _internal directory"
    Copy-Item $newInternal $internal -Recurse -Force
    
    # Create/update shortcut
    $shortcutPath = Join-Path $InstallDir 'Cabplanner.lnk'
    if (-not (Test-Path $shortcutPath) -or -not (Test-Path $db)) {
        Write-Log "Creating/updating desktop shortcut"
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $exe
        $Shortcut.WorkingDirectory = $InstallDir
        $Shortcut.IconLocation = "$exe,0"
        $Shortcut.Description = "Cabplanner Application"
        $Shortcut.Save()
        Write-Log "Shortcut created/updated: $shortcutPath"
    }
    
    # Mark update as successful
    "Update completed successfully at $(Get-Date)" | Out-File -FilePath $successMarker -Encoding UTF8
    Write-Log "Update completed successfully"
    
    # Clean up backups on success
    if ($exeBackup -and (Test-Path $exeBackup)) {
        Remove-Item $exeBackup -Force -ErrorAction SilentlyContinue
        Write-Log "Removed executable backup"
    }
    if ($internalBackup -and (Test-Path $internalBackup)) {
        Remove-Item $internalBackup -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Removed _internal backup"
    }
    
    # Restart the application
    Write-Log "Restarting application: $exe"
    try {
        Start-Process -FilePath $exe -WorkingDirectory $InstallDir -ErrorAction Stop
        Write-Log "Application restarted successfully"
    } catch {
        Write-Log "ERROR: Failed to restart application: $($_.Exception.Message)"
        # Don't exit with error - the update was successful, just restart failed
    }
    
} catch {
    Write-Log "ERROR: Update failed: $($_.Exception.Message)"
    
    # Restore from backups
    if ($exeBackup) {
        Restore-Backup $exeBackup $exe
    }
    if ($internalBackup) {
        Restore-Backup $internalBackup $internal
    }
    
    Write-Log "Rollback completed"
    exit 1
}

# Clean up temporary directory
try {
    Remove-Item $NewDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Log "Cleaned up temporary directory: $NewDir"
} catch {
    Write-Log "Warning: Could not clean up temporary directory: $($_.Exception.Message)"
}

Write-Log "Update process completed successfully"
exit 0
"""


if __name__ == "__main__":
    # For testing - write the script to a file
    script_content = get_update_script()
    with open("update_test.ps1", "w", encoding="utf-8") as f:
        f.write(script_content)
    print("Update script written to update_test.ps1")
