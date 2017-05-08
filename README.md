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

If the file is an Jupyter notebook the returned url will be in [nbviewer.jupyter.org](http://nbviewer.jupyter.org).


## Limitations
* Assumes your base folder is in `/public_html/`.
* Uses `pbcopy`, so the url will be copied to your clipboard only on macOS.

Both these things are super easy to fix, please let me know if you run into this problem. I'll fix it if anybody is interested in using this.
