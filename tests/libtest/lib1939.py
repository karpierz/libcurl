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


@curl_test_decorator
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        # Crash only happens when using HTTPS
        c: lcurl.CURLcode = lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        if not c:
            # Any old HTTP tunneling proxy will do here
            c = lcurl.easy_setopt(curl, lcurl.CURLOPT_PROXY,
                                  proxy.encode("utf-8") if proxy else None)
        if not c:
            # We're going to drive the transfer using multi interface here,
            # because we want to stop during the middle.
            mres: lcurl.CURLMcode = lcurl.multi_add_handle(multi, curl)
            if mres == lcurl.CURLM_OK:
                # Run the multi handle once, just enough to start establishing an
                # HTTPS connection.
                running_handles = ct.c_int()
                mres = lcurl.multi_perform(multi, ct.byref(running_handles))

            if mres != lcurl.CURLM_OK:
                print("libcurl.multi_perform failed", file=sys.stderr)

    return lcurl.CURLE_OK
