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

#
# Get a single URL without select().
#


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global libtest_debug_config, libtest_debug_cb

    res: lcurl.CURLcode = lcurl.CURLE_OK

    dbl_epsilon: float = 1.0
    while (1.0 + dbl_epsilon / 2.0) > 1.0:
        dbl_epsilon /= 2.0

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
        libtest_debug_config.nohex     = 1
        libtest_debug_config.tracetime = 1
        easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
        easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        multi_add_handle(multi, curl)

        still_running = ct.c_int(1)
        while still_running.value:
            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

            if not still_running.value:
                break  # done

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            max_fd = ct.c_int(-99)
            multi_fdset(multi,
                        ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                        ct.byref(max_fd))
            max_fd = max_fd.value

            # At this point, max_fd is guaranteed to be greater or equal than -1.

            timeout = lcurl.timeval(tv_sec=0, tv_usec=100_000)  # 100 ms
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout()

        connect_time = ct.c_double(0.0)
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_CONNECT_TIME, ct.byref(connect_time))
        if connect_time.value < dbl_epsilon:
            print("connect time %e is < epsilon %e" %
                  (connect_time.value, dbl_epsilon), file=sys.stderr)
            res = TEST_ERR_MAJOR_BAD

    return res
