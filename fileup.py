"""fileup - Effortless File Sharing for Command-Line Enthusiasts.

This module provides a command-line tool for easily sharing files.
"""

from __future__ import annotations

import abc
import argparse
import configparser
import contextlib
import datetime
import ftplib
import io
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class FileUploader(abc.ABC):
    """Base class for file uploading."""

    def __init__(self, config: FileupConfig) -> None:
        """Initialize the uploader."""
        self.config = config

    @abc.abstractmethod
    def upload_file(self, local_path: Path, remote_filename: str) -> None:
        """Upload a file to the remote server."""

    @abc.abstractmethod
    def list_files(self) -> list[str]:
        """List files in the remote directory."""

    @abc.abstractmethod
    def delete_file(self, filename: str) -> None:
        """Delete a file from the remote server."""

    def cleanup(self) -> None:  # noqa: B027
        """Cleanup resources."""


class FTPUploader(FileUploader):
    """FTP implementation of FileUploader."""

    def __init__(self, config: FileupConfig) -> None:
        """Initialize the FTP uploader."""
        super().__init__(config)
        if not (config.username and config.password):
            msg = "FTP requires username and password"
            raise ValueError(msg)

        self.ftp = ftplib.FTP(  # noqa: S321
            config.hostname,
            config.username,
            config.password,
        )
        self.ftp.cwd(str(Path(config.base_folder) / config.file_up_folder))

    def upload_file(self, local_path: Path, remote_filename: str) -> None:
        """Upload a file using FTP."""
        if not local_path.exists():
            # For marker files, create an empty file
            self.ftp.storbinary(f"STOR {remote_filename}", io.BytesIO())
        else:
            with local_path.open("rb") as file:
                self.ftp.storbinary(f"STOR {remote_filename}", file)

    def list_files(self) -> list[str]:
        """List files using FTP."""
        return self.ftp.nlst()

    def delete_file(self, filename: str) -> None:
        """Delete a file using FTP."""
        self.ftp.delete(filename)

    def cleanup(self) -> None:
        """Close the FTP connection."""
        self.ftp.quit()


