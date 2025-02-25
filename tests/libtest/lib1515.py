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
import time

import libcurl as lcurl
from curl_test import *  # noqa
from curl_trace import *  # noqa

# Check for bugs #1303 and #1327: libcurl should never remove DNS entries
# created via libcurl.CURLOPT_RESOLVE, neither after DNS_CACHE_TIMEOUT
# elapses (test1515) nor a dead connection is detected (test1616).

DNS_TIMEOUT = 1


def do_one_request(multi: ct.POINTER(lcurl.CURLM), URL: str, resolve: str) -> lcurl.CURLcode:

    global libtest_debug_config, libtest_debug_cb

    res: lcurl.CURLcode = lcurl.CURLE_OK

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(False, curl) as guard:

        resolve_list: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                      resolve.encode("utf-8"))
        guard.add_slist(resolve_list)

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_RESOLVE, resolve_list)
        easy_setopt(curl, lcurl.CURLOPT_DNS_CACHE_TIMEOUT, DNS_TIMEOUT)

        libtest_debug_config.nohex     = 1
        libtest_debug_config.tracetime = 1
        easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
        easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

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

            timeout = lcurl.timeval(tv_sec=1, tv_usec=0)  # 1 sec
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout()

        while True:
            msgs_left = ct.c_int()
            msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                    ct.byref(msgs_left))
            if not msgp: break
            msg = msgp.contents

            if msg.msg == lcurl.CURLMSG_DONE and msg.easy_handle == curl:
                res = msg.data.result
                break

        # test_cleanup:

        lcurl.multi_remove_handle(multi, curl)

    return res


@curl_test_decorator
def test(URL: str, address: str, port: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    count: int = 2

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    lcurl.global_trace(b"all")

    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, mcurl=multi) as guard:

        dns_entry : str= "testserver.example.com:%s:%s" % (port, address)

        for i in range(1, count + 1):
            # second request must succeed like the first one
            target_url = "http://testserver.example.com:%s/%s%04d" % (
                         port, URL, i)

            res = do_one_request(multi, target_url, dns_entry)
            if res != lcurl.CURLE_OK:
                print("request %s failed with %d" % (target_url, res),
                      file=sys.stderr)
                break

            if i < count:
                time.sleep(DNS_TIMEOUT + 1)

    return res
