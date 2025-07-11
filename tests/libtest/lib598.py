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

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        test_setopt(curl, lcurl.CURLOPT_REFERER, b"http://example.com/the-moo")
        test_setopt(curl, lcurl.CURLOPT_USERAGENT, b"the-moo agent next generation")
        test_setopt(curl, lcurl.CURLOPT_COOKIE, b"name=moo")
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:  # pragma: no cover
            print("retrieve 1 failed", file=sys.stderr)
            raise guard.Break

        lcurl.easy_reset(curl)

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:  # pragma: no cover
            print("retrieve 2 failed", file=sys.stderr)
            raise guard.Break

    return res
