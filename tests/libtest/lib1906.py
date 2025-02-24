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

    curlu: ct.POINTER(lcurl.CURLU) = lcurl.url()
    error_buffer = (ct.c_char * lcurl.CURL_ERROR_SIZE)(b"\0")

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.url_set(curlu, lcurl.CURLUPART_URL, URL.encode("utf-8"),
                      lcurl.CURLU_DEFAULT_SCHEME)
        easy_setopt(curl, lcurl.CURLOPT_CURLU, curlu)
        easy_setopt(curl, lcurl.CURLOPT_ERRORBUFFER, error_buffer)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # msys2 times out instead of CURLE_COULDNT_CONNECT, so make it faster
        easy_setopt(curl, lcurl.CURLOPT_CONNECTTIMEOUT_MS, 5000)

        # set a port number that makes this request fail
        easy_setopt(curl, lcurl.CURLOPT_PORT, 1)

        res = lcurl.easy_perform(curl)
        if res not in (lcurl.CURLE_COULDNT_CONNECT,
                       lcurl.CURLE_OPERATION_TIMEDOUT):
            print("failure expected, "
                  "libcurl.easy_perform() returned %d: <%s>, <%s>" %
                  (res, lcurl.easy_strerror(res).decode("utf-8"),
                   error_buffer.raw.decode("utf-8")), file=sys.stderr)
            if res == lcurl.CURLE_OK: res = TEST_ERR_MAJOR_BAD  # force an error return
        else:
            res = lcurl.CURLE_OK  # reset for next use

            # print the used url
            url_after = ct.c_char_p()
            lcurl.url_get(curlu, lcurl.CURLUPART_URL, ct.byref(url_after), 0)
            print("curlu now: <%s>" % url_after.value.decode("utf-8"),
                  file=sys.stderr)
            lcurl.free(url_after) ; url_after = None

            # now reset libcurl.CURLOP_PORT to go back to originally set port number
            easy_setopt(curl, lcurl.CURLOPT_PORT, 0)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK:
                print("success expected, "
                      "libcurl.easy_perform() returned %d: <%s>, <%s>" %
                      (res, lcurl.easy_strerror(res).decode("utf-8"),
                       error_buffer.raw.decode("utf-8")), file=sys.stderr)

            # print url
            url_after = ct.c_char_p()
            lcurl.url_get(curlu, lcurl.CURLUPART_URL, ct.byref(url_after), 0)
            print("curlu now: <%s>" % url_after.value.decode("utf-8"),
                  file=sys.stderr)
            lcurl.free(url_after) ; url_after = None

        lcurl.url_cleanup(curlu)

    return res
