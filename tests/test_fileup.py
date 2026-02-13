"""Tests for the ``fileup`` package."""

from __future__ import annotations

import datetime
import io
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

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
url = files.example.com

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
    assert result.url == "files.example.com"
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
url = files.example.com

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
    assert result.url == "files.example.com"
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
url = files.example.com
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
        url="files.example.com",
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
    assert url == "http://files.example.com/stuff/test_file.txt"

    # Verify FTP operations
    mock_ftp.storbinary.assert_called()

    # Test other URL formats
    url = fileup.fileup(filename, time=90, direct=True, img=False)
    assert url == "http://files.example.com/stuff/test_file.txt"

    url = fileup.fileup(filename, time=90, direct=False, img=True)
    assert url == "![](http://files.example.com/stuff/test_file.txt)"


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
    assert url == "http://files.example.com/stuff/test_file.txt"

    # Verify SCP operations
    assert mock_run.call_count >= 1

    # Test direct URL
    url = fileup.fileup(filename, time=90, direct=True, img=False)
    assert url == "http://files.example.com/stuff/test_file.txt"


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
        return_value="http://files.example.com/stuff/mocked_file_name",
    )
    mock_fileup.main()
    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == "Your url is: http://files.example.com/stuff/mocked_file_name"
    )


def test_zero_time_no_deletion(
    mocker: pytest_mock.plugin.MockerFixture,
    tmp_path: Path,
    mock_config: FileupConfig,
    mock_temp_file: MagicMock,  # noqa: ARG001
) -> None:
    """Test that time=0 means no deletion marker."""
    mocker.patch("fileup.read_config", return_value=mock_config)
    mock_ftp = MagicMock()
    mock_ftp.nlst.return_value = []
    mocker.patch("ftplib.FTP", return_value=mock_ftp)

    filename = tmp_path / "test_file.txt"
    filename.write_text("test")
    fileup.fileup(filename, time=0)

    # Verify no deletion marker was created
    delete_marker = [
        call[0][0]
        for call in mock_ftp.storbinary.call_args_list
        if "_delete_on_" in str(call)
    ]
    assert len(delete_marker) == 0


def test_ftp_uploader_invalid_config() -> None:
    """Test FTPUploader with invalid config."""
    config = FileupConfig(
        protocol="ftp",
        hostname="example.com",
        base_folder="/base",
        file_up_folder="files",
        url="example.com",
    )
    with pytest.raises(ValueError, match="FTP requires username and password"):
        fileup.FTPUploader(config)


def test_ftp_uploader_file_not_exists(mock_config: FileupConfig) -> None:
    """Test FTPUploader with non-existent file."""
    mock_ftp = MagicMock()
    with patch("ftplib.FTP", return_value=mock_ftp):
        uploader = fileup.FTPUploader(mock_config)
        uploader.upload_file(Path("nonexistent.txt"), "remote.txt")
        mock_ftp.storbinary.assert_called_once()


def test_fileup_ipynb(
    mocker: pytest_mock.plugin.MockerFixture,
    tmp_path: Path,
    mock_config: FileupConfig,
) -> None:
    """Test fileup with Jupyter notebook."""
    mocker.patch("fileup.read_config", return_value=mock_config)
    mock_ftp = MagicMock()
    mock_ftp.nlst.return_value = []
    mocker.patch("ftplib.FTP", return_value=mock_ftp)

    filename = tmp_path / "test.ipynb"
    filename.write_text("{}")

    url = fileup.fileup(filename, time=90)
    assert "nbviewer.jupyter.org" in url


