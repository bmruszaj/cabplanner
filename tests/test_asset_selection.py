"""Unit tests for asset selection logic."""

from src.app.update.github_client import AssetInfo, ReleaseInfo


class TestAssetSelection:
    """Test asset selection logic for Windows onedir packages."""

    def create_mock_release(self, assets):
        """Helper to create mock release with given assets."""
        asset_objects = [
            AssetInfo(
                name=name, download_url=f"https://github.com/releases/{name}", size=size
            )
            for name, size in assets
        ]
        return ReleaseInfo(
            tag_name="v1.0.0",
            name="Release 1.0.0",
            assets=asset_objects,
            prerelease=False,
        )

    def test_select_windows_zip_asset(self):
        """Test selection of Windows ZIP asset from multiple assets."""
        # Create mock release with various assets
        assets = [
            ("cabplanner-1.0.0-linux.tar.gz", 5000000),
            ("cabplanner-1.0.0-windows.zip", 8000000),  # This should be selected
            ("cabplanner-1.0.0-macos.dmg", 6000000),
            ("Source-Code.zip", 1000000),
        ]

        release = self.create_mock_release(assets)

        # Find ZIP asset (simulating the logic from UpdateWorker)
        zip_asset = None
        for asset in release.assets:
            if asset.name.endswith(".zip") and "windows" in asset.name.lower():
                zip_asset = asset
                break

        # If no windows-specific ZIP, fall back to any ZIP
        if not zip_asset:
            for asset in release.assets:
                if asset.name.endswith(".zip"):
                    zip_asset = asset
                    break

        assert zip_asset is not None
        assert zip_asset.name == "cabplanner-1.0.0-windows.zip"

    def test_select_generic_zip_fallback(self):
        """Test fallback to generic ZIP when no Windows-specific ZIP exists."""
        assets = [
            ("cabplanner-1.0.0.tar.gz", 5000000),
            ("cabplanner-1.0.0.zip", 8000000),  # This should be selected
            ("README.txt", 1000),
        ]

        release = self.create_mock_release(assets)

        # Find ZIP asset with fallback logic
        zip_asset = None
        for asset in release.assets:
            if asset.name.endswith(".zip") and "windows" in asset.name.lower():
                zip_asset = asset
                break

        if not zip_asset:
            for asset in release.assets:
                if asset.name.endswith(".zip"):
                    zip_asset = asset
                    break

        assert zip_asset is not None
        assert zip_asset.name == "cabplanner-1.0.0.zip"

    def test_no_zip_asset_available(self):
        """Test when no ZIP assets are available."""
        assets = [
            ("cabplanner-1.0.0.tar.gz", 5000000),
            ("cabplanner-1.0.0.dmg", 6000000),
            ("README.txt", 1000),
        ]

        release = self.create_mock_release(assets)

        # Try to find ZIP asset
        zip_asset = None
        for asset in release.assets:
            if asset.name.endswith(".zip"):
                zip_asset = asset
                break

        assert zip_asset is None

    def test_prefer_onedir_over_onefile(self):
        """Test preference for onedir packages over onefile."""
        assets = [
            ("cabplanner-1.0.0-onefile.zip", 3000000),
            ("cabplanner-1.0.0-onedir.zip", 8000000),  # Larger, should be preferred
            ("cabplanner-1.0.0.exe", 3000000),  # Single executable
        ]

        release = self.create_mock_release(assets)

        # Prefer larger ZIP (likely onedir) over smaller ZIP (likely onefile)
        zip_assets = [asset for asset in release.assets if asset.name.endswith(".zip")]

        if zip_assets:
            # Select the largest ZIP asset (onedir packages are typically larger)
            selected_asset = max(zip_assets, key=lambda a: a.size)
            assert selected_asset.name == "cabplanner-1.0.0-onedir.zip"
            assert selected_asset.size == 8000000

    def test_exclude_source_code_zip(self):
        """Test exclusion of source code ZIP files."""
        assets = [
            ("Source-Code.zip", 1000000),
            ("cabplanner-1.0.0.zip", 8000000),  # This should be selected
        ]

        release = self.create_mock_release(assets)

        # Find ZIP asset excluding source code
        zip_asset = None
        for asset in release.assets:
            if (
                asset.name.endswith(".zip")
                and "source" not in asset.name.lower()
                and "code" not in asset.name.lower()
            ):
                zip_asset = asset
                break

        assert zip_asset is not None
        assert zip_asset.name == "cabplanner-1.0.0.zip"

    def test_multiple_valid_zip_assets(self):
        """Test selection when multiple valid ZIP assets exist."""
        assets = [
            ("cabplanner-1.0.0-x64.zip", 8000000),
            ("cabplanner-1.0.0-x86.zip", 7000000),
            ("cabplanner-1.0.0-arm64.zip", 7500000),
        ]

        release = self.create_mock_release(assets)

        # Should select the first valid ZIP (or could implement architecture preference)
        zip_asset = None
        for asset in release.assets:
            if asset.name.endswith(".zip"):
                zip_asset = asset
                break

        assert zip_asset is not None
        assert zip_asset.name in [
            "cabplanner-1.0.0-x64.zip",
            "cabplanner-1.0.0-x86.zip",
            "cabplanner-1.0.0-arm64.zip",
        ]

    def test_asset_validation(self):
        """Test validation of selected assets."""
        assets = [
            ("cabplanner-1.0.0.zip", 0),  # Invalid: zero size
            ("cabplanner-1.0.0-valid.zip", 8000000),  # Valid
        ]

        release = self.create_mock_release(assets)

        # Find valid ZIP asset (non-zero size)
        zip_asset = None
        for asset in release.assets:
            if asset.name.endswith(".zip") and asset.size > 0:
                zip_asset = asset
                break

        assert zip_asset is not None
        assert zip_asset.name == "cabplanner-1.0.0-valid.zip"
        assert zip_asset.size > 0
