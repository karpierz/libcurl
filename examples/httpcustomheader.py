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
HTTP request with custom modified, removed and added headers
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "localhost"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        chunk = ct.POINTER(lcurl.slist)()
        # Remove a header curl would otherwise add by itself
        chunk = lcurl.slist_append(chunk, b"Accept:")
        # Add a custom header
        chunk = lcurl.slist_append(chunk, b"Another: yes")
        # Modify a header curl otherwise adds differently
        chunk = lcurl.slist_append(chunk, b"Host: example.com")
        # Add a header with "blank" contents to the right of the colon.
        # Note that we are then using a semicolon in the string we pass to curl!
        chunk = lcurl.slist_append(chunk, b"X-silly-header;")
        # set our custom set of headers
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, chunk)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    # free the custom headers
    lcurl.slist_free_all(chunk)

    return 0


sys.exit(main())
