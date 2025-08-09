"""Update error definitions and custom exceptions."""


class UpdateError(Exception):
    """Base exception for update operations."""
    pass


class NetworkError(UpdateError):
    """Network/connectivity issues."""
    pass


class NoAssetError(UpdateError):
    """No suitable asset found in release."""
    pass


class BadArchiveError(UpdateError):
    """Archive corruption or invalid structure."""
    pass


class UpdateCancelledError(UpdateError):
    """Operation cancelled by user."""
    pass


class NotFrozenError(UpdateError):
    """Cannot update in development mode."""
    pass


class GitHubAPIError(UpdateError):
    """GitHub API error."""
    pass


class DownloadFailedError(UpdateError):
    """Download failed."""
    pass


class ExtractionFailedError(UpdateError):
    """ZIP extraction failed."""
    pass


class VerificationFailedError(UpdateError):
    """Package verification failed."""
    pass


class ScriptFailedError(UpdateError):
    """PowerShell script execution failed."""
    pass
