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
# test case and code based on https://github.com/curl/curl/issues/3927
#


@lcurl.xferinfo_callback
def dload_progress_cb(clientp, dltotal, dlnow, ultotal, ulnow):
    return 0


def run(curl: ct.POINTER(lcurl.CURL), limit: int, time: int) -> lcurl.CURLcode:
    lcurl.easy_setopt(curl, lcurl.CURLOPT_LOW_SPEED_LIMIT, limit)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_LOW_SPEED_TIME,  time)
    return lcurl.easy_perform(curl)


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    ret: lcurl.CURLcode

    error_buffer = (ct.c_char * lcurl.CURL_ERROR_SIZE)()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # this example just ignores the content of downloaded data
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_skipped)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_ERRORBUFFER, error_buffer)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_XFERINFOFUNCTION, dload_progress_cb)

        ret = run(curl, 1, 2)
        if ret:
            print("error %d: %s" %
                  (ret, error_buffer.raw.decode("utf-8")), file=sys.stderr)

        ret = run(curl, 12000, 1)
        if ret and ret != lcurl.CURLE_OPERATION_TIMEDOUT:
            print("error %d: %s" %
                  (ret, error_buffer.raw.decode("utf-8")), file=sys.stderr)
        else:
            ret = lcurl.CURLE_OK

    return ret
