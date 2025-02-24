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
    i:   lcurl.CURLcode = TEST_ERR_FAILURE

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    multi: ct.POINTER(lcurl.CURLM) = multi_init()
    curl:  ct.POINTER(lcurl.CURL)  = easy_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # no peer verify
        easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

        # first, make an easy perform with the handle
        lcurl.easy_perform(curl)

        # then proceed and use it for a multi perform
        multi_add_handle(multi, curl)

        still_running = ct.c_int()
        multi_perform(multi, ct.byref(still_running))

        abort_on_test_timeout()

        while still_running.value:

            num = ct.c_int()
            mres: lcurl.CURLMcode = lcurl.multi_wait(multi, None, 0, TEST_HANG_TIMEOUT,
                                                     ct.byref(num))
            if mres != lcurl.CURLM_OK:
                print("libcurl.multi_wait() returned %d" % mres)
                res = TEST_ERR_MAJOR_BAD
                break

            abort_on_test_timeout()

            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

        else:
            msg: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                   ct.byref(still_running))
            if msg:
                # this should now contain a result code from the easy handle, get it
                msg = msg.contents
                i = msg.data.result

            lcurl.multi_remove_handle(multi, curl)

            # make a third transfer with the easy handle
            lcurl.easy_perform(curl)

        # test_cleanup:

        # undocumented cleanup sequence - type UA
        # curl_multi_cleanup(multi)
        # curl_easy_cleanup(curl)
        # curl_global_cleanup()

        if res:
            i = res

    return i  # return the final return code
