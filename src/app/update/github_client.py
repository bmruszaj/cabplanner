"""GitHub API client for release information."""

import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional, List

import requests

logger = logging.getLogger(__name__)


@dataclass
class AssetInfo:
    """Information about a release asset."""

    name: str
    download_url: str
    size: int


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""

    tag_name: str
    name: str
    assets: List[AssetInfo]
    prerelease: bool


class GitHubClient:
    """Client for GitHub API operations."""

    def __init__(self, repo: str, token: Optional[str] = None):
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = 10

    def _get_headers(self) -> dict:
        """Get HTTP headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Cabplanner-Updater/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def get_latest_release(self) -> ReleaseInfo:
        """Get the latest release information from GitHub."""
        url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        logger.debug("Fetching latest release from: %s", url)

        try:
            response = requests.get(
                url, headers=self._get_headers(), timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            assets = [
                AssetInfo(
                    name=asset["name"],
                    download_url=asset["browser_download_url"],
                    size=asset["size"],
                )
                for asset in data.get("assets", [])
            ]

            return ReleaseInfo(
                tag_name=data["tag_name"],
                name=data["name"],
                assets=assets,
                prerelease=data.get("prerelease", False),
            )

        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching release info")
            raise
        except requests.exceptions.RequestException as e:
            logger.error("Network error while fetching release info: %s", e)
            raise
        except KeyError as e:
            logger.error("Invalid response format: missing key %s", e)
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
