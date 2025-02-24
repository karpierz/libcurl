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


class headerinfo(ct.Structure):
    _fields_ = [
    ("largest", ct.c_size_t),
]


@lcurl.write_callback
def header_callback(buffer, size, nitems, userp):
    info = ct.cast(userp, ct.POINTER(headerinfo)).contents
    header_size = nitems * size
    if header_size > info.largest:
        # remember the longest header
        info.largest = header_size
    return header_size


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res:  lcurl.CURLcode = lcurl.CURLE_OK

    info = headerinfo(0)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, header_callback)
        easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, ct.byref(info))
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        code: lcurl.CURLcode = lcurl.easy_perform(curl)

        if code != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_perform() failed, with code %d (%s)" %
                  (current_file(), current_line(),
                   code, lcurl.easy_strerror(code).decode("utf-8")), file=sys.stderr)
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break

        print("Max = %ld" % info.largest)

    return res
