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

# Source code in here hugely as reported in bug report 651464 by
# Christopher R. Palmer.
#
# Use multi interface to get document over proxy with bad port number.
# This caused the interface to "hang" in libcurl 7.10.2.


@curl_test_decorator
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # The point here is that there must not be anything running on the given
        # proxy port
        if proxy:
            easy_setopt(curl, lcurl.CURLOPT_PROXY, proxy.encode("utf-8") )
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        multi_add_handle(multi, curl)

        still_running = ct.c_int()
        while True:
            print("libcurl.multi_perform()", file=sys.stderr)
            multi_perform(multi, ct.byref(still_running))

            while still_running.value:
                num = ct.c_int()
                mres: lcurl.CURLMcode = lcurl.multi_wait(multi, None, 0, TEST_HANG_TIMEOUT,
                                                         ct.byref(num))
                if mres != lcurl.CURLM_OK:
                    print("libcurl.multi_wait() returned %d" % mres)
                    res = TEST_ERR_MAJOR_BAD
                    return res

                abort_on_test_timeout()
                multi_perform(multi, ct.byref(still_running))
                abort_on_test_timeout()

            abort_on_test_timeout()

            if not still_running.value:
                # This is where this code is expected to reach
                msgs_left = ct.c_int()
                msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                        ct.byref(msgs_left))
                print("Expected: not running", file=sys.stderr)
                if msgp and not msgs_left.value:
                    res = TEST_ERR_SUCCESS  # this is where we should be
                else:
                    res = TEST_ERR_FAILURE  # not correct
                break  # done

            print("running == %d" % still_running.value, file=sys.stderr)

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            print("libcurl.multi_fdset()", file=sys.stderr)

            max_fd = ct.c_int(-99)
            multi_fdset(multi,
                        ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                        ct.byref(max_fd))
            max_fd = max_fd.value

            # At this point, max_fd is guaranteed to be greater or equal than -1.

            timeout = lcurl.timeval(tv_sec=1, tv_usec=0)  # 1 sec
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout()

    return res
