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


chunks = [
    b"one",
    b"two",
    b"three",
    b"four",
    None
]


idx: int = 0

@lcurl.read_callback
def read_callback(buffer, size, nitems, stream):
    global chunks
    global idx
    if chunks[idx] is None: return 0
    chunk_len = len(chunks[idx])
    ct.memmove(buffer, chunks[idx], chunk_len)
    buffer[chunk_len] = ord(b'\0')
    idx += 1
    return chunk_len


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # deliberately setting the size - to a wrong value to make sure libcurl
        # ignores it
        easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, 4)
        easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, None)
        easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        easy_setopt(curl, lcurl.CURLOPT_POST, 1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION,
                          lcurl.CURL_HTTP_VERSION_1_1)
        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_READDATA, None)

        chunk: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                               b"Expect:")
        if chunk:
            n: ct.POINTER(lcurl.slist) = lcurl.slist_append(chunk,
                                               b"Transfer-Encoding: chunked")
            if n:
                chunk = n
                easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, n)
        guard.add_slist(chunk)

        res = lcurl.easy_perform(curl)

        lcurl.slist_free_all(chunk)

    return res
