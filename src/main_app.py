import sys

from PySide6.QtCore import QCoreApplication, QObject, QTimer, Slot
from PySide6.QtWidgets import QMessageBox

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
from src.services.kill_switch_service import KillSwitchService
from src.version import VERSION


class _RuntimeKillSwitchHandler(QObject):
    """Handle runtime kill switch notifications on the Qt main thread."""

    def __init__(self, log, parent=None):
        super().__init__(parent)
        self._log = log
        self._handled = False

    @Slot(object)
    def on_remote_block_detected(self, decision) -> None:
        """Show a blocking message and quit after the user confirms it."""
        if self._handled:
            return
        self._handled = True

        self._log.error(
            "Runtime kill switch activated: source=%s reason=%s",
            getattr(decision, "source", "unknown"),
            getattr(decision, "reason", "unknown"),
        )
        QMessageBox.critical(
            None,
            decision.title,
            f"{decision.message}\n\nAplikacja zostanie teraz zamknieta.",
        )
        QCoreApplication.quit()


def _enforce_startup_kill_switch(log, kill_switch_service) -> None:
    """Block application startup when the cached kill switch disables this version."""
    decision = kill_switch_service.evaluate_current_version(
        VERSION, prefer_remote=False
    )
    if not decision.is_blocked:
        return

    log.warning(
        "Startup blocked by kill switch: version=%s source=%s reason=%s",
        VERSION,
        decision.source,
        decision.reason or "unknown",
    )

    QMessageBox.critical(None, decision.title, decision.message)
    raise SystemExit(decision.message)


def main():
    """Entry point when run as a script."""
    log = configure_logging(get_base_path() / "cabplanner.log")
    enforce_single_instance("CabplannerApp")

    app = create_qt_app()
    set_app_icon(app)

    base = get_base_path()
    kill_switch_service = KillSwitchService(base_path=base)
    _enforce_startup_kill_switch(log, kill_switch_service)

    db_path, is_first_run = ensure_db_and_migrate(base)
    session = create_session(db_path)
    seed_cabinet_templates_if_first_run(session, base)

    # Ensure session is closed on app quit
    app.aboutToQuit.connect(session.close)

    services = create_services(session, kill_switch_service=kill_switch_service)
    apply_theme(app, session)

    window = create_main_window(session)
    window.showMaximized()
    wire_startup_update_check(window, services["settings"], services["updater"])
    runtime_kill_switch_handler = _RuntimeKillSwitchHandler(log)
    kill_switch_service.remote_block_detected.connect(
        runtime_kill_switch_handler.on_remote_block_detected
    )
    QTimer.singleShot(
        0, lambda: kill_switch_service.refresh_current_version_async(VERSION)
    )

    try:
        log.info("Starting Cabplanner application")
        sys.exit(app.exec())
    except Exception:
        log.exception("Unhandled exception in main")
        raise


if __name__ == "__main__":
    main()
