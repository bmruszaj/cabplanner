"""Remote kill switch for blocking broken packaged versions."""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Any

from packaging.version import InvalidVersion
from PySide6.QtCore import QObject, Signal

from src.app.paths import get_base_path
from src.app.update.github_client import GitHubClient
from src.app.update.versioning import parse_version
from src.version import VERSION

logger = logging.getLogger(__name__)

DEFAULT_KILL_SWITCH_REPO = "bmruszaj/cabplanner"
DEFAULT_KILL_SWITCH_PATH = "kill-switch.json"
DEFAULT_KILL_SWITCH_TITLE = "Wymagana aktualizacja"
DEFAULT_KILL_SWITCH_MESSAGE = (
    "Ta wersja aplikacji zostala wylaczona. Zaktualizuj Cabplanner do nowszej wersji."
)
DEFAULT_CACHE_FILE_NAME = ".kill_switch_cache.json"
DEFAULT_CACHE_TTL_HOURS = 24
DEFAULT_REMOTE_TIMEOUT_SECONDS = 3


@dataclass(frozen=True)
class KillSwitchDecision:
    """Decision produced by the kill switch evaluation."""

    is_blocked: bool
    title: str = DEFAULT_KILL_SWITCH_TITLE
    message: str = DEFAULT_KILL_SWITCH_MESSAGE
    source: str = "none"
    reason: str = ""


