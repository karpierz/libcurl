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

"""
WebSocket using CONNECT_ONLY
"""

import sys
import ctypes as ct
import time

import libcurl as lcurl
from curl_utils import *  # noqa


def ping(curl: ct.POINTER(lcurl.CURL), send_payload: bytes) -> int:
    sent = ct.c_size_t()
    return lcurl.ws_send(curl, send_payload, len(send_payload),
                         ct.byref(sent), 0, lcurl.CURLWS_PING)


def recv_pong(curl: ct.POINTER(lcurl.CURL), expected_payload: bytes) -> int:
    buff = (ct.c_char * 256)()
    rlen = ct.c_size_t()
    meta = ct.POINTER(lcurl.ws_frame)
    result = lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                           ct.byref(rlen), ct.byref(meta))
    rlen = rlen.value
    if result == lcurl.CURLE_OK:
        meta = meta.contents
        if meta.flags & lcurl.CURLWS_PONG:
            print("ws: got PONG back", file=sys.stderr)
            if rlen == len(expected_payload) and expected_payload == buff[0:rlen]:
                print("ws: got the same payload back", file=sys.stderr)
            else:
                print("ws: did NOT get the same payload back", file=sys.stderr)
        else:
            print("recv_pong: got %u bytes rflags %x" % (rlen, meta.flags),
                  file=sys.stderr)

    print("ws: curl_ws_recv returned %u, received %u" % (result, rlen),
          file=sys.stderr)
    return result


def recv_any(curl: ct.POINTER(lcurl.CURL)) -> lcurl.CURLcode:
    buff = (ct.c_char * 256)()
    rlen = ct.c_size_t()
    meta = ct.POINTER(lcurl.ws_frame)
    return lcurl.CURLcode(lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                                        ct.byref(rlen), ct.byref(meta)))


def websocket(curl: ct.POINTER(lcurl.CURL)):
    for i in range(10):
        recv_any(curl)
        if ping(curl, b"foobar") != lcurl.CURLE_OK:
            return
        if recv_pong(curl, b"foobar") != lcurl.CURLE_OK:
            return
        time.sleep(2)
    websocket_close(curl)


def websocket_close(curl: ct.POINTER(lcurl.CURL)):
    # close the connection
    sent = ct.c_size_t()
    lcurl.ws_send(curl, b"", 0, ct.byref(sent), 0, lcurl.CURLWS_CLOSE)


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "wss://example.com"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 2)  # websocket style

        # Perform the request, res gets the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)
        if res != lcurl.CURLE_OK:
            raise guard.Break

        # connected and ready
        websocket(curl)

    return int(res)


sys.exit(main())
