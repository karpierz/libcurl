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

from typing import List
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

#
# Testing libcurl.CURLOPT_PROTOCOLS_STR
#


class pair(ct.Structure):
    _fields_ = [
    ("inp", ct.c_char_p),
    ("exp", ct.POINTER(lcurl.CURLcode)),
]


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    ok        = lcurl.CURLcode(lcurl.CURLE_OK)
    bad       = lcurl.CURLcode(lcurl.CURLE_BAD_FUNCTION_ARGUMENT)
    unsup     = lcurl.CURLcode(lcurl.CURLE_UNSUPPORTED_PROTOCOL)
    httpcode  = lcurl.CURLcode(lcurl.CURLE_UNSUPPORTED_PROTOCOL)
    httpscode = lcurl.CURLcode(lcurl.CURLE_UNSUPPORTED_PROTOCOL)

    prots = [
        pair(b"goobar",       ct.pointer(unsup)),
        pair(b"http ",        ct.pointer(unsup)),
        pair(b" http",        ct.pointer(unsup)),
        pair(b"http",         ct.pointer(httpcode)),
        pair(b"http,",        ct.pointer(httpcode)),
        pair(b"https,",       ct.pointer(httpscode)),
        pair(b"https,http",   ct.pointer(httpscode)),
        pair(b"http,http",    ct.pointer(httpcode)),
        pair(b"HTTP,HTTP",    ct.pointer(httpcode)),
        pair(b",HTTP,HTTP",   ct.pointer(httpcode)),
        pair(b"http,http,ft", ct.pointer(unsup)),
        pair(b"",             ct.pointer(bad)),
        pair(b",,",           ct.pointer(bad)),
        pair(b"@protocols@",  ct.pointer(ok)),
        pair(b"all",          ct.pointer(ok)),
    ]

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # Get enabled protocols.
        curlinfo = lcurl.version_info(lcurl.CURLVERSION_NOW)
        if not curlinfo:
            print("libcurl.version_info failed", file=sys.stderr)
            return TEST_ERR_FAILURE
        curlinfo = curlinfo.contents

        protolist: List[bytes] = []
        for proto in curlinfo.protocols:
            if not proto: break
            protolist.append(proto)
            if proto == b"http":
                httpcode.value = lcurl.CURLE_OK
            elif proto == b"https":
                httpscode.value = lcurl.CURLE_OK

        protocols = next(prot for prot in prots if prot.inp == b"@protocols@")
        protocols.inp = b",".join(protolist)

        # Run the tests.
        for i, prot in enumerate(prots):
            res = lcurl.easy_setopt(curl, lcurl.CURLOPT_PROTOCOLS_STR, prot.inp)
            if res != prot.exp.contents.value:
                print("unexpectedly '%s' returned %d" %
                      (prot.inp.decode("utf-8"), res))
                break

        print("Tested %u strings" % i)

    return res
