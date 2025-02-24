# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 2020 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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
from curl_trace import *  # noqa

#
# Read/write HSTS cache entries via callback.
#


class entry(ct.Structure):
    _fields_ = [
    ("name", ct.c_char_p),
    ("exp",  ct.c_char_p),
]


if ct.sizeof(lcurl.time_t) < 5:
    preload_hosts = [
    # curl turns 39 that day just before 31-bit lcurl.time_t overflow
    entry(b"1.example.com", b"20370320 01:02:03"),
    entry(b"2.example.com", b"20370320 03:02:01"),
    entry(b"3.example.com", b"20370319 01:02:03"),
    ]
else:
    preload_hosts = [
    entry(b"1.example.com", b"25250320 01:02:03"),
    entry(b"2.example.com", b"25250320 03:02:01"),
    entry(b"3.example.com", b"25250319 01:02:03"),
    ]
preload_hosts.extend([
    entry(b"4.example.com", b""),
    entry(None, None),  # end of list marker
])


class state(ct.Structure):
    _fields_ = [
    ("index", ct.c_int),
]


@lcurl.hstsread_callback
def hstsread(easy, entry, userp):
    # "read" is from the point of the library, it wants data from us
    entry = entry.contents
    st = ct.cast(userp, ct.POINTER(state)).contents

    host:   str = preload_hosts[st.index].name
    expire: str = preload_hosts[st.index].exp
    st.index += 1

    if not host or len(host) >= entry.namelen:
        return lcurl.CURLSTS_DONE

    ct.memmove(entry.name, host, len(host) + 1)
    entry.includeSubDomains = False
    ct.memmove(entry.expire, expire, len(expire) + 1)
    print("add '%s'" % host, file=sys.stderr)
    return lcurl.CURLSTS_OK


@lcurl.hstsread_callback
def hstsreadfail(easy, entry, userp):
    # verify error from callback
    return lcurl.CURLSTS_FAIL


@lcurl.hstswrite_callback
def hstswrite(easy, entry, index, userp):
    # check that we get the hosts back in the save
    entry = entry.contents
    index = index.contents
    print("[%u/%u] %s %s" % (index.index, index.total,
          entry.name.decode("utf-8"), entry.expire.decode("utf-8")))
    return lcurl.CURLSTS_OK


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global libtest_debug_config, libtest_debug_cb

    res: lcurl.CURLcode = lcurl.CURLE_OK

    curl: ct.POINTER(lcurl.CURL)

    st = state(0)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    libtest_debug_config.nohex     = 1
    libtest_debug_config.tracetime = 1

    with curl_guard(True) as guard:

        curl = easy_init()

        with curl_guard(False, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            easy_setopt(curl, lcurl.CURLOPT_CONNECTTIMEOUT, 1)
            easy_setopt(curl, lcurl.CURLOPT_HSTSREADFUNCTION, hstsread)
            easy_setopt(curl, lcurl.CURLOPT_HSTSREADDATA, ct.byref(st))
            easy_setopt(curl, lcurl.CURLOPT_HSTSWRITEFUNCTION, hstswrite)
            easy_setopt(curl, lcurl.CURLOPT_HSTSWRITEDATA, ct.byref(st))
            easy_setopt(curl, lcurl.CURLOPT_HSTS_CTRL, lcurl.CURLHSTS_ENABLE)
            easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
            easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
            easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

            res = lcurl.easy_perform(curl)

        curl = None
        if res == lcurl.CURLE_OPERATION_TIMEDOUT:  # we expect that on Windows
            res = lcurl.CURLE_COULDNT_CONNECT
        print("First request returned %d" % res)

        res = lcurl.CURLE_OK

        curl = easy_init()

        with curl_guard(False, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            easy_setopt(curl, lcurl.CURLOPT_CONNECTTIMEOUT, 1)
            easy_setopt(curl, lcurl.CURLOPT_HSTSREADFUNCTION, hstsreadfail)
            easy_setopt(curl, lcurl.CURLOPT_HSTSREADDATA, ct.byref(st))
            easy_setopt(curl, lcurl.CURLOPT_HSTSWRITEFUNCTION, hstswrite)
            easy_setopt(curl, lcurl.CURLOPT_HSTSWRITEDATA, ct.byref(st))
            easy_setopt(curl, lcurl.CURLOPT_HSTS_CTRL, lcurl.CURLHSTS_ENABLE)
            easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
            easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
            easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

            res = lcurl.easy_perform(curl)

        curl = None
        print("Second request returned %d" % res)

    return res
