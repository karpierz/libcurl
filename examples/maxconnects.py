# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) James Fuller, <jim@webcomposite.com>, et al.
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
Set maximum number of persistent connections to 1.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


def main(argv=sys.argv[1:]):

    urls: str = argv or [
        "https://example.com",
        "https://curl.se",
        "https://www.example/",
    ]

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        # Change the maximum number of persistent connection
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAXCONNECTS, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # loop over the URLs
        for url in urls:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
            if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
                lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

            # Perform the request, res gets the return code
            res: int = lcurl.easy_perform(curl)

            # Check for errors
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
