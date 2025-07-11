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


@lcurl.fnmatch_callback
def new_fnmatch(ptr, pattern, string):
    print("lib574: match string '%s' against pattern '%s'" %
          (string.decode("utf-8"), pattern.decode("utf-8")),
          file=sys.stderr)
    return lcurl.CURL_FNMATCHFUNC_MATCH


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_WILDCARDMATCH, 1)
        test_setopt(curl, lcurl.CURLOPT_FNMATCH_FUNCTION, new_fnmatch)
        test_setopt(curl, lcurl.CURLOPT_TIMEOUT_MS, TEST_HANG_TIMEOUT)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:  # pragma: no cover
            print("libcurl.easy_perform() failed %d" % res, file=sys.stderr)
            raise guard.Break

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:  # pragma: no cover
            print("libcurl.easy_perform() failed %d" % res, file=sys.stderr)
            raise guard.Break

    return res
