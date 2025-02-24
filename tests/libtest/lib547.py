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

# argv1 = URL
# argv2 = proxy
# argv3 = proxyuser:password


uploadthis = b"this is the blurb we want to upload\n"


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    counter = ct.cast(userp, ct.POINTER(ct.c_int)).contents

    if counter.value:
        # only do this once and then require a clearing of this
        print("READ ALREADY DONE!", file=sys.stderr)
        return 0

    counter.value += 1  # bump

    data_size = len(uploadthis)

    if data_size > nitems * size:
        print("READ NOT FINE!", file=sys.stderr)
        return 0

    print("READ!", file=sys.stderr)
    ct.memmove(buffer, uploadthis, data_size + 1)
    return data_size


@lcurl.ioctl_callback
def ioctl_callback(handle, cmd, clientp):
    counter = ct.cast(clientp, ct.POINTER(ct.c_int)).contents

    if cmd == lcurl.CURLIOCMD_RESTARTREAD:
        print("REWIND!", file=sys.stderr)
        counter.value = 0  # clear counter to make the read callback restart

    return lcurl.CURLIOE_OK


@curl_test_decorator
def test(URL: str,
         proxy: str = None,
         proxy_login: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    counter = ct.c_int(0)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        if defined("LIB548"):
            # set the data to POST with a mere pointer to a null-terminated string
            test_setopt(curl, lcurl.CURLOPT_POSTFIELDS, uploadthis)
        else:
            # 547 style, which means reading the POST data from a callback
            # CURL_IGNORE_DEPRECATION(
            test_setopt(curl, lcurl.CURLOPT_IOCTLFUNCTION, ioctl_callback)
            test_setopt(curl, lcurl.CURLOPT_IOCTLDATA, ct.byref(counter))
            # )
            test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
            test_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(counter))
            # We CANNOT do the POST fine without setting the size (or choose
            # chunked)!
            test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, len(uploadthis))
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        test_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)
        if proxy_login:
            test_setopt(curl, lcurl.CURLOPT_PROXYUSERPWD, proxy_login.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_PROXYAUTH,
                          lcurl.CURLAUTH_BASIC | lcurl.CURLAUTH_DIGEST | lcurl.CURLAUTH_NTLM)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
