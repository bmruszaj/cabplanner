"""Unit tests for the background backup service."""

import gzip
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from src.app.update.github_client import AssetInfo, ReleaseInfo
from src.services.backup_service import BackupService


class _FakeGitHubBackupClient:
    def __init__(self):
        self.created_release = None
        self.deleted_asset_ids = []
        self.repo = None
        self.token = None
        self.uploaded_asset_name = None
        self.uploaded_content_type = None
        self.uploaded_snapshot_bytes = None

    def __call__(self, repo, token):
        self.repo = repo
        self.token = token
        return self

    def get_release_by_tag(self, _tag_name):
        return None

    def create_release(self, tag_name, name, body="", draft=False, prerelease=False):
        self.created_release = {
            "tag_name": tag_name,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
        }
        return ReleaseInfo(
            tag_name=tag_name,
            name=name,
            assets=[],
            prerelease=prerelease,
            release_id=7,
            upload_url="https://uploads.github.com/repos/bmruszaj/cabplanner-backups/releases/7/assets{?name,label}",
        )

    def upload_release_asset(
        self, upload_url, asset_path, content_type="application/octet-stream"
    ):
        self.uploaded_asset_name = asset_path.name
        self.uploaded_content_type = content_type
        with gzip.open(asset_path, "rb") as handle:
            self.uploaded_snapshot_bytes = handle.read()
        return AssetInfo(
            name=asset_path.name,
            download_url=upload_url,
            size=asset_path.stat().st_size,
            asset_id=11,
        )

    def list_release_assets(self, _release_id):
        prefix = self.uploaded_asset_name.split("__", 1)[0]
        return [
            AssetInfo(self.uploaded_asset_name, "https://example.test/current", 10, 11),
            AssetInfo(
                f"{prefix}__20260316T120000Z.db.gz",
                "https://example.test/older-1",
                10,
                12,
            ),
            AssetInfo(
                f"{prefix}__20260315T120000Z.db.gz",
                "https://example.test/older-2",
                10,
                13,
            ),
            AssetInfo(
                "other-client__20260314T120000Z.db.gz",
                "https://example.test/other",
                10,
                14,
            ),
        ]

    def delete_release_asset(self, asset_id):
        self.deleted_asset_ids.append(asset_id)


def _create_sqlite_db(db_path):
    connection = sqlite3.connect(str(db_path))
    try:
        connection.execute(
            "CREATE TABLE test_items (id INTEGER PRIMARY KEY, name TEXT)"
        )
        connection.execute(
            "INSERT INTO test_items (name) VALUES (?)",
            ("backup payload",),
        )
        connection.commit()
    finally:
        connection.close()


def test_backup_service_marks_fresh_backups_as_not_due(tmp_path):
    db_path = tmp_path / "cabplanner.db"
    db_path.touch()
    state_path = tmp_path / ".backup_state.json"
    service = BackupService(db_path=db_path, base_path=tmp_path, state_path=state_path)

    service._save_state({"last_success_at": datetime.now(timezone.utc).isoformat()})
    assert service._is_backup_due() is False

    service._save_state(
        {
            "last_success_at": (
                datetime.now(timezone.utc) - timedelta(hours=25)
            ).isoformat()
        }
    )
    assert service._is_backup_due() is True


def test_backup_service_uploads_snapshot_and_prunes_old_assets(tmp_path, monkeypatch):
    db_path = tmp_path / "cabplanner.db"
    state_path = tmp_path / ".backup_state.json"
    _create_sqlite_db(db_path)
    fake_client = _FakeGitHubBackupClient()
    monkeypatch.setenv("CABPLANNER_BACKUP_TOKEN", "secret-token")

    service = BackupService(
        db_path=db_path,
        base_path=tmp_path,
        state_path=state_path,
        client_factory=fake_client,
        retention_per_client=2,
    )

    service._perform_backup()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert fake_client.repo == "bmruszaj/cabplanner-backups"
    assert fake_client.token == "secret-token"
    assert fake_client.created_release is not None
    assert fake_client.uploaded_asset_name == state["last_asset_name"]
    assert state["client_id"] in fake_client.uploaded_asset_name
    assert fake_client.uploaded_content_type == "application/gzip"
    assert fake_client.uploaded_snapshot_bytes.startswith(b"SQLite format 3")
    assert fake_client.deleted_asset_ids == [13]
