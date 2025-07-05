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
def test(URL: str, host: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = TEST_ERR_MAJOR_BAD

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        test_setopt(curl, lcurl.CURLOPT_INFILESIZE, 0)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_AWS_SIGV4, b"aws:amz:us-east-1:s3")
        test_setopt(curl, lcurl.CURLOPT_USERPWD, b"xxx")
        test_setopt(curl, lcurl.CURLOPT_HEADER, 0)

        # We want to test a couple assumptions here.
        # 1. the merging works with non-adjacent headers
        # 2. the merging works across multiple duplicate headers
        # 3. the merging works if a duplicate header has no colon
        # 4. the merging works if the headers are cased differently
        # 5. the merging works across multiple duplicate headers
        # 6. the merging works across multiple duplicate headers with the
        #    same value
        # 7. merging works for headers all with no values
        # 8. merging works for headers some with no values

        http_headers: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                      b"x-amz-meta-test: test2")
        guard.add_slist(http_headers)
        lcurl.slist_append(http_headers, b"some-other-header: value")
        lcurl.slist_append(http_headers, b"x-amz-meta-test: test1")
        lcurl.slist_append(http_headers, b"duplicate-header: duplicate")
        lcurl.slist_append(http_headers, b"header-no-value")
        lcurl.slist_append(http_headers, b"x-amz-meta-test: test3")
        lcurl.slist_append(http_headers, b"X-amz-meta-test2: test2")
        lcurl.slist_append(http_headers, b"x-amz-meta-blah: blah")
        lcurl.slist_append(http_headers, b"x-Amz-meta-test2: test1")
        lcurl.slist_append(http_headers, b"x-amz-Meta-test2: test3")
        lcurl.slist_append(http_headers, b"curr-header-no-colon")
        lcurl.slist_append(http_headers, b"curr-header-no-colon: value")
        lcurl.slist_append(http_headers, b"next-header-no-colon: value")
        lcurl.slist_append(http_headers, b"next-header-no-colon")
        lcurl.slist_append(http_headers, b"duplicate-header: duplicate")
        lcurl.slist_append(http_headers, b"header-no-value;")
        lcurl.slist_append(http_headers, b"header-no-value;")
        lcurl.slist_append(http_headers, b"header-some-no-value;")
        lcurl.slist_append(http_headers, b"header-some-no-value: value")
        test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, http_headers)

        connect_to: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
        if host:
            connect_to = lcurl.slist_append(connect_to, host.encode("utf-8"))
        guard.add_slist(connect_to)
        test_setopt(curl, lcurl.CURLOPT_CONNECT_TO, connect_to)

        res = lcurl.easy_perform(curl)

    return res
