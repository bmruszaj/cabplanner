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
    # Make sure to fetch all tags first
    run_git_command(["git", "fetch", "--tags", "--force"])

    # Get all tags with git tag command
    all_tags = run_git_command(["git", "tag", "-l"])
    print(f"Available tags: {all_tags or 'None'}")

    # Try to get the latest tag with git describe (this sometimes fails in CI)
    last_tag = run_git_command(["git", "describe", "--tags", "--abbrev=0"])

    # If git describe failed but we have tags, use manual selection
    if not last_tag and all_tags:
        print("git describe failed, using manual tag selection")
        # Split the tags into a list and sort them
        all_tags_list = all_tags.strip().split("\n")

        # Filter for tags that follow versioning pattern (v1.2.3 or 1.2.3)
        version_pattern = re.compile(r"^v?\d+\.\d+\.\d+.*$")
        versioned_tags = [tag for tag in all_tags_list if version_pattern.match(tag)]

        if versioned_tags:
            # Sort tags by version number (remove v prefix for sorting)
            def version_key(tag):
                # Remove v prefix if present
                clean_tag = re.sub(r"^v", "", tag)
                # Split into version components
                parts = clean_tag.split(".")
                # Convert numeric parts to integers for proper sorting
                return [int(p) if p.isdigit() else p for p in parts]

            # Sort tags and get the latest one
            versioned_tags.sort(key=version_key, reverse=True)
            last_tag = versioned_tags[0]
            print(f"Manually selected tag: {last_tag}")
        else:
            # If no versioned tags, use alphabetical sorting as fallback
            all_tags_list.sort(reverse=True)
            last_tag = all_tags_list[0]
            print(f"Selected non-versioned tag: {last_tag}")

    if last_tag:
        print(f"Found tag: {last_tag}")

        # Filter out repository/product prefixes from tag names
        # Remove both 'v' prefix and 'cabplanner-' prefix if present
        base_version = re.sub(r"^(v|cabplanner-)", "", last_tag)

        # Count commits since last tag
        commit_count = run_git_command(
            ["git", "rev-list", "--count", f"{last_tag}..HEAD"]
        )
        if not commit_count:
            commit_count = "0"

        print(f"Commits since tag: {commit_count}")

        # If there are commits since the last tag, increment the version
        if int(commit_count) > 0:
            # Check if base_version already has a fourth component (e.g., 1.0.0.1)
            version_parts = base_version.split(".")

            if len(version_parts) >= 4:
                # Already has a fourth component, increment it
                try:
                    version_parts[3] = str(int(version_parts[3]) + 1)
                    version = ".".join(version_parts)
                except ValueError:
                    # Non-numeric fourth component, just append commit count
                    version = f"{base_version}.{commit_count}"
            else:
                # Standard version like 1.0.0, append fourth component
                version = f"{base_version}.{commit_count}"
        else:
            version = base_version
    else:
        print("No tags found, using fallback versioning")
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
