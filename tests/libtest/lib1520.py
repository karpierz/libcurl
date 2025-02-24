# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Steve Holme, <steve_holme@hotmail.com>.
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

#
# This is the list of basic details you need to tweak to get things right.
#

TO   = "<recipient@example.com>"
FROM = "<sender@example.com>"

payload_text = [
    "From: different\r\n",
    "To: another\r\n",
    "\r\n",
    "\r\n",
    ".\r\n",
    ".\r\n",
    "\r\n",
    ".\r\n",
    "\r\n",
    "body",
    None
]

class upload_status(ct.Structure):
    _fields_ = [
    ("lines_read", ct.c_int),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    upload_ctx = ct.cast(userp, ct.POINTER(upload_status)).contents
    buffer_size = nitems * size
    if buffer_size < 1: return 0
    data = payload_text[upload_ctx.lines_read]
    if data is None: return 0
    data = data.encode("utf-8")
    data_size = len(data)
    ct.memmove(buffer, data, data_size)
    upload_ctx.lines_read += 1
    return data_size


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    upload_ctx = upload_status(0)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        rcpt_list: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                   TO.encode("utf-8"))
        # more addresses can be added here
        # rcpt_list = lcurl.slist_append(rcpt_list, b"<others@example.com>")
        guard.add_slist(rcpt_list)

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        test_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(upload_ctx))
        test_setopt(curl, lcurl.CURLOPT_MAIL_FROM, FROM.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_MAIL_RCPT, rcpt_list)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
