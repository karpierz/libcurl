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


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() returned %d (%s)" %
                  (res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break

        protocol = ct.c_long(0)
        # CURL_IGNORE_DEPRECATION(
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_PROTOCOL, ct.byref(protocol))
        # )
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_getinfo() returned %d (%s)" %
                  (res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break

        print("Protocol: %lx" % protocol.value)

    return res  # return the final return code
