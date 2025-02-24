# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Linus Nielsen Feltzing <linus@haxx.se>
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
import time

import libcurl as lcurl
from curl_test import *  # noqa

NUM_HANDLES = 4


@curl_test_decorator
def test(URL: str, address: str, port: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    slist: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
    # Create fake DNS entries for serverX.example.com for all handles
    for i in range(NUM_HANDLES):
        dns_entry: str = "server%d.example.com:%s:%s" % (
                         i + 1, port, address)
        print("%s" % dns_entry)
        slist2: ct.POINTER(lcurl.slist) = lcurl.slist_append(slist,
                                                dns_entry.encode("utf-8"))
        if not slist2:
            lcurl.slist_free_all(slist)
            print("libcurl.slist_append() failed", file=sys.stderr)
            return 1  # !!! use proper error !!!
        slist = slist2

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        lcurl.slist_free_all(slist)
        return TEST_ERR_MAJOR_BAD

    multi: ct.POINTER(lcurl.CURLM) = multi_init()
    # get NUM_HANDLES easy handles
    curls: List[ct.POINTER(lcurl.CURL)] = [easy_init() for i in range(NUM_HANDLES)]

    with curl_guard(True, curls, multi) as guard:
        guard.add_slist(slist)

        multi_setopt(multi, lcurl.CURLMOPT_MAXCONNECTS, 3)

        # get NUM_HANDLES easy handles
        for i, curl in enumerate(curls):
            # specify target
            target_url = "http://server%d.example.com:%s/path/1506%04i" % (
                         i + 1, port, i + 1)
            easy_setopt(curl, lcurl.CURLOPT_URL, target_url.encode("utf-8"))
            # go verbose
            easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            # include headers
            easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
            easy_setopt(curl, lcurl.CURLOPT_RESOLVE, slist)

        print("Start at URL 0", file=sys.stderr)

        for curl in curls:

            # add handle to multi
            multi_add_handle(multi, curl)

            still_running = ct.c_int()
            while True:
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

                timeout = lcurl.timeval(tv_sec=1, tv_usec=0)  # 1 sec
                res = select_test(max_fd + 1,
                                  ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                  ct.byref(timeout))

                abort_on_test_timeout()

            time.sleep(1/1000)  # to ensure different end times

    return res
