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


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    share: ct.POINTER(lcurl.CURLSH) = lcurl.share_init()
    lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE,
                              lcurl.CURL_LOCK_DATA_COOKIE)

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_SHARE, share)
        test_setopt(curl, lcurl.CURLOPT_URL, b"http://localhost/")
        test_setopt(curl, lcurl.CURLOPT_PROXY, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        test_setopt(curl, lcurl.CURLOPT_COOKIEFILE, b"")
        # Set a cookie without Max-age or Expires
        test_setopt(curl, lcurl.CURLOPT_COOKIELIST,
                          b"Set-Cookie: c1=v1; domain=localhost")

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)

        # always cleanup
        lcurl.share_cleanup(share)

    return res
