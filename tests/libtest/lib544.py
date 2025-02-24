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

teststring = b"This\0 is test binary data with an embedded NUL"
teststring = ct.create_string_buffer(teststring, len(teststring))


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        if defined("LIB545"):
            test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, len(teststring))
        test_setopt(curl, lcurl.CURLOPT_COPYPOSTFIELDS, teststring)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)  # show verbose for debug
        test_setopt(curl, lcurl.CURLOPT_HEADER,  1)  # include header

        # Update the original data to detect non-copy.
        teststring[:5] = b"FAIL\0"

        handle2: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(curl)
        lcurl.easy_cleanup(curl)
        curl = handle2
        del handle2

        # Now, this is a POST request with binary 0 embedded in POST data.
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
