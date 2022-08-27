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
Re-using handles to do HTTP persistent connections
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://example.com"

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        res: lcurl.CURLcode

        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER,  1)
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

        # get the first document
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # get another document from the same server using the same connection
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL,
                                (url + "/docs/").encode("utf-8"))

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
