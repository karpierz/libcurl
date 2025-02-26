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

# Test case for below scenario:
#   - Connect to an FTP server using CONNECT_ONLY option
#
# The test case originated for verifying CONNECT_ONLY option shall not
# block after protocol connect is done, but it returns the message
# with function lcurl.multi_info_read().

TEST_HANG_TIMEOUT = 60 * 1000


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        # specify target
        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 1)
        # go verbose
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        multi_add_handle(multi, curl)

        still_running = ct.c_int()
        while True:

            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout(TEST_HANG_TIMEOUT)

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

            curl_timeout = ct.c_long(-99)
            multi_timeout(multi, ct.byref(curl_timeout))
            curl_timeout = curl_timeout.value

            # At this point, timeout is guaranteed to be greater or equal than -1.
            if curl_timeout != -1:
                curl_timeout = min(LONG_MAX, INT_MAX, curl_timeout)
                timeout = lcurl.timeval(tv_sec=curl_timeout // 1000,
                                        tv_usec=(curl_timeout % 1000) * 1000)
            else:
                timeout = lcurl.timeval(tv_sec=TEST_HANG_TIMEOUT // 1000 - 1,
                                        tv_usec=0)
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout(TEST_HANG_TIMEOUT)

        msgs_left = ct.c_int()
        msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                ct.byref(msgs_left))
        if msgp:
            msg = msgp.contents
            res = msg.data.result

    return res
