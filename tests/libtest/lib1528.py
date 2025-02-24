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
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_FAILED_INIT

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # http header list
        hhl: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                             b"User-Agent: Http Agent")
        phl: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                             b"Proxy-User-Agent: Http Agent2")
        guard.add_slist(hhl)
        guard.add_slist(phl)
        if not hhl or not phl: return res

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)
        test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, hhl)
        test_setopt(curl, lcurl.CURLOPT_PROXYHEADER, phl)
        test_setopt(curl, lcurl.CURLOPT_HEADEROPT, lcurl.CURLHEADER_SEPARATE)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_PROXYTYPE, lcurl.CURLPROXY_HTTP)
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
