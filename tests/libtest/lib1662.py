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


testdata: bytes = b"mooaaa"


class WriteThis(ct.Structure):
    _fields_ = [
    ("sizeleft", ct.c_size_t),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    data_len = len(testdata)
    if buffer_size < data_len: return 0
    if pooh.sizeleft == 0: return 0  # no more data left to deliver
    ct.memmove(buffer, testdata, data_len)
    pooh.sizeleft = 0
    return data_len


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    pooh = WriteThis(1)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_BUFFERSIZE, 102400)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        mime: ct.POINTER(lcurl.mime) = lcurl.mime_init(curl)
        if mime:
            part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)
            lcurl.mime_data_cb(part, -1, read_callback,
                               lcurl.seek_callback(0), lcurl.free_callback(0),
                               ct.byref(pooh))
            lcurl.mime_filename(part, b"poetry.txt")
            lcurl.mime_name(part, b"content")
            lcurl.easy_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"curl/2000")
            lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_MAXREDIRS, 50)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION,
                                    lcurl.CURL_HTTP_VERSION_2TLS)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_FTP_SKIP_PASV_IP, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPALIVE, 1)

            res = lcurl.easy_perform(curl)

        lcurl.mime_free(mime)

    return res
