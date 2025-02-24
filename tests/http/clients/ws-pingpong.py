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
WebSockets pingpong
"""

import argparse
import sys
import ctypes as ct
import time

import libcurl as lcurl
from curl_utils import *  # noqa


def ping(curl: ct.POINTER(lcurl.CURL), send_payload: bytes) -> lcurl.CURLcode:

    sent = ct.c_size_t()
    result: lcurl.CURLcode = lcurl.ws_send(curl, send_payload, len(send_payload),
                                           ct.byref(sent), 0, lcurl.CURLWS_PING)
    sent = sent.value
    print("ws: curl_ws_send returned %u, sent %u" % (int(result), sent),
          file=sys.stderr)

    return result


def recv_pong(curl: ct.POINTER(lcurl.CURL), expected_payload: bytes) -> lcurl.CURLcode:

    buff = (ct.c_char * 256)()
    rlen = ct.c_size_t()
    meta = ct.POINTER(lcurl.ws_frame)()
    result: lcurl.CURLcode = lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                                           ct.byref(rlen), ct.byref(meta))
    rlen = rlen.value
    meta = meta.contents
    if result:
        print("ws: curl_ws_recv returned %u, received %d" % (int(result), rlen),
              file=sys.stderr)
        return result

    if not (meta.flags & lcurl.CURLWS_PONG):
        print("recv_pong: wrong frame, got %d bytes rflags %x" % (rlen, meta.flags),
              file=sys.stderr)
        return lcurl.CURLE_RECV_ERROR

    print("ws: got PONG back", file=sys.stderr)
    if rlen == len(expected_payload) and buff[:rlen] == expected_payload[:rlen]:
        print("ws: got the same payload back", file=sys.stderr)
        return lcurl.CURLE_OK

    print("ws: did NOT get the same payload back", file=sys.stderr)
    return lcurl.CURLE_RECV_ERROR


def websocket_close(curl: ct.POINTER(lcurl.CURL)):
    # just close the connection
    sent = ct.c_size_t()
    result: lcurl.CURLcode = lcurl.ws_send(curl, b"", 0,
                                           ct.byref(sent), 0,
                                           lcurl.CURLWS_CLOSE)
    sent = sent.value
    print("ws: curl_ws_send returned %u, sent %u" %
          (int(result), sent), file=sys.stderr)


def pingpong(curl: ct.POINTER(lcurl.CURL), payload: bytes) -> lcurl.CURLcode:

    res: lcurl.CURLcode = ping(curl, payload)
    if res != lcurl.CURLE_OK:
        return res

    for i in range(10):
        print("Receive pong", file=sys.stderr)
        res = recv_pong(curl, payload)
        if res != lcurl.CURLE_AGAIN:
            break
        time.sleep(100 / 1000)
    else:
        res = lcurl.CURLE_RECV_ERROR

    websocket_close(curl)

    return res


def main(argv=sys.argv[1:]) -> int:
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if defined("CURL_DISABLE_WEBSOCKETS") and CURL_DISABLE_WEBSOCKETS:
        print("WebSockets not enabled in libcurl", file=sys.stderr)
        return 1
    # endif

    if len(argv) != 2:
        print(f"usage: python {app_name} url payload", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(prog=f"python {app_name}")
    parser.add_argument("url")
    parser.add_argument("payload")
    args = parser.parse_args(argv)

    url:     str = args.url
    payload: str = args.payload

    res: lcurl.CURLcode = lcurl.CURLE_OK

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
    if not curl:
        lcurl.global_cleanup()
        return int(res)  # !!! tu raczej blad a nie sukces !!!

    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    # use the callback style
    lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"ws-pingpong")
    lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 2)  # websocket style

    res = lcurl.easy_perform(curl)
    print("curl_easy_perform() returned %u" % int(res), file=sys.stderr)
    if res == lcurl.CURLE_OK:
        res = pingpong(curl, payload.encode("utf-8"))

    # always cleanup
    lcurl.easy_cleanup(curl)
    lcurl.global_cleanup()

    return int(res)


if __name__ == "__main__":
    sys.exit(main())
