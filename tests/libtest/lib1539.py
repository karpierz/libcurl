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

# Make sure libcurl does not send a `Content-Length: -1` header when HTTP POST
# size is unknown.

testdata = b"dummy"


class WriteThis(ct.Structure):
    _fields_ = [
    ("readptr",  ct.POINTER(ct.c_ubyte)),
    ("sizeleft", ct.c_size_t),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    if buffer_size <= 0:
        return 0  # pragma: no cover
    if pooh.sizeleft == 0:       # no more data left to deliver
        return 0  # pragma: no cover
    buffer[0] = pooh.readptr[0]  # copy one single byte
    c_ptr_iadd(pooh.readptr, 1)  # advance pointer
    pooh.sizeleft -= 1           # less data left
    return 1                     # we return 1 byte at a time!


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    pooh = WriteThis(ct.cast(testdata, ct.POINTER(ct.c_ubyte)), len(testdata))

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_POST, 1)
        # Purposely omit to set libcurl.CURLOPT_POSTFIELDSIZE
        easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(pooh))
        # speak HTTP 1.0 - no chunked!
        easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION,
                          lcurl.CURL_HTTP_VERSION_1_0)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
