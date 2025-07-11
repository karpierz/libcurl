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
def test(URL: str, user_login: str = "u:s") -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK
    i:   lcurl.CURLcode = lcurl.CURLE_OK

    counter: int = 3

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        if user_login:
            easy_setopt(curl, lcurl.CURLOPT_USERPWD, user_login.encode("utf-8"))

        multi_add_handle(multi, curl)

        still_running = ct.c_int()
        multi_perform(multi, ct.byref(still_running))

        abort_on_test_timeout()

        while still_running.value and counter:
            counter -= 1

            num = ct.c_int()
            mres: lcurl.CURLMcode = lcurl.multi_wait(multi, None, 0, TEST_HANG_TIMEOUT,
                                                     ct.byref(num))
            if mres != lcurl.CURLM_OK:  # pragma: no cover
                print("libcurl.multi_wait() returned %d" % mres)
                return TEST_ERR_MAJOR_BAD

            abort_on_test_timeout()

            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

        msgs_left = ct.c_int(0)
        msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                ct.byref(msgs_left))
        if msgp:
            msg = msgp.contents
            # this should now contain a result code from the easy handle, get it
            i = msg.data.result

        #test_cleanup:
        if res:  # pragma: no cover
            i = res

    return i  # return the final return code
