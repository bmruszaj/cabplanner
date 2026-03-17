"""Background GitHub backup service for the user database."""

import gzip
import json
import logging
import os
import platform
import re
import shutil
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Any

import requests
from PySide6.QtCore import QObject, QTimer

from src.app.update.github_client import GitHubClient, ReleaseInfo

logger = logging.getLogger(__name__)

DEFAULT_BACKUP_REPO = "bmruszaj/cabplanner-backups"
DEFAULT_BACKUP_RELEASE_TAG = "backups"
DEFAULT_BACKUP_RELEASE_NAME = "Cabplanner Backups"
DEFAULT_BACKUP_RELEASE_BODY = "Automatyczne backupy baz danych Cabplanner."
DEFAULT_STATE_FILE_NAME = ".backup_state.json"
DEFAULT_BACKUP_INTERVAL_HOURS = 24
DEFAULT_CHECK_INTERVAL_MINUTES = 60
DEFAULT_STARTUP_DELAY_MS = 15000
DEFAULT_RETENTION_PER_CLIENT = 30
DEFAULT_BACKUP_TOKEN_ENV = "CABPLANNER_BACKUP_TOKEN"
FALLBACK_BACKUP_TOKEN_ENV = "GITHUB_TOKEN"


class BackupService(QObject):
    """Schedule and upload SQLite backups to GitHub release assets."""

    def __init__(
        self,
        db_path: Path,
        base_path: Path | None = None,
        state_path: Path | None = None,
        repo: str | None = None,
        release_tag: str | None = None,
        release_name: str | None = None,
        client_factory=GitHubClient,
        backup_interval_hours: int = DEFAULT_BACKUP_INTERVAL_HOURS,
        check_interval_minutes: int = DEFAULT_CHECK_INTERVAL_MINUTES,
        startup_delay_ms: int = DEFAULT_STARTUP_DELAY_MS,
        retention_per_client: int = DEFAULT_RETENTION_PER_CLIENT,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        resolved_db_path = Path(db_path)
        resolved_base_path = (
            Path(base_path) if base_path is not None else resolved_db_path.parent
        )
        self.db_path = resolved_db_path
        self.base_path = resolved_base_path
        self.state_path = (
            Path(state_path)
            if state_path is not None
            else resolved_base_path / DEFAULT_STATE_FILE_NAME
        )
        self.repo = repo or os.environ.get(
            "CABPLANNER_BACKUP_REPO", DEFAULT_BACKUP_REPO
        )
        self.release_tag = release_tag or os.environ.get(
            "CABPLANNER_BACKUP_RELEASE_TAG", DEFAULT_BACKUP_RELEASE_TAG
        )
        self.release_name = release_name or os.environ.get(
            "CABPLANNER_BACKUP_RELEASE_NAME", DEFAULT_BACKUP_RELEASE_NAME
        )
        self.client_factory = client_factory
        self.backup_interval = timedelta(hours=backup_interval_hours)
        self.retention_per_client = max(1, retention_per_client)
        self.startup_delay_ms = max(0, startup_delay_ms)
        self.check_interval_ms = max(60_000, check_interval_minutes * 60 * 1000)
        self._state_lock = Lock()
        self._backup_in_flight = False
        self._started = False
        self._missing_token_logged = False
        self._check_timer = QTimer(self)
        self._check_timer.setInterval(self.check_interval_ms)
        self._check_timer.timeout.connect(self.run_due_backup_async)

    def start(self) -> None:
        """Start background due checks for database backups."""
        if self._started:
            return

        self._started = True
        self._check_timer.start()
        QTimer.singleShot(self.startup_delay_ms, self.run_due_backup_async)
        logger.info(
            "Backup service started: repo=%s interval=%s state=%s",
            self.repo,
            self.backup_interval,
            self.state_path,
        )

    def stop(self) -> None:
        """Stop background due checks."""
        if not self._started:
            return

        self._check_timer.stop()
        self._started = False

    def run_due_backup_async(self, force: bool = False) -> None:
        """Start an asynchronous backup when the schedule says it is due."""
        if not force and not self._is_backup_due():
            logger.debug("Skipping backup because the current backup is still fresh")
            return

        token = self._get_backup_token()
        if not token:
            if not self._missing_token_logged:
                logger.warning(
                    "Backup service disabled because %s is not set",
                    DEFAULT_BACKUP_TOKEN_ENV,
                )
                self._missing_token_logged = True
            return
        self._missing_token_logged = False

        with self._state_lock:
            if self._backup_in_flight:
                logger.debug("Backup already in flight")
                return
            self._backup_in_flight = True

        Thread(
            target=self._backup_worker, name="cabplanner-backup", daemon=True
        ).start()

    def _backup_worker(self) -> None:
        """Execute the backup on a background thread."""
        try:
            self._perform_backup()
        except Exception as exc:
            logger.exception("Background backup failed: %s", exc)
            state = self._load_state()
            state["last_error"] = str(exc)
            state["last_failure_at"] = datetime.now(timezone.utc).isoformat()
            self._save_state(state)
        finally:
            with self._state_lock:
                self._backup_in_flight = False

    def _perform_backup(self) -> None:
        """Create a snapshot and upload it to GitHub."""
        state = self._load_state()
        client_id = self._get_or_create_client_id(state)
        now = datetime.now(timezone.utc)
        state["last_attempt_at"] = now.isoformat()
        state["last_error"] = ""
        self._save_state(state)

        if not self.db_path.exists():
            message = f"Database file not found: {self.db_path}"
            logger.warning(message)
            state["last_error"] = message
            self._save_state(state)
            return

        token = self._get_backup_token()
        if not token:
            return

        client = self.client_factory(self.repo, token)
        release = self._ensure_release(client)
        asset_name = self._build_asset_name(client_id, now)

        with tempfile.TemporaryDirectory(prefix="cabplanner-backup-") as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            snapshot_path = temp_dir / f"{client_id}.db"
            archive_path = temp_dir / asset_name
            self._create_database_snapshot(snapshot_path)
            self._compress_snapshot(snapshot_path, archive_path)
            uploaded_asset = client.upload_release_asset(
                self._require_upload_url(release),
                archive_path,
                content_type="application/gzip",
            )

        state["last_success_at"] = now.isoformat()
        state["last_error"] = ""
        state["last_asset_name"] = uploaded_asset.name
        self._save_state(state)
        self._prune_old_assets(client, release, client_id)
        logger.info("Database backup uploaded successfully as %s", uploaded_asset.name)

    def _ensure_release(self, client: GitHubClient) -> ReleaseInfo:
        """Return the configured release, creating it when necessary."""
        existing_release = client.get_release_by_tag(self.release_tag)
        if existing_release is not None:
            return existing_release

        try:
            return client.create_release(
                tag_name=self.release_tag,
                name=self.release_name,
                body=DEFAULT_BACKUP_RELEASE_BODY,
                draft=False,
                prerelease=False,
            )
        except requests.exceptions.HTTPError as exc:
            response = getattr(exc, "response", None)
            if response is not None and response.status_code == 422:
                raced_release = client.get_release_by_tag(self.release_tag)
                if raced_release is not None:
                    return raced_release
            raise

    def _prune_old_assets(
        self, client: GitHubClient, release: ReleaseInfo, client_id: str
    ) -> None:
        """Keep only the most recent assets for the current client."""
        release_id = release.release_id
        if release_id is None:
            logger.warning("Skipping backup retention because release_id is missing")
            return

        prefix = f"{client_id}__"
        assets = [
            asset
            for asset in client.list_release_assets(release_id)
            if asset.name.startswith(prefix)
        ]
        assets.sort(key=lambda asset: asset.name, reverse=True)
        for old_asset in assets[self.retention_per_client :]:
            if old_asset.asset_id is None:
                continue
            client.delete_release_asset(old_asset.asset_id)
            logger.info("Deleted old backup asset %s", old_asset.name)

    def _create_database_snapshot(self, snapshot_path: Path) -> None:
        """Create a consistent SQLite snapshot using the backup API."""
        source = sqlite3.connect(str(self.db_path), timeout=30)
        destination = sqlite3.connect(str(snapshot_path), timeout=30)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

    @staticmethod
    def _compress_snapshot(snapshot_path: Path, archive_path: Path) -> None:
        """Compress a snapshot to reduce GitHub asset size."""
        with (
            snapshot_path.open("rb") as source,
            gzip.open(archive_path, "wb", compresslevel=6) as destination,
        ):
            shutil.copyfileobj(source, destination)

    def _is_backup_due(self) -> bool:
        """Return whether a new backup should be attempted now."""
        state = self._load_state()
        raw_last_success = state.get("last_success_at")
        if not isinstance(raw_last_success, str) or not raw_last_success.strip():
            return True

        last_success = self._parse_datetime(raw_last_success)
        if last_success is None:
            return True

        return datetime.now(timezone.utc) - last_success >= self.backup_interval

    def _get_or_create_client_id(self, state: dict[str, Any]) -> str:
        """Return a stable per-install backup identifier."""
        raw_client_id = state.get("client_id")
        if isinstance(raw_client_id, str) and raw_client_id.strip():
            return raw_client_id.strip()

        host_name = platform.node() or os.environ.get("COMPUTERNAME") or "client"
        safe_host_name = self._sanitize_name(host_name)[:24] or "client"
        client_id = f"{safe_host_name}-{uuid.uuid4().hex[:8]}"
        state["client_id"] = client_id
        self._save_state(state)
        return client_id

    def _load_state(self) -> dict[str, Any]:
        """Load persisted backup state from disk."""
        if not self.state_path.exists():
            return {}

        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Ignoring invalid backup state file: %s", exc)
            return {}

        if isinstance(payload, dict):
            return payload

        logger.warning("Ignoring backup state file with wrong shape")
        return {}

    def _save_state(self, state: dict[str, Any]) -> None:
        """Persist backup state atomically."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = Path(f"{self.state_path}.tmp")
        temp_path.write_text(
            json.dumps(state, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(self.state_path)

    def _get_backup_token(self) -> str:
        """Resolve the GitHub token used for backup uploads."""
        return os.environ.get(DEFAULT_BACKUP_TOKEN_ENV) or os.environ.get(
            FALLBACK_BACKUP_TOKEN_ENV, ""
        )

    @staticmethod
    def _build_asset_name(client_id: str, when: datetime) -> str:
        """Build a stable, sortable asset name."""
        return f"{client_id}__{when.strftime('%Y%m%dT%H%M%SZ')}.db.gz"

    @staticmethod
    def _require_upload_url(release: ReleaseInfo) -> str:
        """Return a release upload URL or fail loudly."""
        if release.upload_url:
            return release.upload_url
        raise ValueError("GitHub release response is missing upload_url")

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Parse an ISO timestamp and normalize it to UTC."""
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
    def _sanitize_name(value: str) -> str:
        """Sanitize hostnames for use in file names."""
        return re.sub(r"[^A-Za-z0-9-]+", "-", value).strip("-").lower()
