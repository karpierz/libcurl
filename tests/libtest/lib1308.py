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


@lcurl.formget_callback
def print_httppost_callback(arg, buf, size):
    sys.stdout.buffer.write(bytes(buf[:size]))
    # curl_formget callback to count characters.
    pcounter = ct.cast(arg, ct.POINTER(ct.c_size_t))
    pcounter[0] += size
    return size


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    # buffer= b"test buffer"
    buffer = ct.c_char_p(b"test buffer")

    rc: lcurl.CURLFORMcode
    post: ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()
    last: ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()

    fields = (lcurl.forms * 3)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"name"
    fields[1].option = lcurl.CURLFORM_COPYCONTENTS
    fields[1].value  = b"content"
    fields[2].option = lcurl.CURLFORM_END
    rc = lcurl.formadd(ct.byref(post), ct.byref(last), fields)
    fail_unless(rc == 0, "rc == 0", "curl_formadd returned error: {}".format(rc))
    # after the first curl_formadd when there's a single entry, both pointers
    # should point to the same struct
    fail_unless(ct.cast(post, ct.c_void_p).value == ct.cast(last, ct.c_void_p).value,
                "post == last", "post and last weren't the same")

    fields = (lcurl.forms * 4)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"htmlcode"
    fields[1].option = lcurl.CURLFORM_COPYCONTENTS
    fields[1].value  = b"<HTML></HTML>"
    fields[2].option = lcurl.CURLFORM_CONTENTTYPE
    fields[2].value  = b"text/html"
    fields[3].option = lcurl.CURLFORM_END
    rc = lcurl.formadd(ct.byref(post), ct.byref(last), fields)
    fail_unless(rc == 0, "rc == 0", "curl_formadd returned error: {}".format(rc))

    fields = (lcurl.forms * 3)()
    fields[0].option = lcurl.CURLFORM_COPYNAME
    fields[0].value  = b"name_for_ptrcontent"
    fields[1].option = lcurl.CURLFORM_PTRCONTENTS
    fields[1].value  = buffer
    fields[2].option = lcurl.CURLFORM_END
    rc = lcurl.formadd(ct.byref(post), ct.byref(last), fields)
    fail_unless(rc == 0, "rc == 0", "curl_formadd returned error: {}".format(rc))

    total_size = ct.c_size_t(0)

    res = lcurl.formget(post, ct.byref(total_size), print_httppost_callback)
    fail_unless(res == 0, "res == 0", "curl_formget returned error: {}".format(res))
    fail_unless(total_size.value == 518, "total_size.value == 518",
                "curl_formget got wrong size back")

    lcurl.formfree(post)

    # start a new formpost with a file upload and formget
    post = ct.POINTER(lcurl.httppost)()
    last = ct.POINTER(lcurl.httppost)()

    fields = (lcurl.forms * 4)()
    fields[0].option = lcurl.CURLFORM_PTRNAME
    fields[0].value  = b"name of file field"
    fields[1].option = lcurl.CURLFORM_FILE
    fields[1].value  = URL.encode("utf-8")
    fields[2].option = lcurl.CURLFORM_FILENAME
    fields[2].value  = b"custom named file"
    fields[3].option = lcurl.CURLFORM_END
    rc = lcurl.formadd(ct.byref(post), ct.byref(last), fields)
    fail_unless(rc == 0, "rc == 0", "curl_formadd returned error: {}".format(rc))

    res = lcurl.formget(post, ct.byref(total_size), print_httppost_callback)
    fail_unless(res == 0, "res == 0", "curl_formget returned error: {}".format(res))
    fail_unless(total_size.value == 899, "total_size.value == 899",
                "curl_formget got wrong size back")

    lcurl.formfree(post)

    return lcurl.CURLE_OK
