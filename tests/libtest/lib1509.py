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

# from warnless.c
# unsigned size_t to unsigned long
def curlx_uztoul(uznum) -> int: return int(uznum)


real_header_size: int = 0


@lcurl.write_callback
def header_callback(buffer, size, nitems, stream):
    global real_header_size
    buffer_size = nitems * size
    real_header_size += curlx_uztoul(buffer_size)
    return buffer_size


@curl_test_decorator
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    global real_header_size

    code: lcurl.CURLcode
    res:  lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)
        easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION,  lcurl.write_to_file)
        easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sys.stdout.buffer))
        easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, header_callback)
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_HTTPPROXYTUNNEL, 1)

        code = lcurl.easy_perform(curl)
        if code != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_perform() failed, with code %d (%s)" %
                  (current_file(), current_line(),
                   code, lcurl.easy_strerror(code).decode("utf-8")), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        header_size = ct.c_long()
        code = lcurl.easy_getinfo(curl, lcurl.CURLINFO_HEADER_SIZE,
                                  ct.byref(header_size))
        if code != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_getinfo() failed, with code %d (%s)" %
                  (current_file(), current_line(),
                   code, lcurl.easy_strerror(code).decode("utf-8")), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        print("header length is ........: %ld" % header_size.value)
        print("header length should be..: %lu" % real_header_size)

    return res
