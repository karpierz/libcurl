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


testpost = [
    "one",
    "two",
    "three",
    "and a final longer crap: four",
    None,
]


class WriteThis(ct.Structure):
    _fields_ = [
    ("counter", ct.c_int),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    if buffer_size < 1: return 0
    data = testpost[pooh.counter]
    if not data: return 0  # no more data left to deliver
    data = data.encode("utf-8")
    data_size = len(data)
    if buffer_size < data_size:
        print("read buffer is too small to run test", file=sys.stderr)
        return 0
    ct.memmove(buffer, data, data_size)
    pooh.counter += 1  # advance pointer
    return data_size



@curl_test_decorator
def test(URL: str, user_login: str = "foo:bar") -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    pooh = WriteThis()
    pooh.counter = 0

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        slist: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                               b"Transfer-Encoding: chunked")
        if not slist:
            print("libcurl.slist_append() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD
        guard.add_slist(slist)

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # Now specify we want to POST data
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        # we want to use our own read function
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        # pointer to pass to our read function
        test_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(pooh))
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        # enforce chunked transfer by setting the header
        test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, slist)
        if defined("LIB565"):
            test_setopt(curl, lcurl.CURLOPT_HTTPAUTH, lcurl.CURLAUTH_DIGEST)
            if user_login:
                test_setopt(curl, lcurl.CURLOPT_USERPWD, user_login.encode("utf-8"))

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
