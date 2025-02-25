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


@curl_test_decorator
def test(URL: str, cookie_file: str) -> lcurl.CURLcode:
    cookie_file = str(cookie_file)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    multi: ct.POINTER(lcurl.CURLM)  = multi_init()
    share: ct.POINTER(lcurl.CURLSH) = lcurl.share_init()
    curl:  ct.POINTER(lcurl.CURL)   = easy_init()

    with curl_guard(True, curl, multi, share):
        if not multi: lcurl.CURLcode(1).value
        if not share: lcurl.CURLcode(1).value
        if not curl:  lcurl.CURLcode(1).value

        lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE, lcurl.CURL_LOCK_DATA_COOKIE)
        lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE, lcurl.CURL_LOCK_DATA_COOKIE)

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SHARE, share)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_COOKIEFILE, cookie_file.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_COOKIEJAR,  cookie_file.encode("utf-8"))

        lcurl.multi_add_handle(multi, curl)

        still_running = ct.c_int(1)
        while still_running.value:
            lcurl.multi_perform(multi, ct.byref(still_running))

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            max_fd = ct.c_int(0)
            lcurl.multi_fdset(multi,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(max_fd))
            max_fd = max_fd.value

            curl_timeout = ct.c_long()
            lcurl.multi_timeout(multi, ct.byref(curl_timeout))
            curl_timeout = curl_timeout.value

            timeout = (lcurl.timeval(tv_sec=curl_timeout // 1000,
                                     tv_usec=(curl_timeout % 1000) * 1000)
                       if curl_timeout > 0 else
                       lcurl.timeval(tv_sec=0, tv_usec=1000))  # 1 ms
            lcurl.select(max_fd + 1,
                         ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                         ct.byref(timeout))

        lcurl.easy_setopt(curl, lcurl.CURLOPT_COOKIELIST, b"FLUSH")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SHARE, None)

    return res
