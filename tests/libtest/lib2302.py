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

from typing import Optional
import sys
import ctypes as ct
import time

import libcurl as lcurl
from curl_test import *  # noqa


if not defined("CURL_DISABLE_WEBSOCKETS") or not CURL_DISABLE_WEBSOCKETS:

    class ws_data(ct.Structure):
        _fields_ = [
        ("easy",       ct.POINTER(lcurl.CURL)),
        ("buf",        (ct.c_byte * (1024 * 1024))),
        ("blen",       ct.c_size_t),
        ("nwrites",    ct.c_size_t),
        ("has_meta",   ct.c_bool),
        ("meta_flags", ct.c_int),
    ]

    def flush_data(wd: ws_data):

        if wd.nwrites == 0:
            return

        for i in range(wd.blen):
            print("%02x " % wd.buf[i], end="")
        print()

        if wd.has_meta:
            print("RECFLAGS: %x" % wd.meta_flags)
        else:
            print("RECFLAGS: NULL", file=sys.stderr)

        wd.blen    = 0
        wd.nwrites = 0


    def add_data(wd: ws_data, buf, blen: int,
                 meta: Optional[lcurl.ws_frame]) -> int:

        if (wd.nwrites == 0 or
            bool(meta) != wd.has_meta or
            (meta and meta.flags != wd.meta_flags)):
            if wd.nwrites > 0:
                flush_data(wd)
            wd.has_meta   = bool(meta)
            wd.meta_flags = meta.flags if wd.has_meta else 0

        if wd.blen + blen > ct.sizeof(wd.buf):
            return 0

        ct.memmove(ct.byref(wd.buf, wd.blen), buf, blen)
        wd.blen    += blen
        wd.nwrites += 1
        return blen


    @lcurl.write_callback
    def writecb(buffer, size, nitems, outstream):
        wd = ct.cast(outstream, ct.POINTER(ws_data)).contents
        meta_p: ct.POINTER(lcurl.ws_frame) = lcurl.ws_meta(wd.easy)
        meta = meta_p.contents if meta_p else None
        incoming = add_data(wd, buffer, nitems, meta)
        if incoming != nitems:
            print("returns error from callback", file=sys.stderr)
        return nitems


    @curl_test_decorator
    def test(URL: str) -> lcurl.CURLcode:

        res: lcurl.CURLcode = lcurl.CURLE_OK

        if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
            return TEST_ERR_MAJOR_BAD

        curl: ct.POINTER(lcurl.CURL) = easy_init()

        with curl_guard(True, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            wd = ws_data()
            wd.easy = curl

            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # use the callback style
            lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"webbie-sox/3")
            lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, writecb)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(wd))

            res = lcurl.easy_perform(curl)
            print("libcurl.easy_perform() returned %u" % res, file=sys.stderr)

            flush_data(wd)

        return res

else:  # no WebSockets

    from curl_test import test_missing_support as test

# endif
