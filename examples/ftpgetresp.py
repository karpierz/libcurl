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
Similar to ftpget.c but also stores the received response-lines
in a separate file using our own callback!
"""

import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curl_utils import *  # noqa

here = Path(__file__).resolve().parent

FTP_HEADERS = here/"output/ftp-responses"
FTP_BODY    = here/"output/ftp-list"


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "ftp://ftp.gnu.org/gnu/binutils/"

    try:
        # local filename to store the file and
        resp_file = FTP_HEADERS.open("wb")
    except:
        return 1
    try:
        # local filename to store the FTP server's response lines in
        # (b is binary, needed on Windows)
        ftp_file = FTP_BODY.open("wb")
    except:
        return 1

    with resp_file, ftp_file:

        curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

        with curl_guard(False, curl) as guard:
            if not curl: return 1

            # Get a file listing from sunet
            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, lcurl.write_to_file)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, id(resp_file))
            # If you intend to use this on Windows with a libcurl DLL, you must use
            # CURLOPT_WRITEFUNCTION as well
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_to_file)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(ftp_file))

            # Perform the custom request
            res: int = lcurl.easy_perform(curl)

            # Check for errors
            handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
