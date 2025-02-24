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
def test(URL: str, URL1: str,
         user_login: str = "me:password") -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_MAJOR_BAD

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_HTTPAUTH,
                    lcurl.CURLAUTH_BASIC | lcurl.CURLAUTH_DIGEST | lcurl.CURLAUTH_NTLM)
        test_setopt(curl, lcurl.CURLOPT_USERPWD,
                          user_login.encode("utf-8") if user_login else None)

        for count in range(2):
            res = lcurl.easy_perform(curl)

            usedauth = ct.c_long(0)
            res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_HTTPAUTH_USED,
                                     ct.byref(usedauth))
            if usedauth.value != lcurl.CURLAUTH_NTLM:
                print("CURLINFO_HTTPAUTH_USED did not say NTLM")

            # set a new URL for the second, so that we don't restart NTLM
            test_setopt(curl, lcurl.CURLOPT_URL, URL1.encode("utf-8"))

            if res: break

    return res
