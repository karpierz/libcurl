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

from typing import List
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# This code sets up multiple easy handles that transfer a single file from
# the same URL, in a serial manner after each other. Due to the connection
# sharing within the multi handle all transfers are performed on the same
# persistent connection.
#
# This source code is used for lib526, lib527 and lib532 with only #ifdefs
# controlling the small differences.
#
# - lib526 closes all easy handles after
#   they all have transferred the file over the single connection
# - lib527 closes each easy handle after each single transfer.
# - lib532 uses only a single easy handle that is removed, reset and then
#   re-added for each transfer
#
# Test case 526, 527 and 532 use FTP, while test 528 uses the lib526 tool but
# with HTTP.

NUM_HANDLES = 4


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    multi: ct.POINTER(lcurl.CURLM) = multi_init()
    # get NUM_HANDLES easy handles
    curls: List[ct.POINTER(lcurl.CURL)] = [easy_init() for i in range(NUM_HANDLES)]

    with curl_guard(True, curls, multi) as guard:

        # get NUM_HANDLES easy handles
        for curl in curls:
            # specify target
            easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # go verbose
            easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        current: int = 0

        multi_add_handle(multi, curls[current])

        print("Start at URL 0", file=sys.stderr)

        still_running = ct.c_int()
        while True:
            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

            if not still_running.value:

                if defined("LIB527"):
                    # NOTE: this code does not remove the handle from the multi handle
                    # here, which would be the nice, sane and documented way of working.
                    # This however tests that the API survives this abuse gracefully.
                    lcurl.easy_cleanup(curls[current])
                    curls[current] = ct.POINTER(lcurl.CURL)()

                current += 1
                if current >= NUM_HANDLES:
                    break  # done

                print("Advancing to URL %d" % current, file=sys.stderr)
                if defined("LIB532"):
                    # first remove the only handle we use
                    lcurl.multi_remove_handle(multi, curls[0])
                    # make us reuse the same handle all the time, and try resetting
                    # the handle first too
                    lcurl.easy_reset(curls[0])

                    easy_setopt(curls[0], lcurl.CURLOPT_URL, URL.encode("utf-8"))
                    # go verbose
                    easy_setopt(curls[0], lcurl.CURLOPT_VERBOSE, 1)

                    # re-add it
                    multi_add_handle(multi, curls[0])
                else:
                    multi_add_handle(multi, curls[current])

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

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
