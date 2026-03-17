"""Tests for remote startup kill switch policy."""

import json
from datetime import datetime, timedelta, timezone

from src.services.kill_switch_service import KillSwitchService


class TestKillSwitchService:
    """Coverage for startup cache rules and remote refresh behavior."""

    def test_startup_uses_fresh_cache_without_remote_fetch(self, tmp_path):
        service = KillSwitchService(
            base_path=tmp_path, cache_path=tmp_path / "cache.json"
        )
        payload = {
            "enabled": True,
            "blocked_versions": ["1.2.3"],
            "message": "Blocked build",
            "title": "Blocked",
        }
        service._cache_payload(payload)

        def _fail_remote_fetch():
            raise AssertionError("startup should not fetch remote policy")

        service._fetch_remote_payload = _fail_remote_fetch
        decision = service.evaluate_current_version("1.2.3", prefer_remote=False)

        assert decision.is_blocked is True
        assert decision.source == "cache"
        assert decision.reason == "blocked_versions"
        assert decision.title == "Blocked"
        assert decision.message == "Blocked build"

    def test_expired_cache_is_not_enforced(self, tmp_path):
        cache_path = tmp_path / "cache.json"
        wrapper = {
            "fetched_at": (
                datetime.now(timezone.utc) - timedelta(hours=48)
            ).isoformat(),
            "payload": {
                "enabled": True,
                "block_all": True,
            },
        }
        cache_path.write_text(json.dumps(wrapper))
        service = KillSwitchService(
            base_path=tmp_path,
            cache_path=cache_path,
            cache_ttl_hours=24,
        )

        decision = service.evaluate_current_version("1.0.0", prefer_remote=False)

        assert decision.is_blocked is False
        assert decision.source == "none"

    def test_remote_refresh_caches_payload_and_blocks_matching_version(self, tmp_path):
        cache_path = tmp_path / "cache.json"
        service = KillSwitchService(base_path=tmp_path, cache_path=cache_path)
        payload = {
            "enabled": True,
            "min_allowed_version": "2.0.0",
        }
        notifications = []

        service._fetch_remote_payload = lambda: payload
        service._notify_remote_block = lambda decision: notifications.append(decision)
        decision = service.refresh_current_version("1.9.9")

        assert decision.is_blocked is True
        assert decision.source == "remote"
        assert decision.reason == "min_allowed_version"
        assert len(notifications) == 1
        assert notifications[0].reason == "min_allowed_version"

        wrapper = json.loads(cache_path.read_text())
        assert wrapper["payload"] == payload
        assert "fetched_at" in wrapper

    def test_bypass_env_disables_both_cache_and_remote(self, tmp_path, monkeypatch):
        service = KillSwitchService(
            base_path=tmp_path, cache_path=tmp_path / "cache.json"
        )
        service._fetch_remote_payload = lambda: {
            "enabled": True,
            "block_all": True,
        }
        monkeypatch.setenv("CABPLANNER_KILL_SWITCH_BYPASS", "1")

        decision = service.evaluate_current_version("1.0.0", prefer_remote=False)

        assert decision.is_blocked is False
        assert decision.source == "bypass"
