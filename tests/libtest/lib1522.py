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
import socket

import libcurl as lcurl
from curl_test import *  # noqa
from curl_trace import *  # noqa

#
# test case and code based on https://github.com/curl/curl/issues/2847
#


g_Data = (ct.c_char * (40 * 1024))()  # POST 40KB
g_sock = None


@lcurl.sockopt_callback
def sockopt_callback(clientp, curlfd, purpose):
    if hasattr(socket, "SOL_SOCKET") and hasattr(socket, "SO_SNDBUF"):
        global g_sock
        g_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, curlfd)
        sndbufsize = 4 * 1024  # 4KB send buffer
        g_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, sndbufsize)
    return lcurl.CURL_SOCKOPT_OK


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global libtest_debug_config, libtest_debug_cb
    global g_Data

    res: lcurl.CURLcode = TEST_ERR_MAJOR_BAD

    ct.memset(g_Data, ord(b'A'), ct.sizeof(g_Data))  # send As!

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SOCKOPTFUNCTION, sockopt_callback)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, g_Data)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, ct.sizeof(g_Data))
        libtest_debug_config.nohex     = 1
        libtest_debug_config.tracetime = 1
        test_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
        test_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # Remove "Expect: 100-continue"
        pHeaderList: ct.POINTER(lcurl.slist) = lcurl.slist_append(None, b"Expect:")
        guard.add_slist(pHeaderList)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, pHeaderList)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() failed. e = %d" % res)
            raise guard.Break

        upload_size = lcurl.off_t()
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_SIZE_UPLOAD_T, ct.byref(upload_size))
        print("uploadSize = %ld" % upload_size.value)
        if upload_size.value == ct.sizeof(g_Data):
            print("!!!!!!!!!! PASS")
        else:
            print("sent %d, libcurl says %d" % (ct.sizeof(g_Data), upload_size.value))

    return res
