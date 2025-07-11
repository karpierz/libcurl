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

"""
Performs an FTP upload and renames the file just after a successful
transfer.
"""

import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curl_utils import *  # noqa

here = Path(__file__).resolve().parent

LOCAL_FILE = here/"input/uploadthis.txt"

UPLOAD_FILE_AS = "while-uploading.txt"
RENAME_FILE_TO = "renamed-and-fine.txt"


# NOTE: if you want this example to work on Windows with libcurl as a DLL,
# you MUST also provide a read callback with CURLOPT_READFUNCTION. Failing to
# do so might give you a crash since a DLL may not use the variable's memory
# when passed in to it from an app like this. */
@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    nread = lcurl.read_from_file(buffer, size, nitems, stream)
    print("*** We read %d bytes from file" % nread, file=sys.stderr)
    return nread


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "ftp://example.com/"

    RNFR_cmd: str = "RNFR " + UPLOAD_FILE_AS
    RNTO_cmd: str = "RNTO " + RENAME_FILE_TO

    # open file to upload
    try:
        fd_src = LOCAL_FILE.open("rb")
    except OSError as exc:
        print("Couldn't open '%s': %s" % (LOCAL_FILE, exc.strerror))
        return 2  # cannot continue

    # get the file size
    try:
        fsize: int = file_size(fd_src)
    except OSError as exc:
        print("Couldn't open '%s': %s" % (LOCAL_FILE, exc.strerror))
        fd_src.close()
        return 1  # cannot continue

    print("Local file size: %d bytes." % fsize)

    # In Windows, this inits the Winsock stuff
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with fd_src, curl_guard(True, curl) as guard:
        if not curl: return 1

        # build a list of FTP commands to pass to libcurl
        headerlist = ct.POINTER(lcurl.slist)()
        headerlist = lcurl.slist_append(headerlist, RNFR_cmd.encode("utf-8"))
        headerlist = lcurl.slist_append(headerlist, RNTO_cmd.encode("utf-8"))

        # upload to this place
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, (url + UPLOAD_FILE_AS).encode("utf-8"))
        # tell it to "upload" to the URL
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # we want to use our own read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        # pass in that last of FTP commands to run after the transfer
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTQUOTE, headerlist)
        # now specify which file to upload
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, id(fd_src))
        # Set the size of the file to upload (optional).  If you give a *_LARGE
        # option you MUST make sure that the type of the passed-in argument is a
        # curl_off_t. If you use CURLOPT_INFILESIZE (without _LARGE) you must
        # make sure that to pass in a type 'long' argument.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, fsize)
        # enable verbose for easier tracing
        #lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

        # clean up the FTP commands list
        lcurl.slist_free_all(headerlist)

    return int(res)


if __name__ == "__main__":
    sys.exit(main())
