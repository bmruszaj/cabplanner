"""Integration-style tests for startup kill switch wiring."""

from pathlib import Path

import pytest

from src.services.kill_switch_service import KillSwitchDecision
import src.main_app as main_app


class _FakeSignal:
    def connect(self, _callback):
        """Mimic Qt signal connect without storing callbacks."""


class _FakeApp:
    def __init__(self):
        self.aboutToQuit = _FakeSignal()

    def exec(self):
        return 0


class _FakeWindow:
    def showMaximized(self):
        """Mimic the main window display call."""


class _FakeSession:
    def close(self):
        """Mimic SQLAlchemy session close."""


class _FakeLog:
    def info(self, *_args, **_kwargs):
        """Ignore info logs in tests."""

    def error(self, *_args, **_kwargs):
        """Ignore error logs in tests."""

    def warning(self, *_args, **_kwargs):
        """Ignore warning logs in tests."""

    def exception(self, *_args, **_kwargs):
        """Ignore exception logs in tests."""


class _FakeTimer:
    calls = []

    @staticmethod
    def singleShot(delay, callback):
        _FakeTimer.calls.append((delay, callback))


def test_main_checks_cached_kill_switch_before_db_mutations(monkeypatch):
    calls = []
    fake_log = _FakeLog()
    _FakeTimer.calls = []

    class _FakeKillSwitchService:
        def __init__(self, base_path):
            calls.append(("kill_switch_init", base_path))
            self.remote_block_detected = _FakeSignal()

        def evaluate_current_version(self, version, prefer_remote=True):
            calls.append(("evaluate_current_version", version, prefer_remote))
            return KillSwitchDecision(is_blocked=False, source="none")

        def refresh_current_version_async(self, version):
            calls.append(("refresh_current_version_async", version))

    monkeypatch.setattr(
        main_app, "configure_logging", lambda *_args, **_kwargs: fake_log
    )
    monkeypatch.setattr(
        main_app,
        "enforce_single_instance",
        lambda *_args: calls.append("single_instance"),
    )
    monkeypatch.setattr(main_app, "create_qt_app", lambda: _FakeApp())
    monkeypatch.setattr(
        main_app, "set_app_icon", lambda *_args: calls.append("set_icon")
    )
    monkeypatch.setattr(main_app, "get_base_path", lambda: Path("BASE"))
    monkeypatch.setattr(main_app, "KillSwitchService", _FakeKillSwitchService)
    monkeypatch.setattr(main_app, "QTimer", _FakeTimer)
    monkeypatch.setattr(
        main_app,
        "ensure_db_and_migrate",
        lambda base: calls.append(("ensure_db_and_migrate", base))
        or ("db.sqlite", False),
    )
    monkeypatch.setattr(main_app, "create_session", lambda *_args: _FakeSession())
    monkeypatch.setattr(
        main_app,
        "seed_cabinet_templates_if_first_run",
        lambda *_args: calls.append("seed"),
    )
    monkeypatch.setattr(
        main_app,
        "create_services",
        lambda *_args, **_kwargs: {
            "settings": "SETTINGS",
            "updater": "UPDATER",
            "kill_switch": "KILL_SWITCH",
        },
    )
    monkeypatch.setattr(
        main_app, "apply_theme", lambda *_args: calls.append("apply_theme")
    )
    monkeypatch.setattr(main_app, "create_main_window", lambda *_args: _FakeWindow())
    monkeypatch.setattr(
        main_app,
        "wire_startup_update_check",
        lambda *_args: calls.append("wire_updates"),
    )
    monkeypatch.setattr(
        main_app.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
    )

    with pytest.raises(SystemExit) as exc_info:
        main_app.main()

    assert exc_info.value.code == 0
    assert calls.index(
        ("evaluate_current_version", main_app.VERSION, False)
    ) < calls.index(("ensure_db_and_migrate", Path("BASE")))
    assert _FakeTimer.calls
    assert _FakeTimer.calls[0][0] == 0


def test_main_aborts_before_db_when_cached_kill_switch_blocks(monkeypatch):
    fake_log = _FakeLog()
    shown_dialogs = []

    class _FakeKillSwitchService:
        def __init__(self, base_path):
            self.base_path = base_path
            self.remote_block_detected = _FakeSignal()

        def evaluate_current_version(self, version, prefer_remote=True):
            return KillSwitchDecision(
                is_blocked=True,
                title="Blocked",
                message="Stop now",
                source="cache",
                reason="block_all",
            )

        def refresh_current_version_async(self, version):
            raise AssertionError("refresh should not start after a blocking decision")

    class _FakeMessageBox:
        @staticmethod
        def critical(_parent, title, message):
            shown_dialogs.append((title, message))

    monkeypatch.setattr(
        main_app, "configure_logging", lambda *_args, **_kwargs: fake_log
    )
    monkeypatch.setattr(main_app, "enforce_single_instance", lambda *_args: None)
    monkeypatch.setattr(main_app, "create_qt_app", lambda: _FakeApp())
    monkeypatch.setattr(main_app, "set_app_icon", lambda *_args: None)
    monkeypatch.setattr(main_app, "get_base_path", lambda: Path("BASE"))
    monkeypatch.setattr(main_app, "KillSwitchService", _FakeKillSwitchService)
    monkeypatch.setattr(main_app, "QMessageBox", _FakeMessageBox)
    monkeypatch.setattr(
        main_app,
        "ensure_db_and_migrate",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("DB should not be touched")
        ),
    )

    with pytest.raises(SystemExit, match="Stop now"):
        main_app.main()

    assert shown_dialogs == [("Blocked", "Stop now")]


def test_runtime_handler_shows_modal_and_quits(monkeypatch):
    fake_log = _FakeLog()
    shown_dialogs = []
    quit_calls = []

    class _FakeMessageBox:
        @staticmethod
        def critical(_parent, title, message):
            shown_dialogs.append((title, message))

    class _FakeCoreApplication:
        @staticmethod
        def quit():
            quit_calls.append("quit")

    monkeypatch.setattr(main_app, "QMessageBox", _FakeMessageBox)
    monkeypatch.setattr(main_app, "QCoreApplication", _FakeCoreApplication)

    handler = main_app._RuntimeKillSwitchHandler(fake_log)
    handler.on_remote_block_detected(
        KillSwitchDecision(
            is_blocked=True,
            title="Blocked",
            message="Stop now",
            source="remote",
            reason="block_all",
        )
    )

    assert shown_dialogs == [
        ("Blocked", "Stop now\n\nAplikacja zostanie teraz zamknieta.")
    ]
    assert quit_calls == ["quit"]
