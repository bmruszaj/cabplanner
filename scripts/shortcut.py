"""
Shortcut creation script generator for Cabplanner.
This module provides the shortcut creation script content for first-run scenarios.
"""


def get_shortcut_script() -> str:
    """
    Get the PowerShell shortcut creation script content as a string.
    This script creates a desktop shortcut for the application on first run.

    Returns:
        str: The complete PowerShell script content for shortcut creation
    """
    return r"""param(
  [string]$InstallDir
)

$ErrorActionPreference = "Continue"
$LogFile = "$env:TEMP\cabplanner_shortcut.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -FilePath $LogFile -Append -Encoding UTF8
    Write-Host "[$timestamp] $Message"
}

$exe = Join-Path $InstallDir 'cabplanner.exe'
$shortcutPath = Join-Path $InstallDir 'Cabplanner.lnk'

Write-Log "Creating desktop shortcut"
Write-Log "Install dir: $InstallDir"
Write-Log "Executable: $exe"
Write-Log "Shortcut path: $shortcutPath"

# Verify executable exists
if (-not (Test-Path $exe)) {
    Write-Log "ERROR: Executable not found: $exe"
    exit 1
}

# Only create if shortcut doesn't exist
if (Test-Path $shortcutPath) {
    Write-Log "Shortcut already exists: $shortcutPath"
    exit 0
}

try {
    # Create shortcut using WScript.Shell
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = $exe
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.IconLocation = "$exe,0"
    $Shortcut.Description = "Cabplanner Application"
    $Shortcut.Save()
    
    Write-Log "Shortcut created successfully: $shortcutPath"
    exit 0
    
} catch {
    Write-Log "ERROR: Failed to create shortcut: $($_.Exception.Message)"
    exit 1
}
"""


if __name__ == "__main__":
    # For testing - write the script to a file
    script_content = get_shortcut_script()
    with open("shortcut_test.ps1", "w", encoding="utf-8") as f:
        f.write(script_content)
    print("Shortcut script written to shortcut_test.ps1")
