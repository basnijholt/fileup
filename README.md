# :rocket: fileup - Effortless File Sharing for Command-Line Enthusiasts :rocket:

[![PyPI](https://img.shields.io/pypi/v/fileup.svg)](https://pypi.python.org/pypi/fileup)
[![Build Status](https://github.com/basnijholt/fileup/actions/workflows/pytest.yml/badge.svg)](https://github.com/basnijholt/fileup/actions/workflows/pytest.yml)
[![CodeCov](https://codecov.io/gh/basnijholt/fileup/branch/main/graph/badge.svg)](https://codecov.io/gh/basnijholt/fileup)

`fileup` is your go-to Python package for hassle-free uploading and sharing of files right from your command-line interface! 🖥️
You can set a time limit after which the file will be automatically removed, ensuring the security of your data. 🕒

> [!TIP]
> Just call `fu myfile.txt` to upload it and get the URL in your clipboard!

## :books: Table of Contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [✨ Features](#-features)
- [:package: Installation](#package-installation)
- [:memo: Configuration](#memo-configuration)
  - [FTP Configuration](#ftp-configuration)
  - [SCP Configuration](#scp-configuration)
- [:video_game: Usage](#video_game-usage)
  - [Special Features](#special-features)
- [:green_apple: macOS Integration](#green_apple-macos-integration)
- [:warning: Limitations](#warning-limitations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## ✨ Features

- 📤 Upload via FTP or SCP (using SSH config)
- ⏰ Automatic file expiration and cleanup
- 🔗 Smart URLs: Jupyter notebooks → nbviewer, image markdown, direct links
- 📋 Automatic clipboard copy (macOS)
- ⚡ Simple config using `~/.config/fileup/config.ini`
- 🔐 Supports SSH keys and password authentication
- 🪶 Zero dependencies - uses Python standard library
- 📜 Works as a single script or installed package
- 🐍 Supports Python ≥3.7

## :package: Installation

To install `fileup`, simply run the following command:

```bash
pip install -U fileup
```
or use `uv` or `pipx`:
```bash
uv tool install fileup
pipx install fileup
```

## :memo: Configuration

Before you can start sharing your files, you'll need to create a configuration file at `~/.config/fileup/config.ini` with the following structure:

```ini
# ~/.config/fileup/config.ini
[default]
protocol = ftp  # or scp
hostname = example.com  # or the Host from your ~/.ssh/config
base_folder = /path/to/files  # where files are stored on the server
file_up_folder =  # subdirectory in URL, can be empty
url = files.example.com  # the actual URL where files are accessible

[ftp]
username = my_user_name
password = my_difficult_password

[scp]
# If empty, will use your SSH config
username =
# If using SSH config, no need for these
private_key =
password =

```

### FTP Configuration
For FTP uploads, you need to provide both `username` and `password` in the `[ftp]` section.

### SCP Configuration
For SCP uploads, you have two options:
1. Use your SSH config by setting `protocol = scp` and using a hostname from your `~/.ssh/config`
2. Explicitly configure SCP by providing `username` and optionally `private_key` in the `[scp]` section

## :video_game: Usage

For a list of available commands, type `fu -h`.

In a nutshell, you can use `fileup` by running:
```bash
fu filename
```

The command supports several options:
- `-t DAYS`, `--time DAYS`: Set an expiration time in days (default: 90, use 0 for no expiration)
- `-d`, `--direct`: Return a direct URL without any prefixes
- `-i`, `--img`: Return the URL formatted for markdown image embedding

This is the output of `fu -h`:
<!-- CODE:BASH:START -->
<!-- echo '```bash' -->
<!-- fu -h -->
<!-- echo '```' -->
<!-- CODE:END -->
<!-- OUTPUT:START -->
<!-- ⚠️ This content is auto-generated by `markdown-code-runner`. -->
```bash
usage: fu [-h] [-t TIME] [-d] [-i] filename

Publish a file.

Create a config file at ~/.config/fileup/config.ini with the following structure:

[default]
protocol = ftp  # or scp
hostname = example.com  # or the Host from your ~/.ssh/config
base_folder = /path/to/files  # where files are stored on the server
file_up_folder =  # subdirectory in URL, can be empty
url = files.example.com  # the actual URL where files are accessible

[ftp]
username = my_user_name
password = my_difficult_password

[scp]
# If empty, will use your SSH config
username =
# If using SSH config, no need for these
private_key =
password =

positional arguments:
  filename

options:
  -h, --help            show this help message and exit
  -t TIME, --time TIME  If time is 0 the file will never be deleted, default is 90 days.
  -d, --direct
  -i, --img
```

<!-- OUTPUT:END -->

### Special Features

- **Jupyter Notebooks**: If you're uploading a Jupyter notebook (`.ipynb`), the returned URL will be accessible via [nbviewer.jupyter.org](http://nbviewer.jupyter.org)
- **Automatic Deletion**: Files with expiration times are automatically removed when their time is up
- **URL Copying**: On macOS, the URL is automatically copied to your clipboard

## :green_apple: macOS Integration

`fileup` currently supports the `pbcopy` command, so the URL will be automatically copied to your clipboard on macOS systems. 📋✨

## :warning: Limitations

- The automatic clipboard copying feature is only available for macOS users
- FTP passwords are stored in plain text; use with caution
- SCP implementation requires the `ssh` and `scp` commands to be available

* * *

Give `fileup` a try today and experience the convenience of effortless file sharing right from your command-line! 🎉
