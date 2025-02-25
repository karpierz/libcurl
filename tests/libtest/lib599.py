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


@lcurl.progress_callback
def progress_callback(clientp, dltotal, dlnow, ultotal, ulnow):
    if dltotal > 0.0 and dlnow > dltotal:
        # this should not happen with test case 599
        print("%.0f > %.0f !!" % (dltotal, dlnow))
        return -1
    return 0


@curl_test_decorator
def test(URL: str, filename: str) -> lcurl.CURLcode:
    filename = str(filename)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # we want to use our own progress function
        test_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        # CURL_IGNORE_DEPRECATION(
        test_setopt(curl, lcurl.CURLOPT_PROGRESSFUNCTION, progress_callback)
        # )
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # follow redirects
        test_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        content_length = ct.c_double(0.0)
        # CURL_IGNORE_DEPRECATION(
        res = lcurl.easy_getinfo(curl,
                                 lcurl.CURLINFO_CONTENT_LENGTH_DOWNLOAD,
                                 ct.byref(content_length))
        # )
        with open(filename, "wb") as moo:
            moo.write(b"CL %.0f" % content_length.value)

    return res
