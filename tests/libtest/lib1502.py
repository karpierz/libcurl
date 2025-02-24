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

# This source code is used for lib1502, lib1503, lib1504 and lib1505 with
# only #ifdefs controlling the cleanup sequence.
#
# Test case 1502 converted from bug report #3575448, identifying a memory
# leak in the libcurl.CURLOPT_RESOLVE handling with the multi interface.


@curl_test_decorator
def test(URL: str, address: str, port: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    res = res_global_init(lcurl.CURL_GLOBAL_ALL)
    if res: return res
    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:

        redirect: str = "google.com:%s:%s" % (port, address)
        # DNS cache injection
        dns_cache_list: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                        redirect.encode("utf-8"))
        if not dns_cache_list:
            print("libcurl.slist_append() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD
        guard.add_slist(dns_cache_list)

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_RESOLVE, dns_cache_list)

        dup: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(curl)
        if not dup: return lcurl.CURLE_OUT_OF_MEMORY
        lcurl.easy_cleanup(curl)
        curl = dup
        guard.curls = [curl]

        multi_add_handle(multi, curl)

        still_running = ct.c_int()
        while True:
            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

            if not still_running.value:
                break

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
