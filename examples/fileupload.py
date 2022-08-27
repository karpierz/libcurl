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
Upload to a file:// URL
"""

import sys
import os
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa

here = Path(__file__).resolve().parent


LOCAL_FILE  = here/"input/debugit"
UPLOAD_FILE = here/"output/debugit.new"

TARGET_URL = UPLOAD_FILE.as_uri()


# NOTE: if you want this example to work on Windows with libcurl as a
# DLL, you MUST also provide a read callback with CURLOPT_READFUNCTION.
# Failing to do so will give you a crash since a DLL may not use the
# variable's memory when passed in to it from an app like this.
@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    bread = file.read(size * nitems)
    if not bread: return 0
    nread = len(bread)
    ct.memmove(buffer, bread, nread)
    return nread


def main(argv=sys.argv[1:]):

    # open file to upload
    try:
        fd_src = LOCAL_FILE.open("rb")
    except OSError as exc:
        print("Couldn't open '%s': %s" %
              (LOCAL_FILE, os.strerror(exc.errno)))
        return 1  # cannot continue

    # get the file size
    try:
        fsize: int = file_size(fd_src)
    except:
        fd_src.close()
        return 1  # cannot continue

    print("Local file size: %d bytes." % fsize)

    # In windows, this will init the winsock stuff
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with fd_src, curl_guard(True, curl):
        if not curl: return 1

        # upload to this place
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, TARGET_URL.encode("utf-8"))
        # tell it to "upload" to the URL
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # we want to use our own read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        # set where to read from (on Windows you need to use READFUNCTION too)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, id(fd_src))
        # and give the size of the upload (optional)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, fsize)
        # enable verbose for easier tracing
        #lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)
        else:
            # now extract transfer info
            speed_upload = lcurl.off_t()
            total_time   = lcurl.off_t()
            lcurl.easy_getinfo(curl, lcurl.CURLINFO_SPEED_UPLOAD_T, ct.byref(speed_upload))
            lcurl.easy_getinfo(curl, lcurl.CURLINFO_TOTAL_TIME_T,   ct.byref(total_time))
            speed_upload = speed_upload.value
            total_time   = total_time.value

            print("Speed: %u bytes/sec during %u.%06u seconds" %
                  (speed_upload, total_time // 1000000, total_time % 1000000),
                  file=sys.stderr)

    return 0


sys.exit(main())
