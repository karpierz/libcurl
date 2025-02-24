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


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 1)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        transfers: int = 0
        while True:
            res = lcurl.easy_perform(curl)

            if not res:
                # we are connected, now get an HTTP document the raw way
                request = (b"GET /556 HTTP/1.1\r\n"
                           b"Host: ninja\r\n"
                           b"\r\n")

                sbuf  = request
                sblen = len(sbuf)
                while True:
                    buf = (ct.c_char * 1024)()

                    if sblen:
                        nwritten = ct.c_size_t(0)
                        res = lcurl.easy_send(curl, sbuf, sblen, ct.byref(nwritten))
                        if res and res != lcurl.CURLE_AGAIN:
                            break
                        nwritten = nwritten.value
                        if nwritten > 0:
                            sbuf  += sbuf[nwritten:]
                            sblen -= nwritten

                    # busy-read like crazy
                    nread = ct.c_size_t(0)
                    res = lcurl.easy_recv(curl, buf, ct.sizeof(buf), ct.byref(nread))
                    nread = nread.value
                    if nread:
                        # send received stuff to stdout
                        try:
                            real_nread = sys.stdout.buffer.write(bytes(buf[:nread]))
                        except OSError as exc:
                            print("write() failed: errno %d (%s)" %
                                  (exc.errno, exc.strerror), file=sys.stderr)
                            res = TEST_ERR_FAILURE
                            break
                        if real_nread != nread:
                            print("write() failed: wrote %d bytes, should be %d" %
                                  (real_nread, nread), file=sys.stderr)
                            res = TEST_ERR_FAILURE
                            break

                    if res == lcurl.CURLE_AGAIN: continue
                    if res != lcurl.CURLE_OK or nread == 0:
                        break

                if res and res != lcurl.CURLE_AGAIN:
                    res = TEST_ERR_FAILURE

            transfers += 1

            if defined("LIB696"):
                # perform the transfer a second time
                if not res and transfers < 2:
                     continue
            # endif
            break

    return res
