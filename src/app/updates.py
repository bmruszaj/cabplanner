import sys
import logging
from pathlib import Path
from datetime import datetime, timezone
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox
from src.gui.update_dialog import UpdateDialog
from src.services.settings_service import SettingsService
from src.services.updater_service import UpdaterService
from src.app.update.errors import UpdateError
from src.version import VERSION

logger = logging.getLogger(__name__)


def configure_update_dialog(
    dialog: UpdateDialog, updater_service: UpdaterService, close_on_cancel: bool = True
) -> None:
    """Connect update dialog signals to the updater service."""
    dialog.check_for_updates.connect(updater_service.check_for_updates)
    dialog.perform_update.connect(
        lambda: _start_update_process(dialog, updater_service)
    )
    updater_service.update_progress.connect(dialog.on_update_progress)
    updater_service.update_complete.connect(dialog.on_update_complete)
    updater_service.update_failed.connect(dialog.on_update_failed)
    updater_service.update_check_failed.connect(dialog.update_check_failed)
    updater_service.request_quit.connect(dialog.accept)
    dialog.cancel_update.connect(updater_service.cancel_update)
    if close_on_cancel:
        dialog.cancel_update.connect(dialog.reject)


def run_forced_update_dialog(
    parent,
    updater_service: UpdaterService,
    title: str,
    message: str,
    current_version: str = VERSION,
) -> None:
    """Show a modal dialog that lets a blocked user install the latest version."""
    dialog = UpdateDialog(current_version, parent=parent)
    configure_update_dialog(dialog, updater_service)
    dialog.force_update_required(title, message)
    dialog.exec()


def wire_startup_update_check(
    window, settings_service: SettingsService, updater_service: UpdaterService
) -> None:
    """Wire up the startup update check with proper signal connections and timing."""
    # Check for updates on startup after a short delay
    QTimer.singleShot(
        2000, lambda: _check_startup_updates(window, settings_service, updater_service)
    )


def _check_startup_updates(
    window, settings_service: SettingsService, updater_service: UpdaterService
):
    """Check for updates on startup based on user settings."""
    try:
        # Check if app was just updated and show success message
        _check_and_show_update_success(window)

        # Create shortcut on every startup (if enabled in settings)
        create_shortcut_enabled = settings_service.get_setting_value(
            "create_shortcut_on_start", True
        )
        if create_shortcut_enabled:
            updater_service.create_shortcut_on_first_run()

        # Update last check timestamp
        now = datetime.now(timezone.utc)
        settings_service.set_setting("last_update_check", now.isoformat())

        # Check if we should check for updates
        if not updater_service.should_check_for_updates(settings_service):
            logger.info("Skipping startup update check based on user settings")
            return

        logger.info("Performing startup update check...")

        # Connect signals for handling update results
        updater_service.update_check_complete.connect(
            lambda update_available,
            current_version,
            latest_version: _handle_startup_update_result(
                window,
                updater_service,
                update_available,
                current_version,
                latest_version,
            )
        )

        # Perform the check
        updater_service.check_for_updates()

    except Exception as e:
        logger.exception(f"Error during startup update check: {e}")


def _check_and_show_update_success(window):
    """Check if app was just updated and show success notification."""
    try:
        # Check for update success marker file
        if getattr(sys, "frozen", False):
            current_exe_path = Path(sys.executable)
            install_dir = current_exe_path.parent
            success_marker = install_dir / ".update_success"

            if success_marker.exists():
                # Show success message
                QTimer.singleShot(1500, lambda: _show_update_success_message(window))

                # Remove the marker file
                try:
                    success_marker.unlink()
                    logger.info("Removed update success marker")
                except Exception as e:
                    logger.warning(f"Could not remove update success marker: {e}")

    except Exception as e:
        logger.exception(f"Error checking update success: {e}")


def _show_update_success_message(window):
    """Show update success message to user."""
    try:
        QMessageBox.information(
            window,
            "Aktualizacja zakończona",
            "Aplikacja została pomyślnie zaktualizowana do najnowszej wersji!\n\n"
            "Wszystkie Twoje dane zostały zachowane.",
        )
    except Exception as e:
        logger.exception(f"Error showing update success message: {e}")


def _handle_startup_update_result(
    window,
    updater_service: UpdaterService,
    update_available,
    current_version,
    latest_version,
):
    """Handle the result of startup update check."""
    try:
        if update_available:
            logger.info(f"Update available: {current_version} -> {latest_version}")

            # Show update dialog
            dialog = UpdateDialog(VERSION, parent=window)
            configure_update_dialog(dialog, updater_service)

            # Show that update is available
            dialog.update_available(current_version, latest_version)
            dialog.show()

        else:
            logger.info("No updates available at startup")

    except Exception as e:
        logger.exception(f"Error handling startup update result: {e}")


def _start_update_process(dialog, updater_service: UpdaterService):
    """Start the update process with proper dialog state management."""
    try:
        logger.info("Starting update process from dialog")

        # Update dialog state to show update is starting
        dialog.on_update_started()

        # Start the actual update process
        updater_service.perform_update()

    except Exception as e:
        logger.exception(f"Error starting update process: {e}")
        # Convert to UpdateError if it's not already an update-related exception
        if isinstance(e, UpdateError):
            dialog.on_update_failed(e)
        else:
            dialog.on_update_failed(UpdateError(f"Unexpected error: {e}"))
