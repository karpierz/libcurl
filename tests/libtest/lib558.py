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


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    a = (ct.c_ubyte * 14)(0x2f, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f,
                          0x91, 0xa2, 0xb3, 0xc4, 0xd5, 0xe6, 0xf7)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        ptr: ct.POINTER(ct.c_char) = ct.cast(libc.malloc(558), ct.POINTER(ct.c_char))
        libc.free(ptr) ; ptr = ct.POINTER(ct.c_char)()

        asize: int = ct.sizeof(a)
        ptr: bytes = lcurl.easy_escape(None, ct.cast(a, ct.c_char_p), asize)

    return res
