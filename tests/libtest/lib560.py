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

# Simply download an HTTPS file!
#
# This test was added after the HTTPS-using-multi-interface with OpenSSL
# regression of 7.19.1 to hopefully prevent this embarrassing mistake from
# appearing again... Unfortunately the bug wasn't triggered by this test,
# which presumably is because the connect to a local server is too
# fast/different compared to the real/distant servers we saw the bug happen
# with.


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    # libcurl.global_init called indirectly from libcurl.easy_init.
    #
    curl: ct.POINTER(lcurl.CURL) = easy_init()
    # init a multi stack
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        # set options
        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

        # add the individual transfers
        multi_add_handle(multi, curl)

        # we start some action by calling perform right away
        still_running = ct.c_int()  # keep number of running handles
        multi_perform(multi, ct.byref(still_running))

        abort_on_test_timeout()

        while still_running.value:

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            # get file descriptors from the transfers
            max_fd = ct.c_int(-99)
            multi_fdset(multi,
                        ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                        ct.byref(max_fd))
            max_fd = max_fd.value

            # At this point, max_fd is guaranteed to be greater or equal than -1.

            # set a suitable timeout to play around with
            timeout = lcurl.timeval(tv_sec=1, tv_usec=0)  # 1 sec
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout()

            # timeout or readable/writable sockets
            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

    return res
