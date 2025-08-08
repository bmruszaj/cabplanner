"""Unit tests for ZIP operations and security."""

import pytest
import tempfile
import zipfile
from pathlib import Path

from src.app.update.zipops import (
    safe_extract,
    find_app_root,
    verify_onedir_structure,
    UnsafeZipError,
)


class TestZipOperations:
    """Test ZIP extraction safety and validation."""

    def test_safe_extract_normal_files(self):
        """Test extraction of normal, safe ZIP files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "test.zip"
            extract_to = temp_path / "extracted"

            # Create a safe ZIP file
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("file1.txt", "content1")
                zf.writestr("subdir/file2.txt", "content2")
                zf.writestr("cabplanner.exe", "fake exe content")

            # Should extract without issues
            safe_extract(zip_path, extract_to)

            # Verify files were extracted
            assert (extract_to / "file1.txt").exists()
            assert (extract_to / "subdir" / "file2.txt").exists()
            assert (extract_to / "cabplanner.exe").exists()

    def test_safe_extract_zip_slip_protection(self):
        """Test protection against zip-slip attacks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "malicious.zip"
            extract_to = temp_path / "extracted"

            # Create malicious ZIP with path traversal
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("../../../etc/passwd", "malicious content")
                zf.writestr("..\\..\\windows\\system32\\evil.exe", "malicious exe")
                zf.writestr("normal_file.txt", "safe content")

            # Should raise UnsafeZipError
            with pytest.raises(UnsafeZipError) as exc_info:
                safe_extract(zip_path, extract_to)

            assert "Unsafe path in ZIP" in str(exc_info.value)

    def test_safe_extract_absolute_paths(self):
        """Test protection against absolute paths in ZIP."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "absolute.zip"
            extract_to = temp_path / "extracted"

            # Create ZIP with absolute paths
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("/etc/passwd", "malicious content")
                zf.writestr("C:\\Windows\\System32\\evil.exe", "malicious exe")

            # Should raise UnsafeZipError
            with pytest.raises(UnsafeZipError):
                safe_extract(zip_path, extract_to)

    def test_find_app_root_success(self):
        """Test finding application root when executable exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure with executable
            app_dir = temp_path / "app"
            app_dir.mkdir()
            exe_path = app_dir / "cabplanner.exe"
            exe_path.write_bytes(b"fake executable content")

            # Should find the app root
            result = find_app_root(temp_path)
            assert result == app_dir

    def test_find_app_root_nested(self):
        """Test finding application root in nested directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested structure
            nested_dir = temp_path / "outer" / "inner" / "app"
            nested_dir.mkdir(parents=True)
            exe_path = nested_dir / "cabplanner.exe"
            exe_path.write_bytes(b"fake executable content")

            # Should find the nested app root
            result = find_app_root(temp_path)
            assert result == nested_dir

    def test_find_app_root_not_found(self):
        """Test when executable is not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some files but no executable
            (temp_path / "readme.txt").write_text("not an executable")

            # Should return None
            result = find_app_root(temp_path)
            assert result is None

    def test_find_app_root_empty_executable(self):
        """Test when executable exists but is empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create empty executable
            app_dir = temp_path / "app"
            app_dir.mkdir()
            exe_path = app_dir / "cabplanner.exe"
            exe_path.write_bytes(b"")  # Empty file

            # Should return None for empty executable
            result = find_app_root(temp_path)
            assert result is None

    def test_find_app_root_multiple_executables(self):
        """Test when multiple executables exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple executables
            app1_dir = temp_path / "app1"
            app1_dir.mkdir()
            (app1_dir / "cabplanner.exe").write_bytes(b"first exe")

            app2_dir = temp_path / "app2"
            app2_dir.mkdir()
            (app2_dir / "cabplanner.exe").write_bytes(b"second exe")

            # Should return one of them (first found)
            result = find_app_root(temp_path)
            assert result in [app1_dir, app2_dir]

    def test_verify_onedir_structure_valid(self):
        """Test verification of valid onedir structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create valid onedir structure
            exe_path = temp_path / "cabplanner.exe"
            exe_path.write_bytes(b"fake executable")

            internal_dir = temp_path / "_internal"
            internal_dir.mkdir()
            (internal_dir / "some_lib.dll").write_bytes(b"library")

            # Should verify successfully
            assert verify_onedir_structure(temp_path) is True

    def test_verify_onedir_structure_missing_exe(self):
        """Test verification fails when executable is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create _internal but no executable
            internal_dir = temp_path / "_internal"
            internal_dir.mkdir()

            # Should fail verification
            assert verify_onedir_structure(temp_path) is False

    def test_verify_onedir_structure_missing_internal(self):
        """Test verification fails when _internal directory is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create executable but no _internal
            exe_path = temp_path / "cabplanner.exe"
            exe_path.write_bytes(b"fake executable")

            # Should fail verification
            assert verify_onedir_structure(temp_path) is False

    def test_verify_onedir_structure_internal_is_file(self):
        """Test verification fails when _internal is a file instead of directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create executable and _internal as file
            exe_path = temp_path / "cabplanner.exe"
            exe_path.write_bytes(b"fake executable")

            internal_file = temp_path / "_internal"
            internal_file.write_text("not a directory")

            # Should fail verification
            assert verify_onedir_structure(temp_path) is False
