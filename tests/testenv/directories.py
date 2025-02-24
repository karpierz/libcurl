# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Daniel Stenberg, <daniel@haxx.se>, et al.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at https://curl.se/docs/copyright.html.
#
# You may opt to use, copy, modify, merge, publish, distribute and/or sell
# copies of the Software, and permit persons to whom the Software is
# furnished to do so, under the terms of the COPYING file.
#
# This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
# KIND, either express or implied.
#
# SPDX-License-Identifier: curl
#
# **************************************************************************

from typing import Optional, Tuple, List, Dict

__all__ = ('ftp_contentlist', 'wildcard_filesize', 'wildcard_getfile')


file_chmod1 = {
    "name":    "chmod1",
    "content": "This file should have permissions 444\n",
    "perm":    "r--r--r--",
    "time":    "Jan 11 10:00",
    "dostime": "01-11-10  10:00AM",
}

file_chmod2 = {
    "name":    "chmod2",
    "content": "This file should have permissions 666\n",
    "perm":    "rw-rw-rw-",
    "time":    "Feb  1  8:00",
    "dostime": "02-01-10  08:00AM",
}

file_chmod3 = {
    "name":    "chmod3",
    "content": "This file should have permissions 777\n",
    "perm":    "rwxrwxrwx",
    "time":    "Feb  1  8:00",
    "dostime": "02-01-10  08:00AM",
}

file_chmod4 = {
    "type":    "d",
    "name":    "chmod4",
    "content": "This file should have permissions 001\n",
    "perm":    "--S--S--t",
    "time":    "May  4  4:31",
    "dostime": "05-04-10  04:31AM",
}

file_chmod5 = {
    "type":    "d",
    "name":    "chmod5",
    "content": "This file should have permissions 110\n",
    "perm":    "--s--s--T",
    "time":    "May  4  4:31",
    "dostime": "05-04-10  04:31AM",
}

link_link = {
    "type":    "l",
    "name":    "link -> file.txt",
    "size":    8,
    "perm":    "rwxrwxrwx",
    "time":    "Jan  6  4:42",
}

link_link_absolute = {
    "type":    "l",
    "name":    "link_absolute -> /data/ftp/file.txt",
    "size":    15,
    "perm":    "rwxrwxrwx",
    "time":    "Jan  6  4:45",
}

dir_dot = {
    "type":    "d",
    "name":    ".",
    "hlink":   "4",
    "time":    "Apr 27  5:12",
    "size":    20480,
    "dostime": "04-27-10  05:12AM",
    "perm":    "rwxrwxrwx",
}

dir_ddot = {
    "type":    "d",
    "name":    "..",
    "hlink":   "4",
    "size":    20480,
    "time":    "Apr 23  3:12",
    "dostime": "04-23-10  03:12AM",
    "perm":    "rwxrwxrwx",
}

dir_weirddir_txt = {
    "type":    "d",
    "name":    "weirddir.txt",
    "hlink":   "2",
    "size":    4096,
    "time":    "Apr 23  3:12",
    "dostime": "04-23-10  03:12AM",
    "perm":    "rwxr-xrwx",
}

dir_UNIX = {
    "type":    "d",
    "name":    "UNIX",
    "hlink":   "11",
    "size":    4096,
    "time":    "Nov 01  2008",
    "dostime": "11-01-08  11:11AM",
    "perm":    "rwx--x--x",
}

dir_DOS = {
    "type":    "d",
    "name":    "DOS",
    "hlink":   "11",
    "size":    4096,
    "time":    "Nov 01  2008",
    "dostime": "11-01-08  11:11AM",
    "perm":    "rwx--x--x",
}

dir_dot_NeXT = {
    "type":    "d",
    "name":    ".NeXT",
    "hlink":   "4",
    "size":    4096,
    "time":    "Jan 23  2:05",
    "dostime": "01-23-05  02:05AM",
    "perm":    "rwxrwxrwx",
}

