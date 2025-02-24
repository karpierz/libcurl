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

NUM_URLS = 4


@curl_test_decorator
def test(URL: str, address: str, port: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    slist: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
    # Create fake DNS entries for serverX.example.com for all handles
    for i in range(NUM_URLS):
        dns_entry: str = "server%d.example.com:%s:%s" % (
                         i + 1, port, address)
        print("%s" % dns_entry)
        slist2: ct.POINTER(lcurl.slist) = lcurl.slist_append(slist,
                                                dns_entry.encode("utf-8"))
        if not slist2:
            print("libcurl.slist_append() failed", file=sys.stderr)
            lcurl.slist_free_all(slist)
            return 1  # !!! use proper error !!!
        slist = slist2

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        lcurl.slist_free_all(slist)
        return TEST_ERR_MAJOR_BAD

    # get an easy handle
    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        guard.add_slist(slist)
        if not curl: return TEST_ERR_EASY_INIT

        # go verbose
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_RESOLVE, slist)
        easy_setopt(curl, lcurl.CURLOPT_MAXCONNECTS, 3)

        # get NUM_HANDLES easy handles
        for i in range(NUM_URLS):
            # specify target
            target_url = "http://server%d.example.com:%s/path/1510%04i" % (
                         i + 1, port, i + 1)
            easy_setopt(curl, lcurl.CURLOPT_URL, target_url.encode("utf-8"))

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            abort_on_test_timeout()

    return res
