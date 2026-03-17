import sys

from PySide6.QtCore import QCoreApplication, QObject, Slot

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
from src.app.updates import run_forced_update_dialog, wire_startup_update_check
from src.app.instance_guard import enforce_single_instance
from src.services.kill_switch_service import KillSwitchService
from src.services.updater_service import UpdaterService
from src.version import VERSION


class _RuntimeKillSwitchHandler(QObject):
    """Handle runtime kill switch notifications on the Qt main thread."""

    def __init__(self, log, updater_service, dialog_parent=None, parent=None):
        super().__init__(parent)
        self._log = log
        self._handled = False
        self._updater_service = updater_service
        self._dialog_parent = dialog_parent

    @Slot(object)
    def on_remote_block_detected(self, decision) -> None:
        """Offer an update and quit once the forced-update dialog closes."""
        if self._handled:
            return
        self._handled = True

        self._log.error(
            "Runtime kill switch activated: source=%s reason=%s",
            getattr(decision, "source", "unknown"),
            getattr(decision, "reason", "unknown"),
        )
        run_forced_update_dialog(
            self._dialog_parent,
            self._updater_service,
            decision.title,
            decision.message,
        )
        QCoreApplication.quit()


def _enforce_startup_kill_switch(
    log, kill_switch_service, updater_service: UpdaterService
) -> None:
    """Block startup when cache and remote policy agree the version is disabled."""
    cached_decision = kill_switch_service.evaluate_current_version(
        VERSION, prefer_remote=False
    )
    if not cached_decision.is_blocked:
        return

    log.warning(
        "Startup cache blocks version=%s; rechecking remote kill switch",
        VERSION,
    )

    decision = kill_switch_service.evaluate_current_version(
        VERSION,
        prefer_remote=True,
        use_service_timeout=False,
    )
    if not decision.is_blocked:
        log.info("Remote kill switch recheck cleared cached startup block")
        return

    log.warning(
        "Startup blocked by kill switch: version=%s source=%s reason=%s",
        VERSION,
        decision.source,
        decision.reason or "unknown",
    )

    run_forced_update_dialog(None, updater_service, decision.title, decision.message)
    raise SystemExit(decision.message)


def main():
    """Entry point when run as a script."""
    log = configure_logging(get_base_path() / "cabplanner.log")
    enforce_single_instance("CabplannerApp")

    app = create_qt_app()
    set_app_icon(app)

    base = get_base_path()
    updater_service = UpdaterService()
    kill_switch_service = KillSwitchService(base_path=base)
    _enforce_startup_kill_switch(log, kill_switch_service, updater_service)

    db_path, is_first_run = ensure_db_and_migrate(base)
    session = create_session(db_path)
    seed_cabinet_templates_if_first_run(session, base)

    # Ensure session is closed on app quit
    app.aboutToQuit.connect(session.close)

    services = create_services(
        session,
        db_path=db_path,
        base_path=base,
        kill_switch_service=kill_switch_service,
        updater_service=updater_service,
    )
    apply_theme(app, session)

    window = create_main_window(session)
    window.showMaximized()
    wire_startup_update_check(window, services["settings"], services["updater"])
    services["backup"].start()
    app.aboutToQuit.connect(services["backup"].stop)
    runtime_kill_switch_handler = _RuntimeKillSwitchHandler(
        log,
        services["updater"],
        dialog_parent=window,
    )
    kill_switch_service.remote_block_detected.connect(
        runtime_kill_switch_handler.on_remote_block_detected
    )
    kill_switch_service.refresh_current_version_async(VERSION)

    try:
        log.info("Starting Cabplanner application")
        sys.exit(app.exec())
    except Exception:
        log.exception("Unhandled exception in main")
        raise


if __name__ == "__main__":
    main()
