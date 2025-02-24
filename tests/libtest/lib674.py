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
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode  = lcurl.CURLE_OK
    uc:  lcurl.CURLUcode = lcurl.CURLUE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    handle: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, handle):
        if not handle: return TEST_ERR_EASY_INIT

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            print("problem init URL api.", file=sys.stderr)
            return int(res)

        uc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, URL.encode("utf-8"), 0)
        if uc:
            print("problem setting libcurl.CURLUPART_URL: %s." %
                  lcurl.url_strerror(uc).decode("utf-8"), file=sys.stderr)
            goto(test_cleanup)

        # demonstrate override behavior

        easy_setopt(handle, lcurl.CURLOPT_CURLU, urlp)
        easy_setopt(handle, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(handle)
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_perform() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            goto(test_cleanup)

        handle2: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(handle)
        res = lcurl.easy_perform(handle2)
        lcurl.easy_cleanup(handle2)

        # test_cleanup:

        lcurl.url_cleanup(urlp)

    return res
