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
# Testing libcurl.CURLINFO_FILETIME
#


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # Test that a filetime is properly initialized on libcurl.easy_init.

        filetime = ct.c_long(-1)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_FILETIME, ct.byref(filetime))
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_getinfo() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break
        if filetime.value != -1:
            print("%s:%d filetime init failed; expected -1 but is %ld" %
                  (current_file(), current_line(), filetime.value), file=sys.stderr)
            res = lcurl.CURLE_FAILED_INIT
            raise guard.Break

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_FILETIME, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_perform() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break

        # Test that a filetime is properly set after receiving an HTTP resource.

        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_FILETIME, ct.byref(filetime))
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_getinfo() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break
        if filetime.value != 30:
            print("%s:%d filetime of http resource is incorrect; "
                  "expected 30 but is %ld" %
                  (current_file(), current_line(), filetime.value), file=sys.stderr)
            res = lcurl.CURLE_HTTP_RETURNED_ERROR
            raise guard.Break

        # Test that a filetime is properly initialized on curl_easy_duphandle.

        dupe: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(curl)
        if not dupe:
            print("%s:%d libcurl.easy_duphandle() failed" %
                  (current_file(), current_line()), file=sys.stderr)
            res = lcurl.CURLE_FAILED_INIT
            raise guard.Break
        guard.add_curl(dupe)

        res = lcurl.easy_getinfo(dupe, lcurl.CURLINFO_FILETIME, ct.byref(filetime))
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_getinfo() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break
        if filetime.value != -1:
            print("%s:%d filetime init failed; expected -1 but is %ld" %
                  (current_file(), current_line(), filetime.value), file=sys.stderr)
            res = lcurl.CURLE_FAILED_INIT
            raise guard.Break

        # Test that a filetime is properly initialized on curl_easy_reset.

        lcurl.easy_reset(curl)

        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_FILETIME, ct.byref(filetime))
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_getinfo() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break
        if filetime.value != -1:
            print("%s:%d filetime init failed; expected -1 but is %ld" %
                  (current_file(), current_line(), filetime.value), file=sys.stderr)
            res = lcurl.CURLE_FAILED_INIT
            raise guard.Break

    return res
