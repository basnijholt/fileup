# fileup
Easily upload and share files using your command-line interface. You can specify a time limit after which the file it removed.


## Installation
```
pip install -U https://github.com/basnijholt/fileup/archive/master.zip
```


## Preperations
Create a config file at `~/.config/fileup/config` with the following information and structure:
```
base_url (example: nijholt.biz)
base_folder (example: /domains/nijholt.biz/public_html/)
file_up_folder (example: 'stuff', if fileup needs to put the files in nijholt.biz/stuff)
my_user_name
my_difficult_password
```


## Usage
See `fu -h`.
tl;dr:
```
fu filename
```

If the file is a Jupyter notebook (`*.ipynb`) the returned url will be via [nbviewer.jupyter.org](http://nbviewer.jupyter.org).


## Limitations
* Uses `pbcopy`, so the url will be copied to your clipboard only on macOS.
