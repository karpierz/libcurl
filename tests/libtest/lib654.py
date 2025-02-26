# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 1998 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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

testdata = b"dummy\n"


class WriteThis(ct.Structure):
    _fields_ = [
    ("readptr",   ct.POINTER(ct.c_ubyte)),
    ("sizeleft",  lcurl.off_t),
    ("freecount", ct.c_int),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    if buffer_size < 1: return 0
    if pooh.sizeleft <= 0: return 0  # no more data left to deliver
    buffer[0] = pooh.readptr[0]  # copy one single byte
    c_ptr_iadd(pooh.readptr, 1)  # advance pointer
    pooh.sizeleft -= 1           # less data left
    return 1                     # we return 1 byte at a time!


@lcurl.free_callback
def free_callback(ptr):
    pooh = ct.cast(ptr, ct.POINTER(WriteThis)).contents
    pooh.freecount += 1


@curl_test_decorator
def test(URL: str, mime_file: str) -> lcurl.CURLcode:
    mime_file = str(mime_file)

    res: lcurl.CURLcode = TEST_ERR_FAILURE

    # Prepare the callback structure.
    pooh = WriteThis()
    pooh.readptr   = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
    pooh.sizeleft  = len(testdata)
    pooh.freecount = 0

    # Check proper copy/release of mime post data bound to a duplicated
    # easy handle.

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    easy: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, easy) as guard:
        if not easy: return TEST_ERR_MAJOR_BAD

        # First set the URL that is about to receive our POST.
        test_setopt(easy, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # get verbose debug output please
        test_setopt(easy, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(easy, lcurl.CURLOPT_HEADER, 1)

        # Build the mime tree.
        mime: ct.POINTER(lcurl.mime) = lcurl.mime_init(easy)
        # guard.add_mime(mime)  # !!! <AK>: commented, because hang while guard exits

        part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
        lcurl.mime_data(part, ct.cast(b"hello", ct.POINTER(ct.c_ubyte)),
                              lcurl.CURL_ZERO_TERMINATED)
        lcurl.mime_name(part, b"greeting")
        lcurl.mime_type(part, b"application/X-Greeting")
        lcurl.mime_encoder(part, b"base64")
        hdrs: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                              b"X-Test-Number: 654")
        lcurl.mime_headers(part, hdrs, True)

        part = lcurl.mime_addpart(mime)
        lcurl.mime_filedata(part, mime_file.encode("utf-8"))

        part = lcurl.mime_addpart(mime)
        lcurl.mime_data_cb(part, -1,
                           read_callback, lcurl.seek_callback(0), free_callback,
                           ct.byref(pooh))

        # Bind mime data to its easy handle.
        test_setopt(easy, lcurl.CURLOPT_MIMEPOST, mime)

        # Duplicate the handle.
        easy2: ct.POINTER(lcurl.CURL) = lcurl.easy_duphandle(easy)
        if not easy2:
            print("libcurl.easy_duphandle() failed", file=sys.stderr)
            res = TEST_ERR_FAILURE
            raise guard.Break
        guard.add_curl(easy2)

        # Now free the mime structure: it should unbind it from the first
        # easy handle.
        lcurl.mime_free(mime)
        mime = ct.POINTER(lcurl.mime)()  # Already cleaned up.

        # Perform on the first handle: should not send any data.
        res = lcurl.easy_perform(easy)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform(original) failed", file=sys.stderr)
            raise guard.Break

        # Perform on the second handle: if the bound mime structure has not been
        # duplicated properly, it should cause a valgrind error.
        res = lcurl.easy_perform(easy2)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform(duplicated) failed", file=sys.stderr)
            raise guard.Break

        # Free the duplicated handle: it should call free_callback again.
        # If the mime copy was bad or not automatically released, valgrind
        # will signal it.
        guard.free_curl(easy2)
        easy2 = ct.POINTER(lcurl.CURL)()  # Already cleaned up.

        if pooh.freecount != 2:
            print("free_callback() called %d times instead of 2" %
                  pooh.freecount, file=sys.stderr)
            res = TEST_ERR_FAILURE
            raise guard.Break

        lcurl.easy_cleanup(easy2)

    return res
