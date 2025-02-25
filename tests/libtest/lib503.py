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

# Source code in here hugely as reported in bug report 651460 by
# Christopher R. Palmer.
#
# Use multi interface to get HTTPS document over proxy, and provide
# auth info.


@curl_test_decorator
def test(URL: str,
         proxy: str = None,
         proxy_login: str = "test%20:ing%41") -> lcurl.CURLcode:

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
        easy_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)
        easy_setopt(curl, lcurl.CURLOPT_PROXYUSERNAME,
                          proxy_login.split(":")[0].encode("utf-8")
                          if proxy_login else None)
        easy_setopt(curl, lcurl.CURLOPT_PROXYPASSWORD,
                          proxy_login.split(":")[1].encode("utf-8")
                          if proxy_login else None)
        easy_setopt(curl, lcurl.CURLOPT_USERPWD, b"test:ing")
        easy_setopt(curl, lcurl.CURLOPT_HTTPPROXYTUNNEL, 1)
        easy_setopt(curl, lcurl.CURLOPT_HEADER,  1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

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

    return res
