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
# Test suppressing the If-Modified-Since header
#


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_TIMECONDITION, lcurl.CURL_TIMECOND_IFMODSINCE)
        # Some TIMEVALUE; it doesn't matter.
        easy_setopt(curl, lcurl.CURLOPT_TIMEVALUE, 1566210680)

        header: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                b"If-Modified-Since:")
        if not header: return TEST_ERR_MAJOR_BAD
        guard.add_slist(header)

        easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, header)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        # Confirm that the condition checking still worked, even though we
        # suppressed the actual header.
        # The server returns 304, which means the condition is "unmet".

        unmet = ct.c_long(0)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_CONDITION_UNMET, ct.byref(unmet))
        if res != lcurl.CURLE_OK: raise guard.Break
        unmet = unmet.value

        if unmet != 1:
            return TEST_ERR_FAILURE

    return res
