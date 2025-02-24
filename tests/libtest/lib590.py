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

#  Based on a bug report recipe by Rene Bernhardt in
#  https://curl.se/mail/lib-2011-10/0323.html
#
#  It is reproducible by the following steps:
#
#  - Use a proxy that offers NTLM and Negotiate (libcurl.CURLOPT_PROXY and
#    libcurl.CURLOPT_PROXYPORT)
#  - Tell libcurl NOT to use Negotiate libcurl.CURL_EASY_SETOPT(CURLOPT_PROXYAUTH,
#    libcurl.CURLAUTH_BASIC | libcurl.CURLAUTH_DIGEST | libcurl.CURLAUTH_NTLM)
#  - Start the request


@curl_test_decorator
def test(URL: str,
         proxy: str = None,
         proxy_login: str = "me:password") -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        test_setopt(curl, lcurl.CURLOPT_PROXYAUTH,
                    lcurl.CURLAUTH_BASIC | lcurl.CURLAUTH_DIGEST | lcurl.CURLAUTH_NTLM)
        test_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)
        test_setopt(curl, lcurl.CURLOPT_PROXYUSERPWD,
                          proxy_login.encode("utf-8") if proxy_login else None)

        res = lcurl.easy_perform(curl)

        usedauth = ct.c_long(0)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_PROXYAUTH_USED, ct.byref(usedauth))
        usedauth = usedauth.value
        if usedauth != lcurl.CURLAUTH_NTLM:
            print("CURLINFO_PROXYAUTH_USED did not say NTLM")

    return res
