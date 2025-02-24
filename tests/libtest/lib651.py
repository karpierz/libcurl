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


testbuf = (ct.c_char * 17000)()  # more than 16K


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    # create a buffer with AAAA...BBBBB...CCCC...etc
    size: int = ct.sizeof(testbuf) // 1000
    for i in range(size):
        ct.memset(ct.byref(testbuf, i * 1000), ord('A') + i, 1000)
    testbuf[ct.sizeof(testbuf) - 1] = 0  # null-terminate

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        formrc: lcurl.CURLFORMcode
        formpost: ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()
        lastptr:  ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()

        # CURL_IGNORE_DEPRECATION(
        # Check proper name and data copying.
        fields = (lcurl.forms * 3)()
        fields[0].option = lcurl.CURLFORM_COPYNAME
        fields[0].value  = b"hello"
        fields[1].option = lcurl.CURLFORM_COPYCONTENTS
        fields[1].value  = ct.cast(testbuf, ct.c_char_p)
        fields[2].option = lcurl.CURLFORM_END
        formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
        # )
        if formrc:
            print("libcurl.formadd(1) = %d" % formrc)

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # CURL_IGNORE_DEPRECATION(
        # send a multi-part formpost
        test_setopt(curl, lcurl.CURLOPT_HTTPPOST, formpost)
        # )
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

        # test_cleanup:

        # always cleanup
        # CURL_IGNORE_DEPRECATION(
        # now cleanup the formpost chain
        lcurl.formfree(formpost)
        # )

    return res
