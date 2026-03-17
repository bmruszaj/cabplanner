"""GitHub API client for release information and backup assets."""

import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import requests

logger = logging.getLogger(__name__)


@dataclass
class AssetInfo:
    """Information about a release asset."""

    name: str
    download_url: str
    size: int
    asset_id: int | None = None
    created_at: str | None = None


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""

    tag_name: str
    name: str
    assets: List[AssetInfo]
    prerelease: bool
    release_id: int | None = None
    upload_url: str | None = None


class GitHubClient:
    """Client for GitHub API operations."""

    def __init__(self, repo: str, token: Optional[str] = None):
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = 10

    def _get_headers(self, content_type: str | None = None) -> dict:
        """Get HTTP headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Cabplanner/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if content_type:
            headers["Content-Type"] = content_type
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    @staticmethod
    def _parse_asset(data: dict) -> AssetInfo:
        """Convert GitHub API asset payload into an AssetInfo object."""
        return AssetInfo(
            name=data["name"],
            download_url=data["browser_download_url"],
            size=data["size"],
            asset_id=data.get("id"),
            created_at=data.get("created_at"),
        )

    def _parse_release(self, data: dict) -> ReleaseInfo:
        """Convert GitHub API release payload into a ReleaseInfo object."""
        assets = [self._parse_asset(asset) for asset in data.get("assets", [])]
        return ReleaseInfo(
            tag_name=data["tag_name"],
            name=data["name"],
            assets=assets,
            prerelease=data.get("prerelease", False),
            release_id=data.get("id"),
            upload_url=data.get("upload_url"),
        )

    def get_latest_release(self) -> ReleaseInfo:
        """Get the latest release information from GitHub."""
        url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        logger.debug("Fetching latest release from: %s", url)

        try:
            response = requests.get(
                url, headers=self._get_headers(), timeout=self.timeout
            )
            response.raise_for_status()
            return self._parse_release(response.json())

        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching release info")
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Network error while fetching release info: %s", e)
            raise
        except KeyError as e:
            logger.error("Invalid response format: missing key %s", e)
            raise

    def get_release_by_tag(self, tag_name: str) -> ReleaseInfo | None:
        """Get a release by tag, returning None when it does not exist."""
        url = f"https://api.github.com/repos/{self.repo}/releases/tags/{tag_name}"
        logger.debug("Fetching release by tag from: %s", url)

        try:
            response = requests.get(
                url, headers=self._get_headers(), timeout=self.timeout
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return self._parse_release(response.json())
        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching release by tag: %s", tag_name)
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Network error while fetching release %s: %s", tag_name, e)
            raise
        except KeyError as e:
            logger.error("Invalid release response for tag %s: %s", tag_name, e)
            raise

    def create_release(
        self,
        tag_name: str,
        name: str,
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
    ) -> ReleaseInfo:
        """Create and return a GitHub release."""
        url = f"https://api.github.com/repos/{self.repo}/releases"
        payload = {
            "tag_name": tag_name,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
            "generate_release_notes": False,
        }
        logger.debug("Creating release %s in repo %s", tag_name, self.repo)

        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_release(response.json())
        except requests.exceptions.Timeout:
            logger.error("Timeout while creating release: %s", tag_name)
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Network error while creating release %s: %s", tag_name, e)
            raise
        except KeyError as e:
            logger.error("Invalid release creation response for %s: %s", tag_name, e)
            raise

    def list_release_assets(self, release_id: int) -> List[AssetInfo]:
        """List assets attached to a GitHub release."""
        url = f"https://api.github.com/repos/{self.repo}/releases/{release_id}/assets"
        logger.debug("Listing release assets from: %s", url)

        try:
            response = requests.get(
                url, headers=self._get_headers(), timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
            return [self._parse_asset(asset) for asset in payload]
        except requests.exceptions.Timeout:
            logger.error("Timeout while listing release assets for %s", release_id)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(
                "Network error while listing release assets for %s: %s", release_id, e
            )
            raise
        except (KeyError, TypeError) as e:
            logger.error("Invalid assets response for release %s: %s", release_id, e)
            raise

    def upload_release_asset(
        self,
        upload_url: str,
        asset_path: Path,
        content_type: str = "application/octet-stream",
    ) -> AssetInfo:
        """Upload a binary asset to an existing GitHub release."""
        upload_target = upload_url.split("{", 1)[0]
        logger.debug("Uploading release asset %s to %s", asset_path.name, upload_target)

        try:
            with asset_path.open("rb") as handle:
                response = requests.post(
                    upload_target,
                    headers=self._get_headers(content_type=content_type),
                    params={"name": asset_path.name},
                    data=handle,
                    timeout=max(self.timeout, 120),
                )
            response.raise_for_status()
            return self._parse_asset(response.json())
        except requests.exceptions.Timeout:
            logger.error("Timeout while uploading release asset: %s", asset_path.name)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(
                "Network error while uploading release asset %s: %s",
                asset_path.name,
                e,
            )
            raise
        except KeyError as e:
            logger.error("Invalid asset upload response for %s: %s", asset_path.name, e)
            raise

    def delete_release_asset(self, asset_id: int) -> None:
        """Delete an existing asset from a GitHub release."""
        url = f"https://api.github.com/repos/{self.repo}/releases/assets/{asset_id}"
        logger.debug("Deleting release asset %s", asset_id)

        try:
            response = requests.delete(
                url, headers=self._get_headers(), timeout=self.timeout
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error("Timeout while deleting release asset: %s", asset_id)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(
                "Network error while deleting release asset %s: %s", asset_id, e
            )
            raise

    def get_repo_json(self, path: str) -> dict:
        """Get a JSON file from the repository default branch via the contents API."""
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}"
        logger.debug("Fetching repository JSON from: %s", url)

        try:
            response = requests.get(
                url, headers=self._get_headers(), timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get("type") != "file":
                raise KeyError(f"Repository path is not a file: {path}")

            encoded_content = data.get("content")
            encoding = data.get("encoding")
            if not encoded_content or encoding != "base64":
                raise KeyError(f"Missing base64 content for repository file: {path}")

            raw_text = base64.b64decode(encoded_content).decode("utf-8")
            return json.loads(raw_text)

        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching repository JSON: %s", path)
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Network error while fetching repository JSON %s: %s", path, e)
            raise
        except (ValueError, KeyError) as e:
            logger.error("Invalid repository JSON response for %s: %s", path, e)
            raise
