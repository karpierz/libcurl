# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Linus Nielsen Feltzing <linus@haxx.se>
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


@curl_test_decorator
def test(URL: str, alt_svc: str) -> lcurl.CURLcode:
    alt_svc = str(alt_svc)

    ret: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_ALTSVC, alt_svc.encode("utf-8"))

        ret = lcurl.easy_perform(curl)
        if not ret:
            # make a copy and check that this also has alt-svc activated
            also: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(curl)
            if also:
                ret = lcurl.easy_perform(also)
                # we close the second handle first, which makes it store the alt-svc
                # file only to get overwritten when the next handle is closed!
                lcurl.easy_cleanup(also)

        lcurl.easy_reset(curl)

    return ret
