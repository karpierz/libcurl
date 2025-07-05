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


testdata = b"this is what we post to the silly web server\n"


class WriteThis(ct.Structure):
    _fields_ = [
    ("readptr",  ct.POINTER(ct.c_ubyte)),
    ("sizeleft", ct.c_size_t),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    if buffer_size <= 0:
        return 0  # pragma: no cover
    if pooh.sizeleft == 0:       # no more data left to deliver
        return 0  # pragma: no cover
    buffer[0] = pooh.readptr[0]  # copy one single byte
    c_ptr_iadd(pooh.readptr, 1)  # advance pointer
    pooh.sizeleft -= 1           # less data left
    return 1                     # we return 1 byte at a time!


def test_once(URL: str, old_style: bool) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    pooh  = WriteThis()
    pooh2 = WriteThis()
    pooh.readptr  = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
    pooh.sizeleft = len(testdata)

    form_rc: lcurl.CURLFORMcode
    formpost: ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()
    lastptr:  ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()

    # Fill in the file upload field
    if old_style:
        fields = (lcurl.forms * 5)()
        fields[0].option = lcurl.CURLFORM_COPYNAME
        fields[0].value  = b"sendfile"
        fields[1].option = lcurl.CURLFORM_STREAM
        fields[1].value  = ct.cast(ct.pointer(pooh), ct.c_char_p)
        fields[2].option = lcurl.CURLFORM_CONTENTSLENGTH
        fields[2].value  = pooh.sizeleft
        fields[3].option = lcurl.CURLFORM_FILENAME
        fields[3].value  = b"postit2.c"
        fields[4].option = lcurl.CURLFORM_END
        form_rc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    else:
        # new style
        fields = (lcurl.forms * 5)()
        fields[0].option = lcurl.CURLFORM_COPYNAME
        fields[0].value  = b"sendfile alternative"
        fields[1].option = lcurl.CURLFORM_STREAM
        fields[1].value  = ct.cast(ct.pointer(pooh), ct.c_char_p)
        fields[2].option = lcurl.CURLFORM_CONTENTLEN
        fields[2].value  = pooh.sizeleft
        fields[3].option = lcurl.CURLFORM_FILENAME
        fields[3].value  = b"file name 2"
        fields[4].option = lcurl.CURLFORM_END
        form_rc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    if form_rc:
        print("libcurl.formadd(1) = %d" % form_rc)

    # Now add the same data with another name and make it not look like
    # a file upload but still using the callback

    pooh2.readptr  = ct.cast(testdata, ct.POINTER(ct.c_ubyte))
    pooh2.sizeleft = len(testdata)

    # Fill in the file upload field
    fields = (lcurl.forms * 4)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"callbackdata"
    fields[1].option = lcurl.CURLFORM_STREAM
    fields[1].value  = ct.cast(ct.pointer(pooh2), ct.c_char_p)
    fields[2].option = lcurl.CURLFORM_CONTENTSLENGTH
    fields[2].value  = pooh2.sizeleft
    fields[3].option = lcurl.CURLFORM_END
    form_rc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    if form_rc:
        print("libcurl.formadd(2) = %d" % form_rc)

    # Fill in the filename field
    fields = (lcurl.forms * 3)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"filename"
    fields[1].option = lcurl.CURLFORM_COPYCONTENTS
    fields[1].value  = b"postit2.c"
    fields[2].option = lcurl.CURLFORM_END
    form_rc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    if form_rc:
        print("libcurl.formadd(3) = %d" % form_rc)

    # Fill in a submit field too
    fields = (lcurl.forms * 4)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"submit"
    fields[1].option = lcurl.CURLFORM_COPYCONTENTS
    fields[1].value  = b"send"
    fields[2].option = lcurl.CURLFORM_CONTENTTYPE
    fields[2].value  = b"text/plain"
    fields[3].option = lcurl.CURLFORM_END
    form_rc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    if form_rc:
        print("libcurl.formadd(4) = %d" % form_rc)

    fields = (lcurl.forms * 5)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"somename"
    fields[1].option = lcurl.CURLFORM_BUFFER
    fields[1].value  = b"somefile.txt"
    fields[2].option = lcurl.CURLFORM_BUFFERPTR
    fields[2].value  = b"blah blah"
    fields[3].option = lcurl.CURLFORM_BUFFERLENGTH
    fields[3].value  = 9
    fields[4].option = lcurl.CURLFORM_END
    form_rc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    if form_rc:
        print("libcurl.formadd(5) = %d" % form_rc)

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(False, curl) as guard:
        if not curl:  # pragma: no cover
            lcurl.formfree(formpost)
            return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # Now specify we want to POST data
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        # Set the expected POST size
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, pooh.sizeleft)
        # we want to use our own read function
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        # send a multi-part formpost
        test_setopt(curl, lcurl.CURLOPT_HTTPPOST, formpost)
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

        # test_cleanup:

        # now cleanup the formpost chain
        lcurl.formfree(formpost)

    return res


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        res = test_once(URL, True)  # old
        if res != lcurl.CURLE_OK: raise guard.Break

        res = test_once(URL, False)  # new
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
