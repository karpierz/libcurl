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


class transfer_status(ct.Structure):
    _fields_ = [
    ("easy",        ct.POINTER(lcurl.CURL)),
    ("out_len",     lcurl.off_t),
    ("hd_line",     ct.c_size_t),
    ("result",      lcurl.CURLcode),
    ("http_status", ct.c_int),
]


@lcurl.write_callback
def header_callback(buffer, size, nitems, userp):
    st = ct.cast(userp, ct.POINTER(transfer_status)).contents
    total_size = size * nitems

    hd = bytes(buffer[:total_size])
    sys.stdout.buffer.write(hd)

    st.hd_line += 1
    if total_size == 2 and hd[0] == ord("\r") and hd[1] == ord("\n"):

        result: lcurl.CURLcode

        httpcode = ct.c_long(0)
        # end of a response
        result = lcurl.easy_getinfo(st.easy, lcurl.CURLINFO_RESPONSE_CODE,
                                    ct.byref(httpcode))
        httpcode = httpcode.value
        print("header_callback, get status: %ld, %d" %
              (httpcode, result), file=sys.stderr)
        if httpcode < 100 or httpcode >= 1000:
            print("header_callback, invalid status: %ld, %d" %
                  (httpcode, result), file=sys.stderr)
            return lcurl.CURLE_WRITE_ERROR
        st.http_status = httpcode

        if st.http_status >= 200 and st.http_status < 300:
            clen = lcurl.off_t()
            result = lcurl.easy_getinfo(st.easy,
                                        lcurl.CURLINFO_CONTENT_LENGTH_DOWNLOAD_T,
                                        ct.byref(clen))
            clen = clen.value
            print("header_callback, info Content-Length: %ld, %d" %
                  (clen, result), file=sys.stderr)
            if result:
                st.result = result;
                return lcurl.CURLE_WRITE_ERROR
            if clen < 0:
                print("header_callback, expected known Content-Length, "
                      "got: %ld" % clen, file=sys.stderr)
                return lcurl.CURLE_WRITE_ERROR

    return total_size


@lcurl.write_callback
def write_callback(buffer, size, nitems, userp):
    st = ct.cast(userp, ct.POINTER(transfer_status)).contents
    total_size = nitems * size
    sys.stdout.buffer.write(bytes(buffer[:total_size]))
    st.out_len += total_size
    return total_size


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    st = transfer_status()
    ct.memset(ct.byref(st), 0, ct.sizeof(st))

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()
    st.easy = curl  # to allow callbacks access

    with curl_guard(True, curl) as guard:

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback)
        easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(st))
        easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, header_callback)
        easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, ct.byref(st))

        easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res  # return the final return code
