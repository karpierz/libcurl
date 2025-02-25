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


bl_servers = (ct.c_char_p * 3)(
    b"Microsoft-IIS/6.0",
    b"nginx/0.8.54",
    None
)

bl_sites = (ct.c_char_p * 3)(
    b"curl.se:443",
    b"example.com:80",
    None
)


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    multi: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    with curl_guard(True, mcurl=multi) as guard:

        lcurl.multi_setopt(multi, lcurl.CURLMOPT_PIPELINING_SERVER_BL, bl_servers)
        lcurl.multi_setopt(multi, lcurl.CURLMOPT_PIPELINING_SITE_BL,   bl_sites)

    return res
