
# :rocket: fileup - Effortless File Sharing for Command-Line Enthusiasts :rocket:

`fileup` is your go-to Python package for hassle-free uploading and sharing of files right from your command-line interface! 🖥️🔥 You can set a time limit after which the file will be automatically removed, ensuring the security of your data. 🕒🔒

## :books: Table of Contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [:package: Installation](#package-installation)
- [:memo: Configuration](#memo-configuration)
- [:video_game: Usage](#video_game-usage)
- [:green_apple: macOS Integration](#green_apple-macos-integration)
- [:warning: Limitations](#warning-limitations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## :package: Installation

To install `fileup`, simply run the following command:

```bash
pip install -U https://github.com/basnijholt/fileup/archive/master.zip
```

## :memo: Configuration

Before you can start sharing your files, you'll need to create a configuration file at `~/.config/fileup/config` with the following structure:

```less
base_url (example: nijholt.biz)
base_folder (example: /domains/nijholt.biz/public_html/)
file_up_folder (example: 'stuff', if fileup needs to put the files in nijholt.biz/stuff)
my_user_name
my_difficult_password
```

## :video_game: Usage

For a list of available commands, type `fu -h`.

In a nutshell, you can use `fileup` by running:

```bash
fu filename
```

If you're uploading a Jupyter notebook (`*.ipynb`), the returned URL will be accessible via [nbviewer.jupyter.org](http://nbviewer.jupyter.org).

## :green_apple: macOS Integration

`fileup` currently supports the `pbcopy` command, so the URL will be automatically copied to your clipboard on macOS systems. 📋✨

## :warning: Limitations

Please note that the automatic clipboard copying feature is only available for macOS users at the moment.

* * *

Give `fileup` a try today and experience the convenience of effortless file sharing right from your command-line! 🎉👏
