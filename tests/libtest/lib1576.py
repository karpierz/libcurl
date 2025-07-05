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

testdata = b"request indicates that the client, which made"


@lcurl.read_callback
def read_callback(buffer, size, nitems, stream):
    amount = nitems * size  # Total bytes curl wants
    data_size = len(testdata)
    if amount < data_size:
        return data_size
    ct.memmove(buffer, testdata, data_size)
    return data_size


@lcurl.seek_callback
def seek_callback(instream, offset, origin):
    if origin != SEEK_SET:
      return lcurl.CURL_SEEKFUNC_FAIL
    return lcurl.CURL_SEEKFUNC_OK


@curl_test_decorator
def test(URL: str, testno: str) -> lcurl.CURLcode:
    testno = int(testno)

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HEADER,  1)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_UPLOAD,  1)
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        test_setopt(curl, lcurl.CURLOPT_SEEKFUNCTION, seek_callback)
        test_setopt(curl, lcurl.CURLOPT_INFILESIZE, len(testdata))
        test_setopt(curl, lcurl.CURLOPT_CUSTOMREQUEST, b"CURL")
        if testno == 1578:
            test_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, lcurl.CURLFOLLOW_FIRSTONLY)
        else:
            test_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, lcurl.CURLFOLLOW_OBEYCODE)
        # Remove "Expect: 100-continue"
        pHeaderList: ct.POINTER(lcurl.slist) = lcurl.slist_append(None, b"Expect:")
        guard.add_slist(pHeaderList)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, pHeaderList)

        res = lcurl.easy_perform(curl)

    return res
