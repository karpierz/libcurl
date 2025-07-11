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

import time
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa


testdata = b"this is what we post to the silly web server\n"


class WriteThis(ct.Structure):
    _fields_ = [
    ("readptr",  ct.POINTER(ct.c_ubyte)),
    ("sizeleft", ct.c_size_t),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    # Wait one second before return POST data
    # so libcurl will wait before sending request body
    time.sleep(1)
    tocopy = nitems * size
    if tocopy <= 0:
        return 0  # pragma: no cover
    if pooh.sizeleft == 0:
        return 0  # pragma: no cover
    tocopy = min(pooh.sizeleft, tocopy)
    ct.memmove(buffer, pooh.readptr, tocopy)  # copy requested data
    c_ptr_iadd(pooh.readptr, tocopy)          # advance pointer
    pooh.sizeleft -= tocopy                   # less data left
    return tocopy


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if URL == "check":

        if is_windows:
            print("Windows TCP does not deliver response data but reports "
                  "CONNABORTED")
            return TEST_ERR_FAILURE  # skip since it fails on Windows without
                                     # workaround
        else:  # pragma: no cover
            return lcurl.CURLE_OK  # sure, run this!

    pooh = WriteThis()
    pooh.readptr  = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
    pooh.sizeleft = len(testdata)

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
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, pooh.sizeleft)
        # we want to use our own read function
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        # pointer to pass to our read function
        test_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(pooh))
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # detect HTTP error codes >= 400
        # test_setopt(curl, lcurl.CURLOPT_FAILONERROR, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