file_empty_file_dat = {
    "name":    "empty_file.dat",
    "content": "",
    "perm":    "rw-r--r--",
    "time":    "Apr 27 11:01",
    "dostime": "04-27-10  11:01AM",
}

file_file_txt = {
    "name":    "file.txt",
    "content": 'This is content of file "file.txt"\n',
    "time":    "Apr 27 11:01",
    "dostime": "04-27-10  11:01AM",
    "perm":    "rw-r--r--",
}

file_someothertext_txt = {
    "name":    "someothertext.txt",
    "content": "Some junk ;-) This file does not really exist.\n",
    "time":    "Apr 27 11:01",
    "dostime": "04-27-10  11:01AM",
    "perm":    "rw-r--r--",
}

lists = {
    "/fully_simulated/": {
        "type":  "unix",
        "files": [dir_dot, dir_ddot, dir_DOS, dir_UNIX],
        "eol":   "\r\n",
    },
    "/fully_simulated/UNIX/": {
        "type":  "unix",
        "files": [dir_dot, dir_ddot,
                  file_chmod1, file_chmod2, file_chmod3, file_chmod4, file_chmod5,
                  file_empty_file_dat, file_file_txt,
                  link_link, link_link_absolute, dir_dot_NeXT,
                  file_someothertext_txt, dir_weirddir_txt],
        "eol":   "\r\n",
    },
    "/fully_simulated/DOS/": {
        "type":  "dos",
        "files": [dir_dot, dir_ddot,
                  file_chmod1, file_chmod2, file_chmod3, file_chmod4, file_chmod5,
                  file_empty_file_dat, file_file_txt,
                  dir_dot_NeXT, file_someothertext_txt, dir_weirddir_txt],
        "eol":   "\r\n",
    }
}

def wildcard_filesize(list_type: str, fname: str) -> int:
    return wildcard_getfile(list_type, fname)[0]


def wildcard_getfile(list_type: str, fname: str) -> Tuple[int, str]:
    global lists
    for file in lists.get(list_type, {}).get("files", []):
        if file["name"] == fname:
            if "content" in file:
                return (len(file["content"]), file["content"])
            elif "type" not in file or file["type"] != "d":
                return (0, "")
            else:
                return (-1, 0)
    return (-1, 0)


def ftp_contentlist(list_type: str) -> Optional[List]:
    global lists
    return _ftp_createcontent(lists.get(list_type, {}))


def _ftp_createcontent(files_set: Dict) -> Optional[List]:

    type  = files_set.get("type")
    fdefs = files_set.get("files", [])
    eol   = files_set["eol"]

    content_list = []
    if type == "unix":
        for file in fdefs:
            ftype  = file.get("type") or "-"
            fname  = file["name"]
            fperm  = file.get("perm") or "rwxr-xr-x"
            fuser  = ("%15s" % file["user"])  if file.get("user")  else "ftp-default"
            fgroup = ("%15s" % file["group"]) if file.get("group") else "ftp-default"
            if "type" in file and file["type"] == "d":
                fsize = "%7d" % file.get("size", 4096)
            else:
                fsize = "%7d" % len(file.get("content", ""))
            fhlink = ("%4d" %  file["hlink"]) if file.get("hlink") else "   1"
            ftime  = ("%10s" % file["time"])  if file.get("time")  else "Jan 9  1933"
            content_list.append(f"{ftype}{fperm} {fhlink} {fuser} {fgroup} {fsize} {ftime} {fname}{eol}")
        return content_list
    elif type == "dos":
        for file in fdefs:
            fname = file["name"]
            ftime = file.get("dostime") or "06-25-97  09:12AM"
            if "type" in file and file["type"] == "d":
                size_or_dir = "      <DIR>         "
            else:
                size_or_dir = "%20d" % len(file.get("content", ""))
            content_list.append(f"{ftime} {size_or_dir} {fname}{eol}")
        return content_list
    else:
        return None
