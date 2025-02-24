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
Checks a single file's size and mtime from an FTP server.
"""

import sys
import ctypes as ct
import time

import libcurl as lcurl
from curl_utils import *  # noqa


def main(argv=sys.argv[1:]):

    ftpurl: str = (argv[0] if len(argv) >= 1 else
                   "ftp://ftp.gnu.org/gnu/binutils/binutils-2.19.1.tar.bz2")
    filename = ftpurl.rpartition("/")[2]

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, ftpurl.encode("utf-8"))
        # No download if the file
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOBODY, 1)
        # Ask for filetime
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FILETIME, 1)
        # we are not interested in the headers itself
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, lcurl.write_skipped)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER, 0)
        # Switch on full protocol/debug output
        # lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)
        if res != lcurl.CURLE_OK:
            raise guard.Break

        # https://curl.se/libcurl/c/curl_easy_getinfo.html

        filetime = ct.c_long(-1)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_FILETIME,
                                 ct.byref(filetime))
        filetime = filetime.value
        if res == lcurl.CURLE_OK and filetime >= 0:
            print("filetime %s: %s" % (filename, time.ctime(filetime)))

        filesize = lcurl.off_t(0)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_CONTENT_LENGTH_DOWNLOAD_T,
                                 ct.byref(filesize))
        filesize = filesize.value
        if res == lcurl.CURLE_OK and filesize > 0:
            print("filesize %s: %d bytes" % (filename, filesize))

    return 0


sys.exit(main())
