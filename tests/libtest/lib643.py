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


testdata = b"dummy\n"


class WriteThis(ct.Structure):
    _fields_ = [
    ("readptr",  ct.POINTER(ct.c_ubyte)),
    ("sizeleft", lcurl.off_t),
]


count: int = 0

@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    if buffer_size <= 0:
        return 0  # pragma: no cover
    if pooh.sizeleft <= 0:  # no more data left to deliver
        return 0  # pragma: no cover
    pooh.sizeleft -= 1
    buffer[0] = pooh.readptr[0]  # copy one single byte
    c_ptr_iadd(pooh.readptr, 1)  # advance pointer
    return 1                     # we return 1 byte at a time!


def test_once(URL: str, oldstyle: bool) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    pooh  = WriteThis()
    pooh2 = WriteThis()
    datasize = lcurl.off_t(-1).value

    pooh.readptr = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
    datasize = len(testdata)
    pooh.sizeleft = datasize

    curl: ct.POINTER(lcurl.CURL) = easy_init()
    if not curl:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(False, curl) as guard:

        mime: ct.POINTER(lcurl.mime) = lcurl.mime_init(curl)
        if not mime:  # pragma: no cover
            print("libcurl.mime_init() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD
        guard.add_mime(mime)

        part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
        if not part:  # pragma: no cover
            print("libcurl.mime_addpart(1) failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        # Fill in the file upload part
        if oldstyle:
            res = lcurl.mime_name(part, b"sendfile")
            if not res:  # pragma: no branch
                res = lcurl.mime_data_cb(part, datasize, read_callback,
                                         lcurl.seek_callback(0), lcurl.free_callback(0),
                                         ct.byref(pooh))
            if not res:  # pragma: no branch
                res = lcurl.mime_filename(part, b"postit2.c")
        else:
            # new style
            res = lcurl.mime_name(part, b"sendfile alternative")
            if not res:  # pragma: no branch
                res = lcurl.mime_data_cb(part, datasize, read_callback,
                                         lcurl.seek_callback(0), lcurl.free_callback(0),
                                         ct.byref(pooh))
            if not res:  # pragma: no branch
                res = lcurl.mime_filename(part, b"file name 2")

        if res:  # pragma: no cover
            print("libcurl.mime_xxx(1) = %s" %
                  lcurl.easy_strerror(res).decode("utf-8"))

        # Now add the same data with another name and make it not look like
        # a file upload but still using the callback

        pooh2.readptr = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
        datasize = len(testdata)
        pooh2.sizeleft = datasize

        part = lcurl.mime_addpart(mime)
        if not part:  # pragma: no cover
            print("libcurl.mime_addpart(2) failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        # Fill in the file upload part
        res = lcurl.mime_name(part, b"callbackdata")
        if not res:  # pragma: no branch
            res = lcurl.mime_data_cb(part, datasize, read_callback,
                                     lcurl.seek_callback(0), lcurl.free_callback(0),
                                     ct.byref(pooh2))

        if res:  # pragma: no cover
            print("libcurl.mime_xxx(2) = %s" %
                  lcurl.easy_strerror(res).decode("utf-8"))

        part = lcurl.mime_addpart(mime)
        if not part:  # pragma: no cover
            print("libcurl.mime_addpart(3) failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        # Fill in the filename field
        res = lcurl.mime_name(part, b"filename")
        if not res:  # pragma: no branch
            res = lcurl.mime_string(part, b"postit2.c")

        if res:  # pragma: no cover
            print("libcurl.mime_xxx(3) = %s" %
                  lcurl.easy_strerror(res).decode("utf-8"))

        # Fill in a submit field too
        part = lcurl.mime_addpart(mime)
        if not part:  # pragma: no cover
            print("libcurl.mime_addpart(4) failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        res = lcurl.mime_name(part, b"submit")
        if not res:  # pragma: no branch
            res = lcurl.mime_string(part, b"send")

        if res:  # pragma: no cover
            print("libcurl.mime_xxx(4) = %s" %
                  lcurl.easy_strerror(res).decode("utf-8"))

        part = lcurl.mime_addpart(mime)
        if not part:  # pragma: no cover
            print("libcurl.mime_addpart(5) failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        res = lcurl.mime_name(part, b"somename")
        if not res:  # pragma: no branch
            res = lcurl.mime_filename(part, b"somefile.txt")
        if not res:  # pragma: no branch
            res = lcurl.mime_data(part, ct.cast(b"blah blah",
                                                ct.POINTER(ct.c_ubyte)), 9)
        if res:  # pragma: no cover
            print("libcurl.mime_xxx(5) = %s" %
                  lcurl.easy_strerror(res).decode("utf-8"))

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # send a multi-part mimepost
        test_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

    return res


def cyclic_add() -> lcurl.CURLcode:

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return TEST_ERR_MAJOR_BAD

        mime: ct.POINTER(lcurl.mime)     = lcurl.mime_init(curl)
        part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
        guard.add_mime(mime)
        a1: lcurl.CURLcode = lcurl.mime_subparts(part, mime)

        if a1 == lcurl.CURLE_BAD_FUNCTION_ARGUMENT:
            submime: ct.POINTER(lcurl.mime)     = lcurl.mime_init(curl)
            subpart: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(submime)
            lcurl.mime_subparts(part, submime)
            a1 = lcurl.mime_subparts(subpart, mime)

    if a1 != lcurl.CURLE_BAD_FUNCTION_ARGUMENT:  # pragma: no cover
        # that should have failed
        return TEST_ERR_FAILURE

    return lcurl.CURLE_OK


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        res = test_once(URL, True)  # old
        if res: raise guard.Break  # pragma: no cover

        res = test_once(URL, False)  # new
        if res: raise guard.Break  # pragma: no cover

        res = cyclic_add()

    return res
