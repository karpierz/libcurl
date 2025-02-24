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

if defined("LIB1946"):
    HEADER_REQUEST = 0
else:
    HEADER_REQUEST = -1

testdata = [
    "daTE",
    "Server",
    "content-type",
    "content-length",
    "location",
    "set-cookie",
    "silly-thing",
    "fold",
    "blank",
    "Blank2",
]


def showem(curl: ct.POINTER(lcurl.CURL), type: int):
    header = ct.POINTER(lcurl.header)()
    for show in testdata:
        if lcurl.easy_header(curl, show.encode("utf-8"), 0, type,
                             HEADER_REQUEST, ct.byref(header)) == lcurl.CURLHE_OK:
            hdr: lcurl.header = header.contents
            if hdr.amount > 1:
                # more than one, iterate over them
                index  = 0
                amount = hdr.amount
                while True:
                    print("- %s == %s (%d/%d)" %
                          (hdr.name.decode("utf-8"), hdr.value.decode("utf-8"), index, amount))

                    index += 1
                    if index == amount:
                        break

                    if lcurl.easy_header(curl, show.encode("utf-8"), index, type,
                                         HEADER_REQUEST, ct.byref(header)) != lcurl.CURLHE_OK:
                        break
                    hdr = header.contents
            else:
                # only one of this
                print(" %s == %s" %
                      (hdr.name.decode("utf-8"), hdr.value.decode("utf-8")))


@curl_test_decorator
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
        # ignores any content
        easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_skipped)

        # if there's a proxy set, use it
        if proxy:
            easy_setopt(curl, lcurl.CURLOPT_PROXY, proxy.encode("utf-8"))
            easy_setopt(curl, lcurl.CURLOPT_HTTPPROXYTUNNEL, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        showem(curl, lcurl.CURLH_HEADER)
        if proxy:
            # now show connect headers only
            showem(curl, lcurl.CURLH_CONNECT)
        showem(curl, lcurl.CURLH_1XX)
        showem(curl, lcurl.CURLH_TRAILER)

    return res
