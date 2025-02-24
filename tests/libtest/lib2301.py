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
import time

import libcurl as lcurl
from curl_test import *  # noqa


if not defined("CURL_DISABLE_WEBSOCKETS") or not CURL_DISABLE_WEBSOCKETS:

    def send_ping(curl: ct.POINTER(lcurl.CURL), send_payload: bytes) -> lcurl.CURLcode:
        sent = ct.c_size_t()
        # !!! was error in original lib2301.c: missing one param: , 0 !!!
        result: lcurl.CURLcode = lcurl.ws_send(curl, send_payload, len(send_payload),
                                               ct.byref(sent), 0, lcurl.CURLWS_PING)
        sent = sent.value
        print("ws: libcurl.ws_send returned %d, sent %d" % (result, sent),
              file=sys.stderr)
        return result


    def recv_pong(curl: ct.POINTER(lcurl.CURL), expected_payload: bytes) -> lcurl.CURLcode:
        buff = (ct.c_char * 256)()
        rlen = ct.c_size_t()
        rflags = ct.c_uint()
        result: lcurl.CURLcode = lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                                               ct.byref(rlen), ct.byref(rflags))
        rlen   = rlen.value
        rflags = rflags.value
        if rflags & lcurl.CURLWS_PONG:
            print("ws: got PONG back", file=sys.stderr)
            if rlen == len(expected_payload) and expected_payload == buff[0:rlen]:
                print("ws: got the same payload back", file=sys.stderr)
            else:
                print("ws: did NOT get the same payload back", file=sys.stderr)
        else:
            print("recv_pong: got %d bytes rflags %x" % (rlen, rflags),
                  file=sys.stderr)
        print("ws: libcurl.ws_recv returned %d, received %d" % (result, rlen),
              file=sys.stderr)
        return result


    def websocket(curl: ct.POINTER(lcurl.CURL)):
        print("ws: websocket() starts", file=sys.stderr)
        for i in range(10):
            if send_ping(curl, b"foobar"):
                return
            if recv_pong(curl, b"foobar"):
                return
            time.sleep(2)
        websocket_close(curl)


    def websocket_close(curl: ct.POINTER(lcurl.CURL)):
        # just close the connection
        sent = ct.c_size_t()
        # !!! was error in original lib2301.c: missing one param: , 0 !!!
        result: lcurl.CURLcode = lcurl.ws_send(curl, b"", 0,
                                               ct.byref(sent), 0,
                                               lcurl.CURLWS_CLOSE)
        sent = sent.value
        print("ws: libcurl.ws_send returned %d, sent %d" %
              (result, sent), file=sys.stderr)


    @lcurl.write_callback
    def writecb(buffer, size, nitems, outstream):
        curl: ct.POINTER(lcurl.CURL) = lcurl.from_oid(outstream)
        incoming = nitems

        print("Called CURLOPT_WRITEFUNCTION with %d bytes: " % nitems,
              end="", file=sys.stderr)
        for i in range(nitems):
            print("%02x " % buffer[i], end="", file=sys.stderr)
        print(file=sys.stderr)

        if buffer[0] == 0x89:
            print("send back a simple PONG", file=sys.stderr)
            pong = (ct.c_ubyte * 2)(0x8a, 0x0)
            sent = ct.c_size_t()
            result: lcurl.CURLcode = lcurl.ws_send(curl,
                                                   pong, ct.sizeof(pong),
                                                   ct.byref(sent), 0, 0)
            if result:
                nitems = 0

        if nitems != incoming:
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

            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # use the callback style
            lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"webbie-sox/3")
            lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WS_OPTIONS, lcurl.CURLWS_RAW_MODE)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, writecb)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(curl))

            res = lcurl.easy_perform(curl)
            print("libcurl.easy_perform() returned %d" % res, file=sys.stderr)
            if res != lcurl.CURLE_OK: raise guard.Break

            if 0:
                websocket(curl)
            # endif

        return res

else:  # no WebSockets

    from curl_test import test_missing_support as test

# endif
