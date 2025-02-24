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


testdata = b"dummy"


class WriteThis(ct.Structure):
    _fields_ = [
    ("readptr",  ct.POINTER(ct.c_ubyte)),
    ("sizeleft", lcurl.off_t),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    eof = (not pooh.readptr[0])
    if buffer_size < 1: return 0
    if pooh.sizeleft <= 0: return 0  # no more data left to deliver
    buffer[0] = pooh.readptr[0]  # copy one single byte
    c_ptr_iadd(pooh.readptr, 1)  # advance pointer
    pooh.sizeleft -= 1           # less data left
    return 1                     # we return 1 byte at a time!


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = TEST_ERR_FAILURE

    pooh = WriteThis()

    # Check proper handling of mime encoder feature when the part read callback
    # delivers data bytes one at a time. Use chunked encoding for accurate test.

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # Prepare the callback structure.
        pooh.readptr  = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
        pooh.sizeleft = len(testdata)

        # Build the mime tree.
        mime: ct.POINTER(lcurl.mime)     = lcurl.mime_init(curl)
        guard.add_mime(mime)
        part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
        lcurl.mime_name(part, b"field")
        lcurl.mime_encoder(part, b"base64")
        # Using an undefined length forces chunked transfer.
        lcurl.mime_data_cb(part, -1, read_callback,
                           lcurl.seek_callback(0), lcurl.free_callback(0),
                           ct.byref(pooh))

        # Bind mime data to its easy handle.
        test_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)

        # Send data.
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() failed", file=sys.stderr)
            raise guard.Break

    return res
