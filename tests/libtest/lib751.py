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

#
# Get a single URL without select().
#

TEST_HANG_TIMEOUT = 60 * 1000


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_FAILED_INIT

    easies = (ct.POINTER(lcurl.CURL) * 1000)()
    ct.memset(easies, 0, ct.sizeof(easies))

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    multi: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    with curl_guard(True, None, multi) as guard:
        if not multi:  # pragma: no cover
            res = lcurl.CURLE_OUT_OF_MEMORY
            raise guard.Break

        for i in range(len(easies)):
            easy: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
            if not easy:  # pragma: no cover
                res = lcurl.CURLE_OUT_OF_MEMORY
                break

            easies[i] = easy

            res = lcurl.easy_setopt(easy, lcurl.CURLOPT_URL,
                                          URL.encode("utf-8"))
            if not res:
                res = lcurl.easy_setopt(easy, lcurl.CURLOPT_VERBOSE, 1)
            if res:  # pragma: no cover
                break

            mres: lcurl.CURLMcode = lcurl.multi_add_handle(multi, easy)
            if mres != lcurl.CURLM_OK:  # pragma: no cover
                print("MULTI ERROR: %s" %
                      lcurl.multi_strerror(mres).decode("utf-8"))
                res = lcurl.CURLE_FAILED_INIT
                break

        for i, easy in enumerate(easies):
            if easy:  # pragma: no branch
                lcurl.multi_remove_handle(multi, easy)
                lcurl.easy_cleanup(easy)
                easies[i] = None

    if res:  # pragma: no cover
        print("ERROR: %s" % lcurl.easy_strerror(res).decode("utf-8"))

    return res
