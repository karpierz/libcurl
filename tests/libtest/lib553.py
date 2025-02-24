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

# This test case and code is based on the bug recipe Joe Malicki provided for
# bug report #1871269, fixed on Jan 14 2008 before the 7.18.0 release.

POSTLEN = 40960

NUM_HEADERS  = 8
SIZE_HEADERS = 5000


read_total: int = POSTLEN
read_buf = (ct.c_char * 1024)()

@lcurl.read_callback
def read_callback(buffer, size, nitems, stream):
    global read_total, read_buf
    buffer_size = nitems * size
    ct.memset(read_buf, ord(b'A'), ct.sizeof(read_buf))
    data_size = min(buffer_size, read_total, ct.sizeof(read_buf))
    ct.memmove(buffer, read_buf, data_size)
    read_total -= data_size
    return data_size


testbuf = (ct.c_char * (SIZE_HEADERS + 100))()

@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global testbuf

    res: lcurl.CURLcode = lcurl.CURLE_FAILED_INIT

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        headerlist: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
        hl: ct.POINTER(lcurl.slist)
        for i in range(NUM_HEADERS):
            prefix = b"Header%d: " % i
            ct.memmove(testbuf, prefix, len(prefix))
            ct.memset(ct.byref(testbuf, len(prefix)), ord(b'A'), SIZE_HEADERS)
            testbuf[len(prefix) + SIZE_HEADERS] = 0  # null-terminate

            hl = lcurl.slist_append(headerlist, testbuf)
            if hl: headerlist = hl
            if not hl:
                guard.add_slist(headerlist)
                return res

        hl = lcurl.slist_append(headerlist, b"Expect: ")
        if hl: headerlist = hl
        guard.add_slist(headerlist)
        if not hl: return res

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headerlist)
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, POSTLEN)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
