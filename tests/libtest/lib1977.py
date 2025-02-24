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

    curlu:   ct.POINTER(lcurl.CURLU) = lcurl.url()
    curlu_2: ct.POINTER(lcurl.CURLU) = lcurl.url()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # first transfer: set just the URL in the first CURLU handle
        lcurl.url_set(curlu, lcurl.CURLUPART_URL, URL.encode("utf-8"),
                             lcurl.CURLU_DEFAULT_SCHEME)
        easy_setopt(curl, lcurl.CURLOPT_CURLU, curlu)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        effective = ct.c_char_p(None)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_EFFECTIVE_URL,
                                       ct.byref(effective))
        if res != lcurl.CURLE_OK: raise guard.Break
        print("effective URL: %s" % effective.value.decode("utf-8"))

        # second transfer: set URL + query in the second CURLU handle
        lcurl.url_set(curlu_2, lcurl.CURLUPART_URL, URL.encode("utf-8"),
                               lcurl.CURLU_DEFAULT_SCHEME)
        lcurl.url_set(curlu_2, lcurl.CURLUPART_QUERY, b"foo", 0)
        easy_setopt(curl, lcurl.CURLOPT_CURLU, curlu_2)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        effective = ct.c_char_p(None)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_EFFECTIVE_URL,
                                       ct.byref(effective))
        if res != lcurl.CURLE_OK: raise guard.Break
        print("effective URL: %s" % effective.value.decode("utf-8"))

        # third transfer: append extra query in the second CURLU handle, but do not
        # set CURLOPT_CURLU again. this is to test that the contents of the handle
        # is allowed to change between transfers and is used without having to set
        # CURLOPT_CURLU again
        lcurl.url_set(curlu_2, lcurl.CURLUPART_QUERY, b"bar",
                               lcurl.CURLU_APPENDQUERY)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        effective = ct.c_char_p(None)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_EFFECTIVE_URL,
                                       ct.byref(effective))
        if res != lcurl.CURLE_OK: raise guard.Break
        print("effective URL: %s" % effective.value.decode("utf-8"))

    lcurl.url_cleanup(curlu)
    lcurl.url_cleanup(curlu_2)
    lcurl.global_cleanup()

    return res
