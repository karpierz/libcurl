#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 1998 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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
#***************************************************************************

"""
Gets a file using an SFTP URL.
"""

from dataclasses import dataclass
import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa

here = Path(__file__).resolve().parent


OUT_FILE = here/"output/yourfile.bin"


# define this to switch off the use of ssh-agent in this program
# DISABLE_SSH_AGENT = 1


# This is an example showing how to get a single file from an SFTP server.
# It delays the actual destination file creation until the first write
# callback so that it will not create an empty file in case the remote file
# does not exist or something else fails.


@dataclass
class FtpFile:
    filename:  Path = None
    outstream: object = None


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    ftpfile = lcurl.from_oid(stream)

    if not ftpfile.outstream:
        # open file for writing
        try:
            ftpfile.outstream = ftpfile.filename.open("wb")
        except:
            ftpfile.outstream = None
            return -1  # failure, cannot open file to write

    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = ftpfile.outstream.write(bwritten)
    return nwritten


def main(argv=sys.argv[1:]):

    # You better replace the URL with one that works!
    url: str = (argv[0] if len(argv) >= 1 else
                "sftp://user@server/home/user/file.txt")

    global OUT_FILE

    ftpfile = FtpFile(OUT_FILE)  # name to store the file

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # Define our callback to get called when there's data to be written
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        # Set a pointer to our struct to pass to the callback
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(ftpfile))
        if not defined("DISABLE_SSH_AGENT"):
            # We activate ssh agent. For this to work you need
            # to have ssh-agent running (type set | grep SSH_AGENT to check)
            # or pageant on Windows (there is an icon in systray if so)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSH_AUTH_TYPES,
                                    lcurl.CURLSSH_AUTH_AGENT);
        # enable progress meter, set to 1 to disable it
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        # Switch on full protocol/debug output
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            # we failed
            handle_easy_perform_error(res)

        # Close the local file
        if ftpfile.outstream:
            ftpfile.outstream.close()

    return 0


sys.exit(main())
