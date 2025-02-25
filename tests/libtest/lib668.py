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
    data_size = min(strlen(pooh.readptr), buffer_size)
    if data_size == 0: return 0
    ct.memmove(buffer, pooh.readptr, data_size)
    c_ptr_iadd(pooh.readptr, data_size)
    return data_size


@curl_test_decorator
def test(URL: str, mime_file: str) -> lcurl.CURLcode:
    mime_file = str(mime_file)

    res: lcurl.CURLcode = TEST_ERR_FAILURE

    mime: ct.POINTER(lcurl.mime) = ct.POINTER(lcurl.mime)()
    part: ct.POINTER(lcurl.mimepart)
    pooh1 = WriteThis()
    pooh2 = WriteThis()

    #
    # Check early end of part data detection.
    #

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

        # Prepare the callback structures.
        pooh1.readptr  = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
        pooh1.sizeleft = len(testdata)
        pooh2.readptr  = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
        pooh2.sizeleft = len(testdata)

        # Build the mime tree.
        mime = lcurl.mime_init(curl)
        guard.add_mime(mime)

        part = lcurl.mime_addpart(mime)
        lcurl.mime_name(part, b"field1")
        # Early end of data detection can be done because the data size is known.
        lcurl.mime_data_cb(part, len(testdata), read_callback,
                           lcurl.seek_callback(0), lcurl.free_callback(0),
                           ct.byref(pooh1))
        part = lcurl.mime_addpart(mime)
        lcurl.mime_name(part, b"field2")
        # Using an undefined length forces chunked transfer and disables early
        # end of data detection for this part.
        lcurl.mime_data_cb(part, -1, read_callback,
                           lcurl.seek_callback(0), lcurl.free_callback(0),
                           ct.byref(pooh2))
        part = lcurl.mime_addpart(mime)
        lcurl.mime_name(part, b"field3")
        # Regular file part sources early end of data can be detected because
        # the file size is known. In addition, and EOF test is performed.
        lcurl.mime_filedata(part, mime_file.encode("utf-8"))

        # Bind mime data to its easy handle.
        test_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)

        # Send data.
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() failed", file=sys.stderr)
            raise guard.Break

    return res
