#!/usr/bin/env python
# -*-Python-*-

import argparse
import base64
import datetime
import ftplib
import os
import re
import subprocess
import tempfile


def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = s.strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def read_config():
    # Read the config
    with open(os.path.expanduser('~/.config/fileup/config'), 'r') as f:
        """Create a config file at ~/.config/fileup/config with the
        following information and structure:
            example.com
            file_up_folder
            my_user_name
            my_difficult_password
        """
        base_url, base_folder, folder, user, pw = [s.replace('\n', '') for s in f.readlines()]
    return base_url, base_folder, folder, user, pw


def remove_old_files(ftp, today):
    # Remove all files that are past the limit
    files = [f for f in ftp.nlst() if '_delete_on_' in f]
    file_dates = [f.rsplit('_delete_on_', 1) for f in files]
    for file_name, date in file_dates:
        rm_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        if rm_date < today:
            print('removing "{}" because the date passed'.format(file_name))
            try:
                ftp.delete(file_name)
            except:
                # File didn't exist anymore for some reason...
                pass
            ftp.delete(file_name + "_delete_on_" + date)


def main():
    # Get arguments
    description = ["Publish a file. \n \n",
                   "Create a config file at ~/.config/fileup/config with the following information and structure:\n",
                   "example.com",
                   "base_folder",
                   "file_up_folder",
                   "my_user_name",
                   "my_difficult_password"]

    parser = argparse.ArgumentParser(description='\n'.join(description),
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('fname', type=str)
    parser.add_argument('-t', '--time', type=int, default=90)
    parser.add_argument('-d', '--direct', action='store_true')
    parser.add_argument('-i', '--img', action='store_true')
    args = parser.parse_args()
    fname = os.path.abspath(os.path.expanduser(args.fname))

    fname_base = os.path.basename(fname)

    base_url, base_folder, folder, user, pw = read_config()

    # Connect to server
    ftp = ftplib.FTP(base_url, user, pw)
    ftp.cwd(os.path.join(base_folder, folder))

    # Fix the filename to avoid filename character issues
    fname_base = get_valid_filename(fname_base)

    today = datetime.datetime.now().date()
    remove_old_files(ftp, today)

    # Delete first if file already exists, it could happen that there is
    # already a file with a specified deletion date, these should be removed.
    for f in ftp.nlst():
        if f.startswith(fname_base) and '_delete_on_' in f:
            ftp.delete(f)

    if args.time != 0:  # could be negative (used for debugging).
        remove_on = today + datetime.timedelta(days=args.time)
        fname_date = fname_base + '_delete_on_' + str(remove_on)
        with tempfile.TemporaryFile() as f:
            print('upload ' + fname_date)
            ftp.storbinary('STOR {0}'.format(fname_date), f)

    # Upload and open the actual file
    with open(fname, 'rb') as f:
        ftp.storbinary('STOR {0}'.format(fname_base), f)
        print('upload ' + fname_base)
        ftp.quit()

    # Create URL
    if folder:
        url = '{}/{}/{}'.format(base_url, folder, fname_base)
    else:
        url = '{}/{}'.format(base_url, fname_base)

    if args.direct:
        # Returns the url as is.
        url = 'http://' + url
    elif args.img:
        url = '![](http://{})'.format(url)
    elif fname.endswith('.ipynb'):
        # Return the url in the nbviewer
        url = 'http://nbviewer.jupyter.org/url/' + url + '?flush_cache=true'

    # Put a URL into clipboard only works on OS X
    try:
        process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'},
                                   stdin=subprocess.PIPE)
        process.communicate(url.encode('utf-8'))
    except:
        pass

    print('Your url is: ', 'http://' + url)

if __name__ == "__main__":
    main()
