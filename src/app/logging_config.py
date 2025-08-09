import os
import sys
import logging
from pathlib import Path


def configure_logging(log_path: Path) -> logging.Logger:
    """Configure root logger with console and file handlers."""
    # Detect auto-restart loop
    if os.environ.get("CABPLANNER_RESTARTING") == "1":
        logger = logging.getLogger(__name__)
        logger.critical(
            "Detected potential restart loop! Application was restarted recently."
        )
        if "--force-restart" not in sys.argv:
            logger.critical("Exiting to prevent infinite restart loop.")
            sys.exit(1)

    # Set environment variable to detect restart loops
    os.environ["CABPLANNER_RESTARTING"] = "1"

    # Create a file to track this instance
    instance_marker = Path(Path.home() / ".cabplanner_instance")
    try:
        with open(instance_marker, "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        # Create a basic logger just for this warning
        temp_logger = logging.getLogger(__name__)
        temp_logger.warning(f"Could not write instance marker: {e}")

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, mode="a"),
        ],
    )
    
    logger = logging.getLogger(__name__)
    logger.debug("Application starting with PID: %s", os.getpid())
    logger.debug("Command line arguments: %s", sys.argv)
    
    return logger
