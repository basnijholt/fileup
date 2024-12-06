"""Tests for the ``fileup`` package."""

from __future__ import annotations

import datetime
import io
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

import fileup
from fileup import FileupConfig

if TYPE_CHECKING:
    from types import ModuleType

    import pytest_mock.plugin


def test_get_valid_filename() -> None:
    """Test the get_valid_filename function."""
    assert (
        fileup.get_valid_filename("john's portrait in 2004.jpg")
        == "johns_portrait_in_2004.jpg"
    )


def test_read_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test the read_config function."""
    config_content = """
[default]
protocol = ftp
hostname = example.com
base_folder = /base/folder
file_up_folder = stuff

[ftp]
username = user
password = pass

[scp]
username = scp_user
private_key = ~/.ssh/id_rsa
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)
    monkeypatch.setattr(Path, "expanduser", lambda _: config_file)

    result = fileup.read_config()
    assert isinstance(result, FileupConfig)
    assert result.protocol == "ftp"
    assert result.hostname == "example.com"
    assert result.base_folder == "/base/folder"
    assert result.file_up_folder == "stuff"
    assert result.username == "user"
    assert result.password == "pass"  # noqa: S105


def test_read_config_scp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test the read_config function with SCP."""
    config_content = """
[default]
protocol = scp
hostname = example.com
base_folder = /base/folder
file_up_folder = stuff

[scp]
username = scp_user
private_key = ~/.ssh/id_rsa
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)
    monkeypatch.setattr(Path, "expanduser", lambda _: config_file)

    result = fileup.read_config()
    assert isinstance(result, FileupConfig)
    assert result.protocol == "scp"
    assert result.username == "scp_user"
    assert result.private_key == "~/.ssh/id_rsa"


def test_invalid_protocol(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test invalid protocol raises ValueError."""
    config_content = """
[default]
protocol = invalid
hostname = example.com
base_folder = /base/folder
file_up_folder = stuff
"""
    config_file = tmp_path / "config.ini"
    config_file.write_text(config_content)
    monkeypatch.setattr(Path, "expanduser", lambda _: config_file)

    with pytest.raises(ValueError, match="Invalid protocol: invalid"):
        fileup.read_config()


class MockUploader(fileup.FileUploader):
    """Mock uploader for testing."""

    def __init__(self) -> None:
        """Initialize with test data."""
        self.files = ["file_delete_on_2000-01-01"]

    def upload_file(
        self,
        local_path: Path,  # noqa: ARG002
        remote_filename: str,
    ) -> None:
        """Mock upload."""
        self.files.append(remote_filename)

    def list_files(self) -> list[str]:
        """Mock list."""
        return self.files

    def delete_file(self, filename: str) -> None:
        """Mock delete."""
        self.files.remove(filename)


def test_remove_old_files() -> None:
    """Test the remove_old_files function."""
    uploader = MockUploader()
    today = datetime.date(2023, 1, 1)
    fileup.remove_old_files(uploader, today)
    assert len(uploader.files) == 0


@pytest.fixture
def mock_config() -> FileupConfig:
    """Create a mock config."""
    return FileupConfig(
        protocol="ftp",
        hostname="example.com",
        base_folder="/base/folder",
        file_up_folder="stuff",
        username="user",
        password="pass",  # noqa: S106
    )


@pytest.fixture
def mock_fileup(
    mocker: pytest_mock.plugin.MockerFixture,
    mock_config: FileupConfig,
) -> ModuleType:
    """Mock the fileup module."""
    mocker.patch("fileup.read_config", return_value=mock_config)
    mocker.patch("fileup.ftplib.FTP", autospec=True)
    mocker.patch("fileup.Path.resolve", return_value="mocked_path")
    mocker.patch("fileup.Path.name", return_value="mocked_file_name")
    mocker.patch("fileup.tempfile.TemporaryFile")
    mocker.patch("fileup.Path.open")
    return fileup


@pytest.fixture
def mock_temp_file(
    mocker: pytest_mock.plugin.MockerFixture,
    tmp_path: Path,
) -> MagicMock:
    """Create a mock temporary file."""
    # Create a real temporary file
    temp_file = tmp_path / "temp_marker"
    temp_file.write_text("")

    # Create a mock file object
    mock_file = MagicMock(spec=io.BytesIO)
    mock_file.name = str(temp_file)

    # Create a mock context manager
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_file
    mock_context.__exit__.return_value = None

    # Patch TemporaryFile to return our mock
    mocker.patch("tempfile.TemporaryFile", return_value=mock_context)
    return mock_file


def test_file_up_ftp(
    mocker: pytest_mock.plugin.MockerFixture,
    tmp_path: Path,
    mock_config: FileupConfig,
    mock_temp_file: MagicMock,  # noqa: ARG001
) -> None:
    """Test the fileup function with FTP."""
    mocker.patch("fileup.read_config", return_value=mock_config)
    mock_ftp = MagicMock()
    mock_ftp.nlst.return_value = []  # No existing files
    mocker.patch("ftplib.FTP", return_value=mock_ftp)

    filename = tmp_path / "test_file.txt"
    filename.write_text("test")

    url = fileup.fileup(filename, time=90, direct=False, img=False)
    assert url == "http://example.com/stuff/test_file.txt"

    # Verify FTP operations
    mock_ftp.storbinary.assert_called()

    # Test other URL formats
    url = fileup.fileup(filename, time=90, direct=True, img=False)
    assert url == "http://example.com/stuff/test_file.txt"

    url = fileup.fileup(filename, time=90, direct=False, img=True)
    assert url == "![](http://example.com/stuff/test_file.txt)"


def test_file_up_scp(
    mocker: pytest_mock.plugin.MockerFixture,
    tmp_path: Path,
    mock_config: FileupConfig,
    mock_temp_file: MagicMock,  # noqa: ARG001
) -> None:
    """Test the fileup function with SCP."""
    mock_config.protocol = "scp"
    mocker.patch("fileup.read_config", return_value=mock_config)
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.stdout = ""  # Empty file list

    filename = tmp_path / "test_file.txt"
    filename.write_text("test")

    url = fileup.fileup(filename, time=90, direct=False, img=False)
    assert url == "http://example.com/stuff/test_file.txt"

    # Verify SCP operations
    assert mock_run.call_count >= 1

    # Test direct URL
    url = fileup.fileup(filename, time=90, direct=True, img=False)
    assert url == "http://example.com/stuff/test_file.txt"


def test_main(
    mock_fileup: MagicMock,
    mocker: pytest_mock.plugin.MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test the main function."""
    test_args = ["test_file.txt", "-t", "90"]
    monkeypatch.setattr("sys.argv", ["fileup", *test_args])
    mocker.patch(
        "fileup.fileup",
        return_value="http://example.com/stuff/mocked_file_name",
    )
    mock_fileup.main()
    captured = capsys.readouterr()
    assert (
        captured.out.strip() == "Your url is: http://example.com/stuff/mocked_file_name"
    )
