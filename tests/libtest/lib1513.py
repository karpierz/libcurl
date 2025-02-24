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

# Test case converted from bug report #1318 by Petr Novak.
#
# Before the fix, this test program returned 52 (CURLE_GOT_NOTHING) instead
# of 42 (CURLE_ABORTED_BY_CALLBACK).


@lcurl.progress_callback
def progress_killer(clientp, dltotal, dlnow, ultotal, ulnow):
    print("PROGRESSFUNCTION called")
    return 1


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_TIMEOUT, 7)
        easy_setopt(curl, lcurl.CURLOPT_NOSIGNAL, 1)
        # CURL_IGNORE_DEPRECATION(
        easy_setopt(curl, lcurl.CURLOPT_PROGRESSFUNCTION, progress_killer)
        easy_setopt(curl, lcurl.CURLOPT_PROGRESSDATA, None)
        # )
        easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return lcurl.CURLE_OK if res == lcurl.CURLE_ABORTED_BY_CALLBACK else res
