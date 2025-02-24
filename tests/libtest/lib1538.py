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

    lcurl.easy_strerror(INT_MAX)
    lcurl.multi_strerror(INT_MAX)
    lcurl.share_strerror(INT_MAX)
    lcurl.url_strerror(INT_MAX)
    lcurl.easy_strerror(-INT_MAX)
    lcurl.multi_strerror(-INT_MAX)
    lcurl.share_strerror(-INT_MAX)
    lcurl.url_strerror(-INT_MAX)

    for easyret in range(lcurl.CURLE_OK, lcurl.CURL_LAST + 1):
        print("e%d: %s" % (easyret, lcurl.easy_strerror(easyret).decode("utf-8")))
    for multiret in range(lcurl.CURLM_CALL_MULTI_PERFORM, lcurl.CURLM_LAST + 1):
        print("m%d: %s" % (multiret, lcurl.multi_strerror(multiret).decode("utf-8")))
    for shareret in range(lcurl.CURLSHE_OK, lcurl.CURLSHE_LAST + 1):
        print("s%d: %s" % (shareret, lcurl.share_strerror(shareret).decode("utf-8")))
    for urlret in range(lcurl.CURLUE_OK, lcurl.CURLUE_LAST + 1):
        print("u%d: %s" % (urlret, lcurl.url_strerror(urlret).decode("utf-8")))

    return res
