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

WITH_PROXY = "http://usingproxy.com/"


def proxystat(curl: ct.POINTER(lcurl.CURL)):
    wasproxy = ct.c_long()
    if lcurl.easy_getinfo(curl, lcurl.CURLINFO_USED_PROXY,
                          ct.byref(wasproxy)) == lcurl.CURLE_OK:
        wasproxy = wasproxy.value
        print("This %s the proxy" % ("used" if wasproxy else "DID NOT use"))


@curl_test_decorator
def test(URL: str, without_proxy: str, host: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        hosts: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                            host.encode("utf-8"))
        if not hosts: return res
        guard.add_slist(hosts)

        test_setopt(curl, lcurl.CURLOPT_RESOLVE, hosts)
        test_setopt(curl, lcurl.CURLOPT_PROXY, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_URL, WITH_PROXY.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_NOPROXY, b"goingdirect.com")
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        proxystat(curl)

        test_setopt(curl, lcurl.CURLOPT_URL, without_proxy.encode("utf-8"))

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        proxystat(curl)

    return res
