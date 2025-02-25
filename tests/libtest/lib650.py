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

# This test attempts to use all form API features that are not
# used elsewhere.


testdata = ct.create_string_buffer(b"this is what we post to the silly web server")
testname = ct.c_char_p(b"fieldname")


@lcurl.formget_callback
def count_chars(arg, buf, size):
    # curl_formget callback to count characters.
    pcounter = ct.cast(arg, ct.POINTER(ct.c_size_t))
    pcounter[0] += size
    return size


@curl_test_decorator
def test(URL: str, file_path: str) -> lcurl.CURLcode:
    file_path = str(file_path)

    global testdata, testname

    res: lcurl.CURLcode = TEST_ERR_MAJOR_BAD

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    # Check proper name and data copying, as well as headers.
    headers:  ct.POINTER(lcurl.slist)
    headers2: ct.POINTER(lcurl.slist)
    headers = lcurl.slist_append(None, b"X-customheader-1: Header 1 data")
    if not headers: goto(test_cleanup)
    headers2 = lcurl.slist_append(headers, b"X-customheader-2: Header 2 data")
    if not headers2: goto(test_cleanup)
    headers = headers2
    headers2 = lcurl.slist_append(headers, b"Content-Type: text/plain")
    if not headers2: goto(test_cleanup)
    headers = headers2

    formrc: lcurl.CURLFORMcode
    formpost: ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()
    lastptr:  ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()

    # CURL_IGNORE_DEPRECATION(
    fields = (lcurl.forms * 4)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = testname
    fields[1].option = lcurl.CURLFORM_COPYCONTENTS
    fields[1].value  = ct.cast(testdata, ct.c_char_p)
    fields[2].option = lcurl.CURLFORM_CONTENTHEADER
    fields[2].value  = ct.cast(headers, ct.c_char_p)
    fields[3].option = lcurl.CURLFORM_END
    formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    # )
    if formrc:
        print("libcurl.formadd(1) = %d" % formrc)
        goto(test_cleanup)

    # <AK>: Commented, because API problem, when array appears as subform.
    # CURL_IGNORE_DEPRECATION(
    # Use a form array for the non-copy test.
    formarray = (lcurl.forms * 3)()
    """
    formarray[0].option = lcurl.CURLFORM_PTRCONTENTS
    formarray[0].value  = ct.cast(testdata, ct.c_char_p)
    formarray[1].option = lcurl.CURLFORM_CONTENTSLENGTH
    formarray[1].value  = strlen(testdata) - 1
    formarray[2].option = lcurl.CURLFORM_END
    formarray[2].value  = 0  # NULL

    fields = (lcurl.forms * 5)()
    fields[0].option = lcurl.CURLFORM_PTRNAME
    fields[0].value  = testname
    fields[1].option = lcurl.CURLFORM_NAMELENGTH
    fields[1].value  = strlen(testname.value) - 1
    fields[2].option = lcurl.CURLFORM_ARRAY
    fields[2].valuep = ct.cast(formarray, ct.c_void_p)
    fields[3].option = lcurl.CURLFORM_FILENAME
    fields[3].value  = b"remotefile.txt"
    fields[4].option = lcurl.CURLFORM_END
    formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    # )
    if formrc:
        print("libcurl.formadd(2) = %d" % formrc)
        goto(test_cleanup)
    """

    # Now change in-memory data to affect CURLOPT_PTRCONTENTS value.
    # Copied values (first field) must not be affected.
    # CURLOPT_PTRNAME actually copies the name thus we do not test this here.
    testdata[0] = ord(testdata[0]) + 1

    # CURL_IGNORE_DEPRECATION(
    # Check multi-files and content type propagation.
    fields = (lcurl.forms * 6)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"multifile"
    fields[1].option = lcurl.CURLFORM_FILE
    fields[1].value  = file_path.encode("utf-8")
    fields[2].option = lcurl.CURLFORM_FILE
    fields[2].value  = file_path.encode("utf-8")
    fields[3].option = lcurl.CURLFORM_CONTENTTYPE
    fields[3].value  = b"text/whatever"
    fields[4].option = lcurl.CURLFORM_FILE
    fields[4].value  = file_path.encode("utf-8")
    fields[5].option = lcurl.CURLFORM_END
    formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    # )
    if formrc:
        print("libcurl.formadd(3) = %d" % formrc)
        goto(test_cleanup)

    # CURL_IGNORE_DEPRECATION(
    # Check data from file content.
    fields = (lcurl.forms * 3)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"filecontents"
    fields[1].option = lcurl.CURLFORM_FILECONTENT
    fields[1].value  = file_path.encode("utf-8")
    fields[2].option = lcurl.CURLFORM_END
    formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    # )
    if formrc:
        print("libcurl.formadd(4) = %d" % formrc)
        goto(test_cleanup)

    # CURL_IGNORE_DEPRECATION(
    # Measure the current form length.
    # This is done before including stdin data because we want to reuse it
    # and stdin cannot be rewound.
    formlength = ct.c_size_t(0)
    lcurl.formget(formpost, ct.byref(formlength), count_chars)
    formlength = formlength.value
    # )

    # CURL_IGNORE_DEPRECATION(
    # Include length in data for external check.
    fields = (lcurl.forms * 3)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"formlength"
    fields[1].option = lcurl.CURLFORM_COPYCONTENTS
    fields[1].value  = b"%lu" % formlength
    fields[2].option = lcurl.CURLFORM_END
    formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    # )
    if formrc:
        print("libcurl.formadd(5) = %d" % formrc)
        goto(test_cleanup)

    # CURL_IGNORE_DEPRECATION(
    # Check stdin (may be problematic on some platforms).
    fields = (lcurl.forms * 3)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"standardinput"
    fields[1].option = lcurl.CURLFORM_FILE
    fields[1].value  = b"-"
    fields[2].option = lcurl.CURLFORM_END
    formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
    # )
    if formrc:
        print("libcurl.formadd(6) = %d" % formrc)
        goto(test_cleanup)

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: goto(test_cleanup)

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # CURL_IGNORE_DEPRECATION(
        # send a multi-part formpost
        test_setopt(curl, lcurl.CURLOPT_HTTPPOST, formpost)
        # )
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
        test_setopt(curl, lcurl.CURLOPT_POSTREDIR, lcurl.CURL_REDIR_POST_301)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

        # test_cleanup:

        # CURL_IGNORE_DEPRECATION(
        # now cleanup the formpost chain
        lcurl.formfree(formpost)
        # )
        lcurl.slist_free_all(headers)

    return res
