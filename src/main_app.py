import sys

from src.app.logging_config import configure_logging
from src.app.paths import get_base_path
from src.app.bootstrap import create_qt_app, create_services, create_main_window
from src.app.database import (
    ensure_db_and_migrate,
    create_session,
    seed_cabinet_templates_if_first_run,
)
from src.app.theme import apply_theme
from src.app.resources import set_app_icon
from src.app.updates import wire_startup_update_check
from src.app.instance_guard import enforce_single_instance


def main():
    """Entry point when run as a script."""
    log = configure_logging(get_base_path() / "cabplanner.log")
    enforce_single_instance("CabplannerApp")

    app = create_qt_app()
    set_app_icon(app)

    base = get_base_path()
    db_path, is_first_run = ensure_db_and_migrate(base)
    session = create_session(db_path)
    seed_cabinet_templates_if_first_run(session, base)

    # Ensure session is closed on app quit
    app.aboutToQuit.connect(session.close)

    services = create_services(session)  # returns {'settings': ..., 'updater': ...}
    apply_theme(app, session)

    window = create_main_window(session)
    window.show()
    wire_startup_update_check(window, services["settings"], services["updater"])

    try:
        log.info("Starting Cabplanner application")
        sys.exit(app.exec())
    except Exception:
        log.exception("Unhandled exception in main")
        raise


if __name__ == "__main__":
    main()
