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
# are also available at https://curl.haxx.se/docs/copyright.html.
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


@lcurl.opensocket_callback
def socket_cb(clientp, purpose, address):
    # provide our own socket
    sock_obj = lcurl.from_oid(clientp)
    return sock_obj.fileno()


@lcurl.closesocket_callback
def closesocket_cb(clientp, sock):
    # to prevent libcurl from closing our socket
    return 0


@lcurl.sockopt_callback
def sockopt_cb(clientp, curlfd, purpose):
    # tell libcurl the socket is connected
    return lcurl.CURL_SOCKOPT_ALREADY_CONNECTED


@curl_test_decorator
def test(URL: str, address: str, port: str) -> lcurl.CURLcode:
    # Expected args: URL IP PORT

    res: lcurl.CURLcode = TEST_ERR_MAJOR_BAD

    if URL == "check":
        return lcurl.CURLE_OK  # no output makes it not skipped

    # This code connects to the TCP port "manually" so that we then can hand
    # over this socket as "already connected" to libcurl and make sure that
    # this works.

    try:
        sock_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except OSError as exc:
        print("socket creation error", file=sys.stderr)
        return res

    try:
        socket.inet_pton(socket.AF_INET, address)
    except socket.error:
        print("inet_pton failed", file=sys.stderr)
        sock_obj.close()
        return res

    try:
        sock_obj.connect((address, int(port)))
    except OSError as exc:
        print("connection failed", file=sys.stderr)
        sock_obj.close()
        return res

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        sock_obj.close()
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(False, curl) as guard:
        if not curl:
            sock_obj.close()
            lcurl.global_cleanup()
            return res

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_OPENSOCKETFUNCTION, socket_cb)
        test_setopt(curl, lcurl.CURLOPT_OPENSOCKETDATA, id(sock_obj))
        test_setopt(curl, lcurl.CURLOPT_SOCKOPTFUNCTION, sockopt_cb)
        test_setopt(curl, lcurl.CURLOPT_SOCKOPTDATA, None)
        test_setopt(curl, lcurl.CURLOPT_CLOSESOCKETFUNCTION, closesocket_cb)
        test_setopt(curl, lcurl.CURLOPT_CLOSESOCKETDATA, None)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    sock_obj.close()
    lcurl.global_cleanup()

    return res
