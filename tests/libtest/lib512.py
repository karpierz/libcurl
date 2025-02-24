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

import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# Test case code based on source in a bug report filed by James Bursa on
# 28 Apr 2004


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    rc: int = 99
    code: lcurl.CURLcode

    code = lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    if code != lcurl.CURLE_OK:
        rc = 5
    else:
        curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
        if not curl:
            rc = 4
        else:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER,  1)

            curl2: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(curl)
            if not curl2:
                rc = 3
            else:
                code = lcurl.easy_setopt(curl2, lcurl.CURLOPT_URL, URL.encode("utf-8"))
                if code != lcurl.CURLE_OK:
                    rc = 2
                else:
                    code = lcurl.easy_perform(curl2)
                    if code != lcurl.CURLE_OK:
                        rc = 1
                    else:
                        rc = 0

                lcurl.easy_cleanup(curl2)

            lcurl.easy_cleanup(curl)

        lcurl.global_cleanup()

    return lcurl.CURLcode(rc).value
