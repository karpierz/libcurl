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

# The size of data should be kept below MAX_INITIAL_POST_SIZE!
testdata: bytes = b"this is a short string.\n"
data_size: int = len(testdata) // ct.sizeof(ct.c_char)


@lcurl.progress_callback
def progress_callback(clientp, dltotal, dlnow, ultotal, ulnow):
    global file_name
    try:
        moo = open(file_name, "wb")
    except: pass
    else:
        with moo:
            if int(ultotal) == data_size and int(ulnow) == data_size:
                moo.write(b"PASSED, UL data matched data size\n")
            else:
                moo.write(b"Progress callback called with UL %f out of %f\n" %
                          (ulnow, ultotal))
    return 0


@curl_test_decorator
def test(URL: str, filename: str) -> lcurl.CURLcode:
    filename = str(filename)

    global file_name
    file_name = filename

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # Now specify we want to POST data
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        # Set the expected POST size
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, data_size)
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDS, testdata)
        # we want to use our own progress function
        # CURL_IGNORE_DEPRECATION(
        test_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        test_setopt(curl, lcurl.CURLOPT_PROGRESSFUNCTION, progress_callback)
        # )
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
