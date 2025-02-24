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

    curlm: ct.POINTER(lcurl.CURLM) = multi_init()
    curl1: ct.POINTER(lcurl.CURL)  = easy_init()
    curl2: ct.POINTER(lcurl.CURL)  = easy_init()

    with curl_guard(True, [curl1, curl2], curlm):
        if not curl1: return TEST_ERR_EASY_INIT
        if not curl2: return TEST_ERR_EASY_INIT

        multi_setopt(curlm, lcurl.CURLMOPT_MAX_HOST_CONNECTIONS, 1)

        easy_setopt(curl1, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        multi_add_handle(curlm, curl1)
        easy_setopt(curl2, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        multi_add_handle(curlm, curl2)

        running_handles = ct.c_int(0)
        multi_perform(curlm, ct.byref(running_handles))
        running_handles = running_handles.value

    return res
