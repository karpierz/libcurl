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
# are also available at https://curl.haxx.se/docs/copyright.html.
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


def showem(curl: ct.POINTER(lcurl.CURL), type: int):
    prev:   ct.POINTER(lcurl.header) = ct.POINTER(lcurl.header)()
    header: ct.POINTER(lcurl.header) = lcurl.easy_nextheader(curl, type, 0, prev)
    while header:
        hdr = header.contents
        print(" %s == %s (%d/%d)" % (hdr.name,  hdr.value, hdr.index, hdr.amount))
        prev   = header
        header = lcurl.easy_nextheader(curl, type, 0, prev)


@curl_test_decorator
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
        # ignores any content
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_skipped)

        # if there's a proxy set, use it
        if proxy and proxy[0]:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_PROXY,
                                    proxy.encode("utf-8") if proxy else None)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPPROXYTUNNEL, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("badness: %d" % res)

        showem(curl, lcurl.CURLH_CONNECT | lcurl.CURLH_HEADER |
                     lcurl.CURLH_TRAILER | lcurl.CURLH_1XX)

    return res