class KillSwitchService(QObject):
    """Fetch and evaluate a remote kill switch policy for the current app version."""

    remote_block_detected = Signal(object)

    def __init__(
        self,
        base_path: Path | None = None,
        cache_path: Path | None = None,
        repo: str | None = None,
        config_path: str | None = None,
        client_factory=GitHubClient,
        cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS,
        remote_timeout_seconds: int = DEFAULT_REMOTE_TIMEOUT_SECONDS,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        resolved_base_path = (
            Path(base_path) if base_path is not None else get_base_path()
        )
        self.base_path = resolved_base_path
        self.cache_path = (
            Path(cache_path)
            if cache_path is not None
            else resolved_base_path / DEFAULT_CACHE_FILE_NAME
        )
        self.repo = repo or os.environ.get(
            "CABPLANNER_KILL_SWITCH_REPO", DEFAULT_KILL_SWITCH_REPO
        )
        self.config_path = config_path or os.environ.get(
            "CABPLANNER_KILL_SWITCH_PATH", DEFAULT_KILL_SWITCH_PATH
        )
        self.client_factory = client_factory
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.remote_timeout_seconds = remote_timeout_seconds
        self._state_lock = Lock()
        self._refresh_in_flight = False
        self._remote_block_notified = False

    def evaluate_current_version(
        self,
        current_version: str = VERSION,
        prefer_remote: bool = True,
        use_service_timeout: bool = True,
    ) -> KillSwitchDecision:
        """Evaluate the current version against remote policy or cached fallback."""
        if os.environ.get("CABPLANNER_KILL_SWITCH_BYPASS") == "1":
            logger.warning("Kill switch bypassed via CABPLANNER_KILL_SWITCH_BYPASS=1")
            return KillSwitchDecision(is_blocked=False, source="bypass")

        payload, source = self._load_payload(
            prefer_remote=prefer_remote,
            use_service_timeout=use_service_timeout,
        )
        return self._build_decision(payload, source, current_version)

    def refresh_current_version_async(self, current_version: str = VERSION) -> None:
        """Refresh the remote policy in the background without blocking startup."""
        with self._state_lock:
            if self._refresh_in_flight:
                logger.debug("Kill switch refresh already in flight")
                return
            self._refresh_in_flight = True

        def _worker() -> None:
            try:
                self.refresh_current_version(current_version=current_version)
            finally:
                with self._state_lock:
                    self._refresh_in_flight = False

        Thread(target=_worker, name="kill-switch-refresh", daemon=True).start()

    def refresh_current_version(
        self, current_version: str = VERSION
    ) -> KillSwitchDecision:
        """Refresh remote policy now and notify the app if it becomes blocked."""
        decision = self.evaluate_current_version(
            current_version=current_version,
            prefer_remote=True,
            use_service_timeout=True,
        )
        if decision.is_blocked and decision.source == "remote":
            logger.error(
                "Remote kill switch blocks version %s with rule %s",
                current_version,
                decision.reason or "unknown",
            )
            self._notify_remote_block(decision)
        return decision

    def _load_payload(
        self,
        prefer_remote: bool,
        use_service_timeout: bool,
    ) -> tuple[dict[str, Any] | None, str]:
        """Load policy from cache, optionally refreshing from remote first."""
        if prefer_remote:
            try:
                payload = self._fetch_remote_payload(
                    use_service_timeout=use_service_timeout
                )
                self._cache_payload(payload)
                return payload, "remote"
            except Exception as exc:
                logger.warning("Kill switch remote fetch failed: %s", exc)

        cached_payload = self._load_cached_payload()
        if cached_payload is not None:
            logger.info("Using cached kill switch payload")
            return cached_payload, "cache"

        return None, "none"

    def _fetch_remote_payload(self, use_service_timeout: bool = True) -> dict[str, Any]:
        """Fetch kill switch config from GitHub."""
        client = self.client_factory(self.repo)
        if use_service_timeout and hasattr(client, "timeout"):
            client.timeout = self.remote_timeout_seconds
        payload = client.get_repo_json(self.config_path)
        if not isinstance(payload, dict):
            raise ValueError("Kill switch payload must be a JSON object")
        return payload

    def _cache_payload(self, payload: dict[str, Any]) -> None:
        """Persist the last valid payload so offline clients can still enforce it."""
        wrapper = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.cache_path.with_suffix(f"{self.cache_path.suffix}.tmp")
        temp_path.write_text(json.dumps(wrapper, ensure_ascii=True, sort_keys=True))
        temp_path.replace(self.cache_path)

    def _load_cached_payload(self) -> dict[str, Any] | None:
        """Load cached payload from local file if it is still fresh."""
        if not self.cache_path.exists():
            return None

        try:
            wrapper = json.loads(self.cache_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring invalid kill switch cache file: %s", exc)
            return None

        if not isinstance(wrapper, dict):
            logger.warning("Ignoring kill switch cache with wrong shape")
            return None

        fetched_at_raw = wrapper.get("fetched_at")
        payload = wrapper.get("payload")
        if not isinstance(payload, dict):
            logger.warning("Ignoring kill switch cache without payload object")
            return None

        fetched_at = self._parse_datetime(fetched_at_raw)
        if fetched_at is None:
            logger.warning("Ignoring kill switch cache with invalid fetched_at")
            return None

        if self._is_cache_expired(fetched_at):
            logger.info("Kill switch cache expired at %s", fetched_at.isoformat())
            return None

        return payload

    def _build_decision(
        self,
        payload: dict[str, Any] | None,
        source: str,
        current_version: str,
    ) -> KillSwitchDecision:
        """Build a decision object from a payload and app version."""
        if not payload:
            return KillSwitchDecision(is_blocked=False, source=source)

        if not self._as_bool(payload.get("enabled", False)):
            logger.debug("Kill switch payload is disabled")
            return KillSwitchDecision(is_blocked=False, source=source)

        is_blocked, reason = self._is_version_blocked(payload, current_version)
        if not is_blocked:
            return KillSwitchDecision(is_blocked=False, source=source)

        title = str(payload.get("title") or DEFAULT_KILL_SWITCH_TITLE)
        message = str(payload.get("message") or DEFAULT_KILL_SWITCH_MESSAGE)
        return KillSwitchDecision(
            is_blocked=True,
            title=title,
            message=message,
            source=source,
            reason=reason,
        )

    def _notify_remote_block(self, decision: KillSwitchDecision) -> None:
        """Emit the runtime shutdown notification at most once."""
        with self._state_lock:
            if self._remote_block_notified:
                logger.debug("Remote kill switch notification already emitted")
                return
            self._remote_block_notified = True

        self.remote_block_detected.emit(decision)

    def _is_version_blocked(
        self, payload: dict[str, Any], current_version: str
    ) -> tuple[bool, str]:
        """Return whether the current version is blocked and which rule matched."""
        if self._as_bool(payload.get("block_all", False)):
            return True, "block_all"

        try:
            current = parse_version(current_version)
        except InvalidVersion as exc:
            logger.warning(
                "Kill switch skipped due to invalid app version %s: %s",
                current_version,
                exc,
            )
            return False, ""

        blocked_versions = payload.get("blocked_versions") or []
        if isinstance(blocked_versions, str):
            blocked_versions = [blocked_versions]

        for blocked_version in blocked_versions:
            try:
                if parse_version(str(blocked_version)) == current:
                    return True, "blocked_versions"
            except InvalidVersion:
                logger.warning(
                    "Ignoring invalid blocked version in kill switch payload: %s",
                    blocked_version,
                )

        min_allowed_version = str(payload.get("min_allowed_version") or "").strip()
        if min_allowed_version:
            try:
                if current < parse_version(min_allowed_version):
                    return True, "min_allowed_version"
            except InvalidVersion:
                logger.warning(
                    "Ignoring invalid min_allowed_version in kill switch payload: %s",
                    min_allowed_version,
                )

        return False, ""

    def _is_cache_expired(self, fetched_at: datetime) -> bool:
        """Return whether a cached payload is too old to enforce."""
        now = datetime.now(timezone.utc)
        return now - fetched_at > self.cache_ttl

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Parse an ISO datetime string and normalize it to UTC."""
        if not isinstance(value, str) or not value.strip():
            return None

        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _as_bool(value: Any) -> bool:
        """Coerce config values to bool without treating arbitrary strings as true."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