def test_main_clipboard_error(
    mock_fileup: MagicMock,  # noqa: ARG001
    mocker: pytest_mock.plugin.MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Test main function when clipboard operation fails."""
    test_args = ["test_file.txt"]
    monkeypatch.setattr("sys.argv", ["fileup", *test_args])
    mocker.patch(
        "fileup.fileup",
        return_value="http://example.com/file",
    )
    # Make subprocess.Popen raise an exception
    mocker.patch("subprocess.Popen", side_effect=Exception("Clipboard error"))

    # Should not raise exception
    fileup.main()
    captured = capsys.readouterr()
    assert "Your url is:" in captured.out


def test_unsupported_protocol(
    mocker: pytest_mock.plugin.MockerFixture,
    mock_config: FileupConfig,
) -> None:
    """Test fileup with unsupported protocol."""
    mock_config.protocol = "unsupported"
    mocker.patch("fileup.read_config", return_value=mock_config)

    with pytest.raises(ValueError, match="Unsupported protocol: unsupported"):
        fileup.fileup("test.txt")


def test_scp_uploader_with_username(mock_config: FileupConfig) -> None:
    """Test SCPUploader with username."""
    mock_config.protocol = "scp"
    mock_config.username = "test_user"
    mock_run = MagicMock()
    with patch("subprocess.run", mock_run):
        uploader = fileup.SCPUploader(mock_config)
        uploader.upload_file(Path("test.txt"), "remote.txt")

        # Check if username was used in command
        cmd = mock_run.call_args[0][0]
        assert "test_user@example.com" in cmd[-1]


def test_scp_uploader_with_private_key(mock_config: FileupConfig) -> None:
    """Test SCPUploader with private key."""
    mock_config.protocol = "scp"
    mock_config.private_key = "~/.ssh/id_rsa"
    mock_run = MagicMock()
    with patch("subprocess.run", mock_run):
        uploader = fileup.SCPUploader(mock_config)
        uploader.upload_file(Path("test.txt"), "remote.txt")

        # Check if private key was used in command
        cmd = mock_run.call_args[0][0]
        assert "-i" in cmd
        assert "~/.ssh/id_rsa" in cmd


def test_main_with_all_options(
    mocker: pytest_mock.plugin.MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,  # noqa: ARG001
) -> None:
    """Test main function with all command line options."""
    test_args = ["test_file.txt", "-t", "30", "-d", "-i"]
    monkeypatch.setattr("sys.argv", ["fileup", *test_args])
    mock_fileup = mocker.patch(
        "fileup.fileup",
        return_value="http://example.com/file",
    )

    fileup.main()

    # Verify fileup was called with all options
    mock_fileup.assert_called_once_with(
        "test_file.txt",
        time=30,
        direct=True,
        img=True,
        remote_filename=None,
    )


def test_clipboard_to_temp_file_image(
    mocker: pytest_mock.plugin.MockerFixture,
) -> None:
    """Test clipboard image content gets written to a temporary PNG."""
    mocker.patch("fileup._read_clipboard_image", return_value=b"png-bytes")
    mocker.patch("fileup._read_clipboard_text", return_value=None)

    temp_path, remote_filename = fileup._clipboard_to_temp_file()
    try:
        assert temp_path.exists()
        assert temp_path.suffix == ".png"
        assert temp_path.read_bytes() == b"png-bytes"
        assert remote_filename.startswith("clipboard-")
        assert remote_filename.endswith(".png")
    finally:
        temp_path.unlink(missing_ok=True)


def test_clipboard_to_temp_file_text(
    mocker: pytest_mock.plugin.MockerFixture,
) -> None:
    """Test clipboard text content gets written to a temporary TXT."""
    mocker.patch("fileup._read_clipboard_image", return_value=None)
    mocker.patch("fileup._read_clipboard_text", return_value="hello clipboard")

    temp_path, remote_filename = fileup._clipboard_to_temp_file("note.txt")
    try:
        assert temp_path.exists()
        assert temp_path.suffix == ".txt"
        assert temp_path.read_text(encoding="utf-8") == "hello clipboard"
        assert remote_filename == "note.txt"
    finally:
        temp_path.unlink(missing_ok=True)


def test_clipboard_to_temp_file_no_supported_content(
    mocker: pytest_mock.plugin.MockerFixture,
) -> None:
    """Test clipboard upload fails when no supported content exists."""
    mocker.patch("fileup._read_clipboard_image", return_value=None)
    mocker.patch("fileup._read_clipboard_text", return_value=None)

    with pytest.raises(
        RuntimeError,
        match="Clipboard has no supported image/text content",
    ):
        fileup._clipboard_to_temp_file()


def test_main_clipboard_upload(
    mocker: pytest_mock.plugin.MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test main function uploads clipboard content."""
    temp_file = tmp_path / "clip.png"
    temp_file.write_bytes(b"png")
    monkeypatch.setattr("sys.argv", ["fileup", "--clipboard", "shot.png"])
    mocker.patch("fileup._clipboard_to_temp_file", return_value=(temp_file, "shot.png"))
    mock_upload = mocker.patch(
        "fileup.fileup",
        return_value="http://example.com/shot.png",
    )

    fileup.main()

    mock_upload.assert_called_once_with(
        temp_file,
        time=90,
        direct=False,
        img=False,
        remote_filename="shot.png",
    )
    assert not temp_file.exists()
