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


def fail_unless(expr: bool, expr_str: str, msg: str):
    if not expr:
        import os
        print("%s:%d Assertion '%s' failed: %s",
              (os.path.basename(current_file(2)), current_line(2),
               expr_str, msg), file=sys.stderr)
        raise Exception()


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    rc: int

    try:
        rc = lcurl.strequal(b"iii", b"III")
        fail_unless(rc != 0, "rc != 0","return code should be non-zero")

        rc = lcurl.strequal(b"iiia", b"III")
        fail_unless(rc == 0, "rc == 0","return code should be zero")

        rc = lcurl.strequal(b"iii", b"IIIa")
        fail_unless(rc == 0, "rc == 0","return code should be zero")

        rc = lcurl.strequal(b"iiiA", b"IIIa")
        fail_unless(rc != 0, "rc != 0","return code should be non-zero")

        rc = lcurl.strnequal(b"iii", b"III", 3);
        fail_unless(rc != 0, "rc != 0","return code should be non-zero")

        rc = lcurl.strnequal(b"iiiABC", b"IIIcba", 3);
        fail_unless(rc != 0, "rc != 0","return code should be non-zero")

        rc = lcurl.strnequal(b"ii", b"II", 3);
        fail_unless(rc != 0, "rc != 0","return code should be non-zero")
    except:
        return lcurl.CURLcode(1).value

    return lcurl.CURLE_OK
