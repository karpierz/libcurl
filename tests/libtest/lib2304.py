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
        result: lcurl.CURLcode = lcurl.ws_send(curl, send_payload, len(send_payload),
                                               ct.byref(sent), 0, lcurl.CURLWS_PING)
        sent = sent.value
        print("ws: libcurl.ws_send returned %d, sent %d" % (result, sent),
              file=sys.stderr)
        return result


    def recv_pong(curl: ct.POINTER(lcurl.CURL), expected_payload: bytes) -> lcurl.CURLcode:
        buff = (ct.c_char * 256)()
        rlen = ct.c_size_t()
        meta = ct.POINTER(lcurl.ws_frame)()
        result: lcurl.CURLcode = lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                                               ct.byref(rlen), ct.byref(meta))
        rlen = rlen.value
        if not result:
            meta = meta.contents
            if meta.flags & lcurl.CURLWS_PONG:
                print("ws: got PONG back", file=sys.stderr)
                if rlen == len(expected_payload) and expected_payload == buff[0:rlen]:
                    print("ws: got the same payload back", file=sys.stderr)
                else:
                    print("ws: did NOT get the same payload back", file=sys.stderr)
            else:
                print("recv_pong: got %d bytes rflags %x" % (rlen, meta.flags),
                      file=sys.stderr)
        print("ws: libcurl.ws_recv returned %d, received %d" % (result, rlen),
              file=sys.stderr)
        return result


    def recv_any(curl: ct.POINTER(lcurl.CURL)) -> lcurl.CURLcode:
        buff = (ct.c_char * 256)()
        rlen = ct.c_size_t()
        meta = ct.POINTER(lcurl.ws_frame)()
        result: lcurl.CURLcode = lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                                               ct.byref(rlen), ct.byref(meta))
        if result:
            return result
        rlen = rlen.value
        meta = meta.contents
        print("recv_any: got %u bytes rflags %x" % (rlen, meta.flags),
              file=sys.stderr)
        return lcurl.CURLE_OK


    def websocket(curl: ct.POINTER(lcurl.CURL)):
        print("ws: websocket() starts", file=sys.stderr)
        for i in range(10):
            recv_any(curl)
            print("Send ping", file=sys.stderr)
            if send_ping(curl, b"foobar"):
                return
            print("Receive pong", file=sys.stderr)
            if recv_pong(curl, b"foobar"):
                print("Connection closed")
                return
            time.sleep(2)
        websocket_close(curl)


    def websocket_close(curl: ct.POINTER(lcurl.CURL)):
        # just close the connection
        sent = ct.c_size_t()
        result: lcurl.CURLcode = lcurl.ws_send(curl, b"", 0,
                                               ct.byref(sent), 0,
                                               lcurl.CURLWS_CLOSE)
        sent = sent.value
        print("ws: libcurl.ws_send returned %d, sent %d" %
              (result, sent), file=sys.stderr)


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
            lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"websocket/2304")
            lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 2)  # websocket style

            res = lcurl.easy_perform(curl)
            print("libcurl.easy_perform() returned %d" % res, file=sys.stderr)
            if res != lcurl.CURLE_OK: raise guard.Break

            websocket(curl)

        return res

else:  # no WebSockets

    from curl_test import test_missing_support as test

# endif
