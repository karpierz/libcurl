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

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)  # show verbose for debug
        test_setopt(curl, lcurl.CURLOPT_HEADER,  1)  # include header

        if defined("LIB584"):
            mime: ct.POINTER(lcurl.mime)     = lcurl.mime_init(curl)
            part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
            lcurl.mime_name(part, b"fake");
            lcurl.mime_data(part, ct.cast(b"party", ct.POINTER(ct.c_ubyte)), 5)
            test_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)

            res = lcurl.easy_perform(curl)

            lcurl.mime_free(mime)
            del mime, part
        # endif

        if res != lcurl.CURLE_OK: raise guard.Break

        test_setopt(curl, lcurl.CURLOPT_MIMEPOST, None)

        # Now, we should be making a zero byte POST request
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
