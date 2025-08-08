# scripts_runner.py
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

def run_powershell(
    script_content: str, args: Optional[List[str]] = None, hidden: bool = True
) -> subprocess.Popen:
    """
    Execute a PowerShell script with the given arguments.

    Args:
        script_content: The PowerShell script content as a string
        args: Optional list of arguments to pass to the script
        hidden: Whether to run the script with hidden window

    Returns:
        Popen object for the running process
    """
    logger.debug("Preparing to run PowerShell script")

    # Write script content to temporary file
    ps_path = (
        Path(tempfile.gettempdir()) / f"cabplanner_script_{id(script_content)}.ps1"
    )
    ps_path.write_text(script_content, encoding="utf-8")

    logger.debug("Created PowerShell script: %s", ps_path)

    # Build command line - Use full PowerShell path for reliability
    cmd = [
        "powershell.exe",
        "-ExecutionPolicy", "Bypass",
        "-NoProfile",  # Don't load user profile for faster startup
        "-File", str(ps_path)
    ]

    if hidden:
        cmd.extend(["-WindowStyle", "Hidden"])

    if args:
        cmd.extend(args)

    logger.info("Executing PowerShell command: %s", " ".join(cmd))

    # For debugging purposes, let's capture output initially to see what's failing
    # We'll only do this for a short period to diagnose the issue
    try:
        # First try: capture output to see what's wrong
        if hidden:
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
        else:
            creation_flags = 0
            stdout = None
            stderr = None

        process = subprocess.Popen(
            cmd,
            creationflags=creation_flags,
            stdout=stdout,
            stderr=stderr,
            stdin=None,
            text=True,
            cwd=None,
        )

        logger.info("Started PowerShell process with PID: %s", process.pid)

        # If we're capturing output (for debugging), check for immediate errors
        if hidden and stdout == subprocess.PIPE:
            import time
            time.sleep(0.5)  # Give it a moment

            poll_result = process.poll()
            if poll_result is not None:
                # Process exited, capture output
                try:
                    stdout_data, stderr_data = process.communicate(timeout=1)
                    logger.error("PowerShell script failed with exit code: %s", poll_result)
                    if stdout_data:
                        logger.error("PowerShell stdout: %s", stdout_data.strip())
                    if stderr_data:
                        logger.error("PowerShell stderr: %s", stderr_data.strip())
                except subprocess.TimeoutExpired:
                    logger.error("PowerShell process hung")

                # Clean up the script file since it failed
                if ps_path.exists():
                    try:
                        ps_path.unlink()
                    except Exception:
                        pass

                raise subprocess.CalledProcessError(poll_result, cmd)
            else:
                # Process is still running, detach it properly
                logger.info("PowerShell process is running successfully, detaching...")
                # Don't clean up the script file yet - let it run

        return process

    except Exception as e:
        logger.error("Failed to start PowerShell process: %s", e)
        # Clean up the temporary script file if process failed to start
        if ps_path.exists():
            try:
                ps_path.unlink()
            except Exception as cleanup_error:
                logger.warning("Failed to cleanup script file: %s", cleanup_error)
        raise
