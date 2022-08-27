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
Simple HTTP GET that stores the headers in a separate file
"""

import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa

here = Path(__file__).resolve().parent


HEADER_FILENAME = here/"output/head.out"
BODY_FILENAME   = here/"output/body.out"


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten)
    return nwritten


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://example.com"

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # init the curl session
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with HEADER_FILENAME.open("wb") as headerfile, \
         BODY_FILENAME.open("wb")   as bodyfile,   \
         curl_guard(True, curl):
        if not curl: return 1

        # set URL to get
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # no progress meter please
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        # send all data to this function 
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        # we want the headers be written to this file handle
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, id(headerfile))
        # we want the body be written to this file handle instead of stdout
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(bodyfile))

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
