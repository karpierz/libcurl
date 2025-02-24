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

#
# Test libcurl.CURLINFO_RESPONSE_CODE
#


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    httpcode = ct.c_long()
    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_perform() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break

        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_RESPONSE_CODE, ct.byref(httpcode))
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_getinfo() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break
        if httpcode.value != 200:
            print("%s:%d unexpected response code %ld" %
                  (current_file(), current_line(), httpcode.value), file=sys.stderr)
            res = lcurl.CURLE_HTTP_RETURNED_ERROR
            raise guard.Break

        # Test for a regression of github bug 1017 (response code does not reset)
        lcurl.easy_reset(curl)

        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_RESPONSE_CODE, ct.byref(httpcode))
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_getinfo() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break
        if httpcode.value:
            print("%s:%d libcurl.easy_reset failed to zero the response code\n"
                  "possible regression of github bug 1017" %
                  (current_file(), current_line()), file=sys.stderr)
            res = lcurl.CURLE_HTTP_RETURNED_ERROR
            raise guard.Break

    return res
