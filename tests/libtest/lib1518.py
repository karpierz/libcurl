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

# Test inspired by github issue 3340


@lcurl.write_callback
def write_callback(buffer, size, nitems, stream):
    return 0


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        if defined("LIB1543"):
            # set libcurl.CURLOPT_URLU
            rc: lcurl.CURLUcode = lcurl.CURLUE_OK
            urlu: ct.POINTER(lcurl.CURLU) = lcurl.url()
            if urlu:
                rc = lcurl.url_set(urlu, lcurl.CURLUPART_URL, URL.encode("utf-8"),
                                   lcurl.CURLU_ALLOW_SPACE)
            if not urlu or rc:
                goto(test_cleanup)
            test_setopt(curl, lcurl.CURLOPT_CURLU, urlu)
            test_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
        else:
            test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # just to make it explicit and visible in this test:
            test_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 0)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

        curlResponseCode  = ct.c_long()
        curlRedirectCount = ct.c_long()
        effectiveUrl = ct.c_char_p(None)
        redirectUrl  = ct.c_char_p(None)
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_RESPONSE_CODE,  ct.byref(curlResponseCode))
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_REDIRECT_COUNT, ct.byref(curlRedirectCount))
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_EFFECTIVE_URL,  ct.byref(effectiveUrl))
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_REDIRECT_URL,   ct.byref(redirectUrl))

        if lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback) == lcurl.CURLE_OK:
            print("res %d\n"
                  "status %ld\n"
                  "redirects %ld\n"
                  "effectiveurl %s\n"
                  "redirecturl %s" % (
                  res,
                  curlResponseCode.value,
                  curlRedirectCount.value,
                  effectiveUrl.value.decode("utf-8"),
                  redirectUrl.value.decode("utf-8") if redirectUrl else "blank"))

        # test_cleanup:

        # always cleanup
        if defined("LIB1543"):
            lcurl.url_cleanup(urlu)

    return res
