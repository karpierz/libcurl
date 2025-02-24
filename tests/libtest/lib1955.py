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


@curl_test_decorator
def test(URL: str,
         user_login: str = "xxx",
         AWS_login:  str = "xxx") -> lcurl.CURLcode:

    res: lcurl.CURLcode = TEST_ERR_MAJOR_BAD

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_AWS_SIGV4,
                          AWS_login.encode("utf-8") if AWS_login else None)
        test_setopt(curl, lcurl.CURLOPT_USERPWD,
                          user_login.encode("utf-8") if user_login else None)
        test_setopt(curl, lcurl.CURLOPT_HEADER, 0)
        list: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                              b"test3: 1234")
        if not list: return res
        guard.add_slist(list)

        lcurl.slist_append(list, b"Content-Type: application/json")

        # 'name;' user headers with no value are used to send an empty header in the
        # format 'name:' (note the semi-colon becomes a colon). this entry should
        # show in SignedHeaders without an additional semi-colon, as any other
        # header would. eg 'foo;test2;test3' and not 'foo;test2;;test3'.
        lcurl.slist_append(list, b"test2;")

        # 'name:' user headers with no value are used to signal an internal header
        # of that name should be removed and are not sent as a header. this entry
        # should not show in SignedHeaders.
        lcurl.slist_append(list, b"test1:")

        # 'name' user headers with no separator or value are invalid and ignored.
        # this entry should not show in SignedHeaders.
        lcurl.slist_append(list, b"test0")

        lcurl.slist_append(list, b"test_space: t\ts  m\t   end    ")
        lcurl.slist_append(list, b"tesMixCase: MixCase")
        test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, list)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
