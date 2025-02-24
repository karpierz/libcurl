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
from curl_trace import *  # noqa


@lcurl.xferinfo_callback
def xferinfo_callback(clientp, dltotal, dlnow, ultotal, ulnow):
    print("xferinfo fail!", file=sys.stderr)
    return 1  # fail as fast as we can


@curl_test_decorator
def test(URL: str, user_login: str = "u:s") -> lcurl.CURLcode:

    global libtest_debug_config, libtest_debug_cb

    res: lcurl.CURLcode = lcurl.CURLE_OK
    i:   lcurl.CURLcode = lcurl.CURLE_OK

    counter: int = 1

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        mime: ct.POINTER(lcurl.mime) = lcurl.mime_init(curl)

        field: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
        lcurl.mime_name(field, b"name")
        lcurl.mime_data(field, ct.cast(b"value", ct.POINTER(ct.c_ubyte)),
                        lcurl.CURL_ZERO_TERMINATED)

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)
        if user_login:
            easy_setopt(curl, lcurl.CURLOPT_USERPWD, user_login.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_XFERINFOFUNCTION, xferinfo_callback)
        easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)

        libtest_debug_config.nohex     = 1
        libtest_debug_config.tracetime = 1
        test_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
        easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        multi_add_handle(multi, curl)

        still_running = ct.c_int()
        multi_perform(multi, ct.byref(still_running))

        abort_on_test_timeout()

        while still_running.value and counter:
            counter -= 1

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

        # test_cleanup:

        lcurl.mime_free(mime)
        lcurl.multi_remove_handle(multi, curl)

        if res:
            i = res

    return i  # return the final return code
