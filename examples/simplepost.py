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
Very simple HTTP POST
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://example.com"

    post_this = b"moo mooo moo moo"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, post_this)
        # if we do not provide POSTFIELDSIZE, libcurl will strlen() by itself
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, len(post_this))

        # Perform the request, res will get the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
