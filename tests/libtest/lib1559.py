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


EXCESSIVE = 10 * 1000 * 1000
#EXCESSIVE = 8 * 1000 * 1000


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    long_url = ct.create_string_buffer(EXCESSIVE)
    if not long_url:
        return lcurl.CURLcode(1).value
    ct.memset(long_url, ord(b'a'), EXCESSIVE)
    long_url[EXCESSIVE - 1] = b'\0'

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        res = lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, long_url)
        print("CURLOPT_URL %d bytes URL == %d" % (EXCESSIVE, res))

        res = lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, long_url)
        print("CURLOPT_POSTFIELDS %d bytes data == %d" % (EXCESSIVE, res))

        u: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not u: return int(res)

        uc: lcurl.CURLUcode = lcurl.url_set(u, lcurl.CURLUPART_URL, long_url, 0)
        print("CURLUPART_URL %d bytes URL == %d (%s)" %
              (EXCESSIVE, uc, lcurl.url_strerror(uc).decode("utf-8")))
        uc = lcurl.url_set(u, lcurl.CURLUPART_SCHEME, long_url,
                              lcurl.CURLU_NON_SUPPORT_SCHEME)
        print("CURLUPART_SCHEME %d bytes scheme == %d (%s)" %
              (EXCESSIVE, uc, lcurl.url_strerror(uc).decode("utf-8")))
        uc = lcurl.url_set(u, lcurl.CURLUPART_USER, long_url, 0)
        print("CURLUPART_USER %d bytes user == %d (%s)" %
              (EXCESSIVE, uc, lcurl.url_strerror(uc).decode("utf-8")))

        lcurl.url_cleanup(u)

    return res  # return the final return code
