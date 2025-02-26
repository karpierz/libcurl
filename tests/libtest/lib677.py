# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 1998 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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

TIMEOUT = 20  # 50 # in secs

testcmd = b"A1 IDLE\r\n"
testbuf = (ct.c_char * 1024)()


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start: lcurl.time_t = time.time()

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 1)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        mres: lcurl.CURLMcode = lcurl.multi_add_handle(multi, curl)
        if mres != lcurl.CURLM_OK:
            return TEST_ERR_MAJOR_BAD

        state: int = 0

        pos:  int = 0
        sock: int = lcurl.CURL_SOCKET_BAD
        while time.time() - start < float(TIMEOUT):

            running = ct.c_int()
            multi_perform(multi, ct.byref(running))

            while True:
                msgs_left = ct.c_int()
                msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                        ct.byref(msgs_left))
                if not msgp: break
                msg = msgp.contents

                if msg.msg == lcurl.CURLMSG_DONE and msg.easy_handle == curl:
                    socket = lcurl.socket_t(lcurl.CURL_SOCKET_BAD)
                    lcurl.easy_getinfo(curl, lcurl.CURLINFO_ACTIVESOCKET, ct.byref(socket))
                    sock = socket.value
                    if sock == lcurl.CURL_SOCKET_BAD:
                        return TEST_ERR_MAJOR_BAD
                    print("Connected fine, extracted socket. Moving on")

            waitfd: lcurl.waitfd = lcurl.waitfd()
            if sock != lcurl.CURL_SOCKET_BAD:
                socket = lcurl.socket_t(lcurl.CURL_SOCKET_BAD)
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_ACTIVESOCKET, ct.byref(socket))
                sock = socket.value
                waitfd.fd      = sock
                waitfd.events  = (lcurl.CURL_WAIT_POLLIN if state else lcurl.CURL_WAIT_POLLOUT)
                waitfd.revents = 0

            lcurl.multi_wait(multi, ct.byref(waitfd),
                             (0 if sock == lcurl.CURL_SOCKET_BAD else 1), 50,
                             ct.byref(running))
            #print("@@@@ waitfd:\t", sock, (waitfd.revents & waitfd.events), state)
            if sock == lcurl.CURL_SOCKET_BAD or not (waitfd.revents & waitfd.events):
                continue

            size = 0
            if not state:
                #print("@@@@", testcmd[pos:])
                size = ct.c_size_t(0)
                ec: lcurl.CURLcode = lcurl.easy_send(curl, testcmd[pos:], len(testcmd) - pos,
                                                     ct.byref(size))
                size = size.value
                if ec == lcurl.CURLE_AGAIN:
                    continue
                if ec != lcurl.CURLE_OK:
                    print("libcurl.easy_send() failed, with code %d (%s)" %
                          (ec, lcurl.easy_strerror(ec).decode("utf-8")), file=sys.stderr)
                    res = ec
                    raise guard.Break
                if size > 0:
                    pos += size
                else:
                    pos = 0
                if pos == len(testcmd):
                    state += 1
                    pos = 0
            elif pos < ct.sizeof(testbuf):
                size = ct.c_size_t(0)
                ec: lcurl.CURLcode = lcurl.easy_recv(curl, testbuf[pos:], ct.sizeof(testbuf) - pos,
                                                     ct.byref(size))
                size = size.value
                if ec == lcurl.CURLE_AGAIN:
                    continue
                if ec != lcurl.CURLE_OK:
                    print("libcurl.easy_recv() failed, with code %d (%s)" %
                          (ec, lcurl.easy_strerror(ec).decode("utf-8")), file=sys.stderr)
                    res = ec
                    raise guard.Break
                if size > 0:
                    pos += size
            if size <= 0:
                sock = lcurl.CURL_SOCKET_BAD

        if state:
            sys.stdout.fwrite(testbuf[:pos])
            print()

    return res
