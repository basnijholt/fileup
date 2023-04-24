"""Tests for the ``fileup`` package."""
from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

import fileup

if TYPE_CHECKING:
    from types import ModuleType

    import pytest_mock.plugin


def test_get_valid_filename() -> None:
    """Test the get_valid_filename function."""
    assert (
        fileup.get_valid_filename("john's portrait in 2004.jpg")
        == "johns_portrait_in_2004.jpg"
    )


def test_read_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the read_config function."""
    monkeypatch.setattr(Path, "expanduser", lambda _: Path("test_config"))
    with open("test_config", "w") as f:  # noqa: PTH123
        f.write(
            "example.com\nbase_folder\nfile_up_folder\nmy_user_name\nmy_difficult_password\n",
        )
    result = fileup.read_config()
    os.remove("test_config")  # noqa: PTH107
    assert result == (
        "example.com",
        "base_folder",
        "file_up_folder",
        "my_user_name",
        "my_difficult_password",
    )


def test_remove_old_files() -> None:
    """Test the remove_old_files function."""

    # Mocking the FTP object
    class MockFTP:
        def __init__(self) -> None:
            self.files = ["file_delete_on_2000-01-01"]

        def nlst(self) -> list[str]:
            return self.files

        def delete(self, file: str) -> None:
            self.files.remove(file)

    ftp = MockFTP()
    today = datetime.date(2023, 1, 1)
    fileup.remove_old_files(ftp, today)  # type: ignore[arg-type]
    assert len(ftp.files) == 0


@pytest.fixture()
def mock_fileup(mocker: pytest_mock.plugin.MockerFixture) -> ModuleType:
    """Mock the fileup module."""
    mocker.patch(
        "fileup.read_config",
        return_value=(
            "example.com",
            "base_folder",
            "file_up_folder",
            "my_user_name",
            "my_difficult_password",
        ),
    )
    mocker.patch("fileup.ftplib.FTP", autospec=True)
    mocker.patch("fileup.Path.resolve", return_value="mocked_path")
    mocker.patch("fileup.Path.name", return_value="mocked_file_name")
    mocker.patch("fileup.tempfile.TemporaryFile")
    mocker.patch("fileup.Path.open")
    return fileup


def test_file_up(mocker: pytest_mock.plugin.MockerFixture, tmp_path: Path) -> None:
    """Test the file_up function."""
    # Mock the necessary functions
    mocker.patch(
        "fileup.read_config",
        return_value=(
            "example.com",
            "base_folder",
            "file_up_folder",
            "my_user_name",
            "my_difficult_password",
        ),
    )
    mock_ftp = MagicMock()
    mocker.patch("ftplib.FTP", return_value=mock_ftp)
    filename = tmp_path / "test_file.txt"
    filename.write_text("test")
    # Call the function
    url = fileup.file_up(filename, time=90, direct=False, img=False)
    assert url.startswith("http://example.com/file_up_folder/test_file.txt")

    url = fileup.file_up(filename, time=90, direct=True, img=False)
    assert url.startswith("http://example.com/file_up_folder/test_file.txt")

    url = fileup.file_up(filename, time=90, direct=False, img=True)
    assert url.startswith("![](http://example.com/file_up_folder/test_file.txt)")


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
        "fileup.file_up",
        return_value="http://example.com/file_up_folder/mocked_file_name",
    )
    mock_fileup.main()
    captured = capsys.readouterr()
    assert (
        "Your url is:  http://example.com/file_up_folder/mocked_file_name"
        in captured.out
    )
