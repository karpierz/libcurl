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
# are also available at https://curl.haxx.se/docs/copyright.html.
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


class put_buffer(ct.Structure):
    _fields_ = [
    ("buf", ct.POINTER(ct.c_byte)),
    ("len", ct.c_size_t),
]


@lcurl.read_callback
def put_callback(buffer, size, nitems, userp):
    putdata = ct.cast(userp, ct.POINTER(put_buffer)).contents
    totalsize = size * nitems
    tocopy = min(putdata.len, totalsize)
    ct.memmove(buffer, putdata.buf, tocopy)
    c_ptr_iadd(putdata.buf, tocopy)  # advance pointer
    putdata.len -= tocopy
    return tocopy


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        testput: bytes = b"This is test PUT data\n"

        pbuf = put_buffer()
        pbuf.buf = ct.cast(testput, ct.POINTER(ct.c_byte))
        pbuf.len = len(testput)

        # PUT
        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, put_callback)
        easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(pbuf))
        easy_setopt(curl, lcurl.CURLOPT_INFILESIZE, pbuf.len)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        # POST
        easy_setopt(curl, lcurl.CURLOPT_POST, 1)
        easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, testput);
        easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, len(testput))

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
