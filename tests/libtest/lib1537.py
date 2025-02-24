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

# because deprecation
# from functools import partial
# lcurl.escape   = partial(lcurl.easy_escape, None)
# lcurl.unescape = partial(lcurl.easy_unescape, None, outlength=None)


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    a = (ct.c_ubyte * 14)(0x2f, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f,
                          0x91, 0xa2, 0xb3, 0xc4, 0xd5, 0xe6, 0xf7)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        asize: int = ct.sizeof(a)
        ptr: bytes = lcurl.easy_escape(None, ct.cast(a, ct.c_char_p), asize)
        print("%s" % ptr.decode("utf-8"))

        # deprecated API
        ptr = lcurl.escape(ct.cast(a, ct.c_char_p), asize)
        if not ptr:
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break
        print("%s" % ptr.decode("utf-8"))

        outlen = ct.c_int(0)
        raw: bytes = lcurl.easy_unescape(None, ptr, len(ptr), ct.byref(outlen))
        print("outlen == %d" % outlen.value)
        print("unescape == original? %s" %
              "no" if raw[:outlen.value] != bytes(a[:outlen.value]) else "YES")

        # deprecated API
        raw = lcurl.unescape(ct.cast(ptr, ct.c_char_p), len(ptr))
        if not raw:
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break
        outlen.value = len(raw)
        print("[old] outlen == %d" % outlen.value)
        print("[old] unescape == original? %s" %
              "no" if raw[:outlen.value] != bytes(a[:outlen.value]) else "YES")

        # weird input length
        ptr = lcurl.easy_escape(None, ct.cast(a, ct.c_char_p), -1)
        print("escape -1 length: %s" %
              (ptr.decode("utf-8") if ptr is not None else ptr))

        # weird input length
        outlen.value = 2017  # just a value
        ptr = lcurl.easy_unescape(None, b"moahahaha", -1, ct.byref(outlen))
        print("unescape -1 length: %s %d" %
              (ptr.decode("utf-8") if ptr is not None else ptr, outlen.value))

    return res
