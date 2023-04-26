"""fileup - Effortless File Sharing for Command-Line Enthusiasts.

This module provides a command-line tool for easily sharing files.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import ftplib
import re
import subprocess
import tempfile
from pathlib import Path


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


def read_config() -> tuple[str, str, str, str, str]:
    """Read the config."""
    config_path = Path("~/.config/fileup/config").expanduser()
    with config_path.open() as f:
        base_url, base_folder, folder, user, pw = (s.strip() for s in f.readlines())
    return base_url, base_folder, folder, user, pw


def remove_old_files(ftp: ftplib.FTP, today: datetime.date) -> None:
    """Remove all files that are past the limit."""
    files = [f for f in ftp.nlst() if "_delete_on_" in f]
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
                ftp.delete(file_name)
            except Exception as e:  # noqa: BLE001
                print(f"Error: {e}")
            ftp.delete(file_name + "_delete_on_" + date)


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

    base_url, base_folder, folder, user, pw = read_config()

    # Connect to server
    ftp = ftplib.FTP(base_url, user, pw)  # noqa: S321
    ftp.cwd(str(Path(base_folder) / folder))

    # Fix the filename to avoid filename character issues
    filename_base = get_valid_filename(filename_base)

    today = datetime.datetime.now(datetime.timezone.utc).date()
    remove_old_files(ftp, today)
    # Delete first if file already exists, it could happen that there is
    # already a file with a specified deletion date, these should be removed.
    for f in ftp.nlst():
        if f.startswith(filename_base) and "_delete_on_" in f:
            ftp.delete(f)

    if time != 0:  # could be negative, meaning it should be deleted now
        remove_on = today + datetime.timedelta(days=time)
        filename_date = filename_base + "_delete_on_" + str(remove_on)
        with tempfile.TemporaryFile() as tmp_file:
            print("upload " + filename_date)
            ftp.storbinary(f"STOR {filename_date}", tmp_file)

    # Upload and open the actual file
    with path.open("rb") as file:
        ftp.storbinary(f"STOR {filename_base}", file)
        print("upload " + filename_base)
        ftp.quit()

    # Create URL
    url = (
        f"{base_url}/{folder}/{filename_base}"
        if folder
        else f"{base_url}/{filename_base}"
    )

    if direct:
        # Returns the url as is.
        url = "http://" + url
    elif img:
        url = f"![](http://{url})"
    elif path.suffix == ".ipynb":
        # Return the url in the nbviewer
        url = "http://nbviewer.jupyter.org/url/" + url + "?flush_cache=true"
    else:
        url = "http://" + url
    return url


DESCRIPTION = [
    "Publish a file. \n \n",
    "Create a config file at ~/.config/fileup/config with the following information and structure:\n",
    "example.com",
    "base_folder",
    "file_up_folder",
    "my_user_name",
    "my_difficult_password",
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
            "pbcopy",
            env={"LANG": "en_US.UTF-8"},
            stdin=subprocess.PIPE,
        )
        process.communicate(url.encode("utf-8"))

    print("Your url is: ", url)


if __name__ == "__main__":
    main()
