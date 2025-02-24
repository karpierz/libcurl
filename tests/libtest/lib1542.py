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
import time

import libcurl as lcurl
from curl_test import *  # noqa
from curl_trace import *  # noqa

# Test libcurl.CURLOPT_MAXLIFETIME_CONN:
# Send four requests, sleeping between the second and third and setting
# MAXLIFETIME_CONN between the third and fourth. The first three requests
# should use the same connection, and the fourth request should close the
# first connection and open a second.


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global libtest_debug_config, libtest_debug_cb

    easy: ct.POINTER(lcurl.CURL) = ct.POINTER(lcurl.CURL)()
    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    easy = res_easy_init()

    with curl_guard(True, easy) as guard:

        easy_setopt(easy, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        libtest_debug_config.nohex     = 1
        libtest_debug_config.tracetime = 0
        easy_setopt(easy, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
        easy_setopt(easy, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
        easy_setopt(easy, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(easy)
        if res != lcurl.CURLE_OK: raise guard.Break

        res = lcurl.easy_perform(easy)
        if res != lcurl.CURLE_OK: raise guard.Break

        # libcurl.CURLOPT_MAXLIFETIME_CONN is inclusive - the connection
        # needs to be 2 seconds old
        time.sleep(2)

        res = lcurl.easy_perform(easy)
        if res != lcurl.CURLE_OK: raise guard.Break

        easy_setopt(easy, lcurl.CURLOPT_MAXLIFETIME_CONN, 1)

        res = lcurl.easy_perform(easy)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
