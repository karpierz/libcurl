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

        mime:  ct.POINTER(lcurl.mime)     = lcurl.mime_init(curl)
        field: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
        lcurl.mime_name(field, b"name")
        lcurl.mime_data(field, ct.cast(b"short value",
                                       ct.POINTER(ct.c_ubyte)),
                        lcurl.CURL_ZERO_TERMINATED)

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)
        easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)

        res = lcurl.easy_perform(curl)
        if res == lcurl.CURLE_OK:
            # Alter form and resubmit.
            lcurl.mime_data(field, ct.cast(b"long value for length change",
                                           ct.POINTER(ct.c_ubyte)),
                            lcurl.CURL_ZERO_TERMINATED)

            res = lcurl.easy_perform(curl)

        lcurl.mime_free(mime)

    return res  # return the final return code
