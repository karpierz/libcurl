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


@lcurl.write_callback
def writecb(buffer, size, nitems, userp):
    # ignore the data
    return size * nitems


@curl_test_decorator
def test(URL: str, URL2: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # perform a request that involves redirection
        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, writecb)
        easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)
            raise guard.Break

        # count the number of requests by reading the first header of each
        # request.
        origins = (lcurl.CURLH_HEADER  | lcurl.CURLH_TRAILER |
                   lcurl.CURLH_CONNECT | lcurl.CURLH_1XX |
                   lcurl.CURLH_PSEUDO)
        count = 0
        while lcurl.easy_nextheader(curl, origins, count, None):
            count += 1
        print("count = %u" % count)

        # perform another request - without redirect
        easy_setopt(curl, lcurl.CURLOPT_URL, URL2.encode("utf-8"))

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)
            raise guard.Break

        # count the number of requests again.
        count = 0
        while lcurl.easy_nextheader(curl, origins, count, None):
            count += 1
        print("count = %u" % count)

    return res
