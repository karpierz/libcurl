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

    # create a testbuf with AAAA...BBBBB...CCCC...etc
    for i in range(ct.sizeof(testbuf) // 10):
        ct.memset(ct.byref(testbuf, i * 10), ord('A') + (i % 26), 10)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # Build mime structure.
        mime: ct.POINTER(lcurl.mime) = lcurl.mime_init(curl)
        if not mime:
            print("libcurl.mime_init() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD
        guard.add_mime(mime)

        part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
        if not part:
            print("libcurl.mime_addpart() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        res = lcurl.mime_filename(part, b"myfile.jpg")
        if res:
            print("libcurl.mime_filename() failed", file=sys.stderr)
            return res
        res = lcurl.mime_type(part, b"image/jpeg")
        if res:
            print("libcurl.mime_type() failed", file=sys.stderr)
            return res
        res = lcurl.mime_data(part, ct.cast(testbuf, ct.POINTER(ct.c_ubyte)),
                                    ct.sizeof(testbuf))
        if res:
            print("libcurl.mime_data() failed", file=sys.stderr)
            return res
        res = lcurl.mime_encoder(part, b"base64")
        if res:
            print("libcurl.mime_encoder() failed", file=sys.stderr)
            return res

        # Prepare recipients.
        recipients: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                    b"someone@example.com")
        if not recipients:
            print("libcurl.slist_append() failed", file=sys.stderr)
            goto(test_cleanup)
        guard.add_slist(recipients)

        # First set the URL that is about to receive our mime mail.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # Set sender.
        test_setopt(curl, lcurl.CURLOPT_MAIL_FROM, b"somebody@example.com")
        # Set recipients.
        test_setopt(curl, lcurl.CURLOPT_MAIL_RCPT, recipients)
        # send a multi-part mail
        test_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)
        # Shorten upload buffer.
        test_setopt(curl, lcurl.CURLOPT_UPLOAD_BUFFERSIZE, 16411)
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
