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


TEST_DATA_STRING = b"Test data"
cb_count: int    = 0


@lcurl.resolver_start_callback
def resolver_alloc_cb_fail(resolver_state, reserved, userdata):
    global cb_count
    cb_count += 1
    if ct.c_char_p(userdata).value != TEST_DATA_STRING:
        print("Invalid test data received", file=sys.stderr)
        sys.exit(1)
    return 1


@lcurl.resolver_start_callback
def resolver_alloc_cb_pass(resolver_state, reserved, userdata):
    global cb_count
    cb_count += 1
    if ct.c_char_p(userdata).value != TEST_DATA_STRING:
        print("Invalid test data received", file=sys.stderr)
        sys.exit(1)
    return 0


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our request.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_RESOLVER_START_DATA, TEST_DATA_STRING)
        test_setopt(curl, lcurl.CURLOPT_RESOLVER_START_FUNCTION, resolver_alloc_cb_fail)

        # this should fail
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_COULDNT_RESOLVE_HOST:
            print("libcurl.easy_perform should have returned "
                  "CURLE_COULDNT_RESOLVE_HOST but instead returned error %d" % res,
                  file=sys.stderr)
            if res == lcurl.CURLE_OK:
                res = TEST_ERR_FAILURE
            raise guard.Break

        test_setopt(curl, lcurl.CURLOPT_RESOLVER_START_FUNCTION, resolver_alloc_cb_pass)

        # this should succeed
        res = lcurl.easy_perform(curl)
        if res:
            print("libcurl.easy_perform failed.", file=sys.stderr)
            raise guard.Break

        if cb_count != 2:
            print("Unexpected number of callbacks: %d" % cb_count, file=sys.stderr)
            res = TEST_ERR_FAILURE
            raise guard.Break

    return res