class SCPUploader(FileUploader):
    """SCP implementation of FileUploader."""

    def upload_file(self, local_path: Path, remote_filename: str) -> None:
        """Upload a file using SCP."""
        remote_path = (
            Path(self.config.base_folder) / self.config.file_up_folder / remote_filename
        )

        # Use hostname directly, which can be from SSH config
        host_str = (
            f"{self.config.username}@{self.config.hostname}"
            if self.config.username
            else self.config.hostname
        )

        cmd = ["scp", "-q"]  # quiet mode

        # Add private key if specified
        if self.config.private_key:
            cmd.extend(["-i", self.config.private_key])

        cmd.extend([str(local_path), f"{host_str}:{remote_path}"])

        subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603

    def list_files(self) -> list[str]:
        """List files using SSH."""
        remote_path = Path(self.config.base_folder) / self.config.file_up_folder

        host_str = (
            f"{self.config.username}@{self.config.hostname}"
            if self.config.username
            else self.config.hostname
        )

        cmd = ["ssh"]

        # Add private key if specified
        if self.config.private_key:
            cmd.extend(["-i", self.config.private_key])

        cmd.extend([host_str, f"ls -1 {remote_path}"])

        result = subprocess.run(  # noqa: S603
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.splitlines()

    def delete_file(self, filename: str) -> None:
        """Delete a file using SSH."""
        remote_path = (
            Path(self.config.base_folder) / self.config.file_up_folder / filename
        )

        host_str = (
            f"{self.config.username}@{self.config.hostname}"
            if self.config.username
            else self.config.hostname
        )

        cmd = ["ssh"]

        # Add private key if specified
        if self.config.private_key:
            cmd.extend(["-i", self.config.private_key])

        cmd.extend([host_str, f"rm {remote_path}"])

        subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603


def get_valid_filename(s: str) -> str:
    """Normalize string to make it a valid filename.

    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'.
    """
    s = s.strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", s)


@dataclass
class FileupConfig:
    """Configuration for fileup."""

    protocol: str
    hostname: str  # SSH hostname or FTP server
    base_folder: str
    file_up_folder: str  # This is what we use in the URL
    url: str  # The actual URL where files will be accessible
    username: str | None = None
    password: str | None = None
    private_key: str | None = None


def read_config() -> FileupConfig:
    """Read the config file."""
    config = configparser.ConfigParser()
    config_path = Path("~/.config/fileup/config.ini").expanduser()
    if not config_path.exists():
        msg = (
            f"Config file not found at {config_path}. "
            "Please create one following the documentation."
        )
        raise FileNotFoundError(msg)

    config.read(config_path)
    protocol = config["default"]["protocol"]
    if protocol not in {"ftp", "scp"}:
        msg = f"Invalid protocol: {protocol}"
        raise ValueError(msg)

    # Get protocol specific settings
    username = config.get(protocol, "username", fallback=None)
    password = config.get(protocol, "password", fallback=None)
    private_key = config.get(protocol, "private_key", fallback=None)
    url = config.get("default", "url", fallback=config["default"]["hostname"])

    return FileupConfig(
        protocol=protocol,
        hostname=config["default"]["hostname"],
        base_folder=config["default"].get("base_folder", ""),
        file_up_folder=config["default"].get("file_up_folder", ""),
        url=url,
        username=username,
        password=password,
        private_key=private_key,
    )


def remove_old_files(uploader: FileUploader, today: datetime.date) -> None:
    """Remove all files that are past the limit."""
    files = [f for f in uploader.list_files() if "_delete_on_" in f]
    file_dates = [f.rsplit("_delete_on_", 1) for f in files]
    for file_name, date in file_dates:
        rm_date = (
            datetime.datetime.strptime(date, "%Y-%m-%d")
            .replace(tzinfo=datetime.timezone.utc)
            .date()
        )
        if rm_date < today:
            print(f'removing "{file_name}" because the date passed')
            try:
                uploader.delete_file(file_name)
            except Exception as e:  # noqa: BLE001
                print(f"Error: {e}")
            uploader.delete_file(file_name + "_delete_on_" + date)


def fileup(
    filename: str | Path,
    *,
    time: float = 90.0,
    direct: bool = False,
    img: bool = False,
) -> str:
    """Upload a file to a server and return the url."""
    path = Path(filename).resolve()
    filename_base = path.name
    config = read_config()

    # Fix the filename to avoid filename character issues
    filename_base = get_valid_filename(filename_base)

    # Create the appropriate uploader
    if config.protocol == "ftp":
        uploader: FileUploader = FTPUploader(config)
    elif config.protocol == "scp":
        uploader = SCPUploader(config)
    else:
        msg = f"Unsupported protocol: {config.protocol}"
        raise ValueError(msg)

    try:
        today = datetime.datetime.now(datetime.timezone.utc).date()
        remove_old_files(uploader, today)

        # Delete first if file already exists
        for f in uploader.list_files():
            if f.startswith(filename_base) and "_delete_on_" in f:
                uploader.delete_file(f)

        if time != 0:  # could be negative, meaning it should be deleted now
            remove_on = today + datetime.timedelta(days=time)
            filename_date = filename_base + "_delete_on_" + str(remove_on)
            # Create empty marker file for deletion date
            with tempfile.NamedTemporaryFile() as tmp_file:
                print("upload " + filename_date)
                uploader.upload_file(Path(tmp_file.name), filename_date)

        # Upload the actual file
        print("upload " + filename_base)
        uploader.upload_file(path, filename_base)

        # Create URL using file_up_folder instead of folder
        url = (
            f"{config.url}/{config.file_up_folder}/{filename_base}"
            if config.file_up_folder
            else f"{config.url}/{filename_base}"
        )

        if direct:
            url = "http://" + url
        elif img:
            url = f"![](http://{url})"
        elif path.suffix == ".ipynb":
            url = "http://nbviewer.jupyter.org/url/" + url + "?flush_cache=true"
        else:
            url = "http://" + url

        return url
    finally:
        uploader.cleanup()


DESCRIPTION = [
    "Publish a file.\n\n",
    "Create a config file at ~/.config/fileup/config.ini with the following structure:\n",
    "[default]",
    "protocol = ftp  # or scp",
    "hostname = example.com  # or the Host from your ~/.ssh/config",
    "base_folder = /path/to/files  # where files are stored on the server",
    "file_up_folder =  # subdirectory in URL, can be empty",
    "url = files.example.com  # the actual URL where files are accessible",
    "",
    "[ftp]",
    "username = my_user_name",
    "password = my_difficult_password",
    "",
    "[scp]",
    "# If empty, will use your SSH config",
    "username =",
    "# If using SSH config, no need for these",
    "private_key =",
    "password =",
]


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="\n".join(DESCRIPTION),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("filename", type=str)
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=90,
        help="If time is 0 the file will never be deleted, default is 90 days.",
    )
    parser.add_argument("-d", "--direct", action="store_true")
    parser.add_argument("-i", "--img", action="store_true")
    args = parser.parse_args()

    url = fileup(args.filename, time=args.time, direct=args.direct, img=args.img)

    # Put a URL into clipboard only works on OS X
    with contextlib.suppress(Exception):
        process = subprocess.Popen(
            "pbcopy",  # noqa: S607
            env={"LANG": "en_US.UTF-8"},
            stdin=subprocess.PIPE,
        )
        process.communicate(url.encode("utf-8"))

    print("Your url is:", url)


if __name__ == "__main__":
    main()
