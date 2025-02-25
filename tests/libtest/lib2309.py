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


@lcurl.write_callback
def cb_ignore(buffer, size, nitems, userp):
    return lcurl.CURL_WRITEFUNC_ERROR


@curl_test_decorator
def test(URL: str, netrc_file: str, proxy: str = None) -> lcurl.CURLcode:
    netrc_file = str(netrc_file)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, cb_ignore)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PROXY,
                                proxy.encode("utf-8") if proxy else None)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NETRC, lcurl.CURL_NETRC_REQUIRED)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NETRC_FILE, netrc_file.encode("utf-8"))

        curldupe: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(curl)
        if not curldupe:
            return TEST_ERR_EASY_INIT
        guard.add_curl(curldupe)

        res = lcurl.easy_perform(curldupe)

        print("Returned %d, should be %d." % (res, lcurl.CURLE_WRITE_ERROR))
        sys.stdout.flush()

    return lcurl.CURLE_OK
