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

# 3x download!
# 1. normal
# 2. dup handle
# 3. with multi interface


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    res = global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = easy_init()

    easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
    easy_setopt(curl, lcurl.CURLOPT_WILDCARDMATCH, 1)
    easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

    res = lcurl.easy_perform(curl)
    if res: goto(test_cleanup)
    res = lcurl.easy_perform(curl)
    if res: goto(test_cleanup)

    dup_curl: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(curl)
    if not dup_curl: goto(test_cleanup)
    lcurl.easy_cleanup(curl)
    curl = dup_curl

    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        multi_add_handle(multi, curl)

        still_running = ct.c_int(0)
        multi_perform(multi, ct.byref(still_running))

        abort_on_test_timeout()

        while still_running.value:

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            max_fd = ct.c_int(-99)
            multi_fdset(multi,
                        ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                        ct.byref(max_fd));
            max_fd = max_fd.value

            # At this point, max_fd is guaranteed to be greater or equal than -1.

            timeout = lcurl.timeval(tv_sec=0, tv_usec=100_000)  # 100 ms
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout()

            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

    return res
