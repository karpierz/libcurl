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

#
# Based on Alex Fishman's bug report on September 30, 2007
#

a = (ct.c_ubyte * 20)(0x9c, 0x26, 0x4b, 0x3d, 0x49, 0x4,  0xa1, 0x1,
                      0xe0, 0xd8, 0x7c, 0x20, 0xb7, 0xef, 0x53, 0x29,
                      0xfa, 0x1d, 0x57, 0xe1)


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        asize: int = ct.sizeof(a)
        s: bytes = lcurl.easy_escape(curl, ct.cast(a, ct.c_char_p), asize)
        if s:
            print("%s" % s.decode("utf-8"))

        s = lcurl.easy_escape(curl, b"", 0)
        if s:
            print("IN: '' OUT: '%s'" % s.decode("utf-8"))

        s = lcurl.easy_escape(curl, b" 123", 3)
        if s:
            print("IN: ' 12' OUT: '%s'" % s.decode("utf-8"))

    return res
