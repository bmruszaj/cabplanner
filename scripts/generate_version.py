#!/usr/bin/env python
"""
Script for generating version number based on Git tags.
Saves the version to .version file in the project root directory.

Usage:
    python scripts/generate_version.py
"""

import os
import re
import subprocess
from pathlib import Path


def run_git_command(cmd):
    """Runs a git command and returns the result as a string."""
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"Error executing git command: {e}")
        return None


def get_version_from_tags():
    """
    Generates version number based on Git tags.

    Rules:
    1. If a tag exists, use it as the base version
    2. If there are commits since the last tag, add commit counter
    3. If no tags, use base version 1.0.0 + commit count
    """
    # Check if tags exist
    last_tag = run_git_command(["git", "describe", "--tags", "--abbrev=0"])

    if last_tag:
        # Remove 'v' prefix if present
        base_version = re.sub(r"^v", "", last_tag)

        # Count commits since last tag
        commit_count = run_git_command(
            ["git", "rev-list", "--count", f"{last_tag}..HEAD"]
        )
        if not commit_count:
            commit_count = "0"

        # If there are commits since the last tag, add counter
        if int(commit_count) > 0:
            version = f"{base_version}.{commit_count}"
        else:
            version = base_version
    else:
        # No tags, use base version 1.0.0 + commit count
        commit_count = run_git_command(["git", "rev-list", "--count", "HEAD"])
        if not commit_count:
            commit_count = "0"
        version = f"1.0.0.{commit_count}"

    return version


def save_version(version):
    """Saves the version to .version file in the project root directory."""
    version_file = Path(__file__).resolve().parents[1] / ".version"
    try:
        with open(version_file, "w") as f:
            f.write(version)
        print(f"Saved version {version} to file {version_file}")
        return True
    except Exception as e:
        print(f"Error saving version to file: {e}")
        return False


def main():
    """Main function."""
    version = get_version_from_tags()
    if version:
        save_version(version)
        print(f"Generated version: {version}")
        # Set environment variable (useful in GitHub Actions)
        if "GITHUB_ENV" in os.environ:
            with open(os.environ["GITHUB_ENV"], "a") as f:
                f.write(f"VERSION={version}\n")
    else:
        print("Failed to generate version.")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
