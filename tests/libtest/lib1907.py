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

    error_buffer = (ct.c_char * lcurl.CURL_ERROR_SIZE)(b"\0")

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_ERRORBUFFER, error_buffer)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(curl)
        if res == lcurl.CURLE_OK:
            print("failure expected, "
                  "libcurl.easy_perform() returned %ld: <%s>, <%s>" %
                  (res, lcurl.easy_strerror(res).decode("utf-8"),
                   error_buffer.raw.decode("utf-8")), file=sys.stderr)

        # print the used url
        url_after = ct.c_char_p()
        if not lcurl.easy_getinfo(curl, lcurl.CURLINFO_EFFECTIVE_URL,
                                  ct.byref(url_after)):
            print("Effective URL: %s" % url_after.value.decode("utf-8"))

    return res
