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
# Get a single URL without select().
#


@curl_test_decorator
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            print("problem init URL api.", file=sys.stderr)
            return int(res)

        # this doesn't set the PATH part
        if (lcurl.url_set(urlp, lcurl.CURLUPART_HOST, b"www.example.com", 0) or
            lcurl.url_set(urlp, lcurl.CURLUPART_SCHEME, b"http", 0) or
            lcurl.url_set(urlp, lcurl.CURLUPART_PORT, b"80", 0)):
            print("problem setting libcurl.CURLUPART", file=sys.stderr)
            goto(test_cleanup)

        easy_setopt(curl, lcurl.CURLOPT_CURLU, urlp)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_perform() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            goto(test_cleanup)

        # test_cleanup:

        lcurl.url_cleanup(urlp)

    return res
