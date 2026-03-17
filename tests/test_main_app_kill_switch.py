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


class _FakeBackupService:
    def __init__(self, calls):
        self._calls = calls

    def start(self):
        self._calls.append("backup_start")

    def stop(self):
        self._calls.append("backup_stop")


class _FakeLog:
    def info(self, *_args, **_kwargs):
        """Ignore info logs in tests."""

    def error(self, *_args, **_kwargs):
        """Ignore error logs in tests."""

    def warning(self, *_args, **_kwargs):
        """Ignore warning logs in tests."""

    def exception(self, *_args, **_kwargs):
        """Ignore exception logs in tests."""


def test_main_checks_cached_kill_switch_before_db_mutations(monkeypatch):
    calls = []
    fake_log = _FakeLog()
    fake_updater = object()

    class _FakeKillSwitchService:
        def __init__(self, base_path):
            calls.append(("kill_switch_init", base_path))
            self.remote_block_detected = _FakeSignal()

        def evaluate_current_version(
            self,
            version,
            prefer_remote=True,
            use_service_timeout=True,
        ):
            calls.append(
                (
                    "evaluate_current_version",
                    version,
                    prefer_remote,
                    use_service_timeout,
                )
            )
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
    monkeypatch.setattr(main_app, "UpdaterService", lambda: fake_updater)
    monkeypatch.setattr(main_app, "KillSwitchService", _FakeKillSwitchService)
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
        lambda *_args, **kwargs: calls.append(
            ("create_services_updater", kwargs["updater_service"])
        )
        or {
            "backup": _FakeBackupService(calls),
            "settings": "SETTINGS",
            "updater": kwargs["updater_service"],
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
        ("evaluate_current_version", main_app.VERSION, False, True)
    ) < calls.index(("ensure_db_and_migrate", Path("BASE")))
    assert ("create_services_updater", fake_updater) in calls
    assert "backup_start" in calls
    assert ("refresh_current_version_async", main_app.VERSION) in calls


def test_main_aborts_before_db_when_cached_kill_switch_blocks(monkeypatch):
    fake_log = _FakeLog()
    forced_update_calls = []
    fake_updater = object()

    class _FakeKillSwitchService:
        def __init__(self, base_path):
            self.base_path = base_path
            self.remote_block_detected = _FakeSignal()

        def evaluate_current_version(
            self,
            version,
            prefer_remote=True,
            use_service_timeout=True,
        ):
            if not prefer_remote:
                return KillSwitchDecision(
                    is_blocked=True,
                    title="Blocked",
                    message="Stop now",
                    source="cache",
                    reason="block_all",
                )
            return KillSwitchDecision(
                is_blocked=True,
                title="Blocked",
                message="Stop now",
                source="remote",
                reason="block_all",
            )

        def refresh_current_version_async(self, version):
            raise AssertionError("refresh should not start after a blocking decision")

    monkeypatch.setattr(
        main_app, "configure_logging", lambda *_args, **_kwargs: fake_log
    )
    monkeypatch.setattr(main_app, "enforce_single_instance", lambda *_args: None)
    monkeypatch.setattr(main_app, "create_qt_app", lambda: _FakeApp())
    monkeypatch.setattr(main_app, "set_app_icon", lambda *_args: None)
    monkeypatch.setattr(main_app, "get_base_path", lambda: Path("BASE"))
    monkeypatch.setattr(main_app, "UpdaterService", lambda: fake_updater)
    monkeypatch.setattr(main_app, "KillSwitchService", _FakeKillSwitchService)
    monkeypatch.setattr(
        main_app,
        "run_forced_update_dialog",
        lambda parent, updater_service, title, message: forced_update_calls.append(
            (parent, updater_service, title, message)
        ),
    )
    monkeypatch.setattr(
        main_app,
        "ensure_db_and_migrate",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("DB should not be touched")
        ),
    )

    with pytest.raises(SystemExit, match="Stop now"):
        main_app.main()

    assert forced_update_calls == [(None, fake_updater, "Blocked", "Stop now")]


def test_main_allows_start_when_remote_recheck_clears_cached_block(monkeypatch):
    calls = []
    fake_log = _FakeLog()
    fake_updater = object()

    class _FakeKillSwitchService:
        def __init__(self, base_path):
            self.base_path = base_path
            self.remote_block_detected = _FakeSignal()

        def evaluate_current_version(
            self,
            version,
            prefer_remote=True,
            use_service_timeout=True,
        ):
            calls.append(
                (
                    "evaluate_current_version",
                    version,
                    prefer_remote,
                    use_service_timeout,
                )
            )
            if not prefer_remote:
                return KillSwitchDecision(
                    is_blocked=True,
                    title="Blocked",
                    message="Stop now",
                    source="cache",
                    reason="block_all",
                )
            return KillSwitchDecision(is_blocked=False, source="remote")

        def refresh_current_version_async(self, version):
            calls.append(("refresh_current_version_async", version))

    monkeypatch.setattr(
        main_app, "configure_logging", lambda *_args, **_kwargs: fake_log
    )
    monkeypatch.setattr(main_app, "enforce_single_instance", lambda *_args: None)
    monkeypatch.setattr(main_app, "create_qt_app", lambda: _FakeApp())
    monkeypatch.setattr(main_app, "set_app_icon", lambda *_args: None)
    monkeypatch.setattr(main_app, "get_base_path", lambda: Path("BASE"))
    monkeypatch.setattr(main_app, "UpdaterService", lambda: fake_updater)
    monkeypatch.setattr(main_app, "KillSwitchService", _FakeKillSwitchService)
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
        lambda *_args, **kwargs: {
            "backup": _FakeBackupService(calls),
            "settings": "SETTINGS",
            "updater": kwargs["updater_service"],
            "kill_switch": "KILL_SWITCH",
        },
    )
    monkeypatch.setattr(main_app, "apply_theme", lambda *_args: None)
    monkeypatch.setattr(main_app, "create_main_window", lambda *_args: _FakeWindow())
    monkeypatch.setattr(main_app, "wire_startup_update_check", lambda *_args: None)
    monkeypatch.setattr(
        main_app.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
    )

    with pytest.raises(SystemExit) as exc_info:
        main_app.main()

    assert exc_info.value.code == 0
    assert (
        "evaluate_current_version",
        main_app.VERSION,
        True,
        False,
    ) in calls
    assert ("ensure_db_and_migrate", Path("BASE")) in calls


def test_runtime_handler_runs_forced_update_and_quits(monkeypatch):
    fake_log = _FakeLog()
    forced_update_calls = []
    quit_calls = []

    class _FakeCoreApplication:
        @staticmethod
        def quit():
            quit_calls.append("quit")

    monkeypatch.setattr(main_app, "QCoreApplication", _FakeCoreApplication)
    monkeypatch.setattr(
        main_app,
        "run_forced_update_dialog",
        lambda parent, updater_service, title, message: forced_update_calls.append(
            (parent, updater_service, title, message)
        ),
    )

    handler = main_app._RuntimeKillSwitchHandler(
        fake_log,
        updater_service="UPDATER",
        dialog_parent="WINDOW",
    )
    handler.on_remote_block_detected(
        KillSwitchDecision(
            is_blocked=True,
            title="Blocked",
            message="Stop now",
            source="remote",
            reason="block_all",
        )
    )

    assert forced_update_calls == [("WINDOW", "UPDATER", "Blocked", "Stop now")]
    assert quit_calls == ["quit"]
