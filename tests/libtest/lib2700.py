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

from typing import Tuple
import sys
import os
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa
from curl_trace import *  # noqa


if not defined("CURL_DISABLE_WEBSOCKETS") or not CURL_DISABLE_WEBSOCKETS:

    def descr_flags(flags: int) -> str:
        if flags & lcurl.CURLWS_TEXT:
            return "txt ---" if flags & lcurl.CURLWS_CONT else "txt fin"
        if flags & lcurl.CURLWS_BINARY:
            return "bin ---" if flags & lcurl.CURLWS_CONT else "bin fin"
        if flags & lcurl.CURLWS_PING:
            return "ping"
        if flags & lcurl.CURLWS_PONG:
            return "pong"
        if flags & lcurl.CURLWS_CLOSE:
            return "close"
        assert False
        return ""

    def send_header(curl: ct.POINTER(lcurl.CURL),
                    flags: int, size: int) -> lcurl.CURLcode:

        res: lcurl.CURLcode = lcurl.CURLE_OK

        nsent = ct.c_size_t()
        while True:
            res = lcurl.ws_send(curl, None, 0, ct.byref(nsent), size,
                                flags | lcurl.CURLWS_OFFSET)
            if res != lcurl.CURLE_AGAIN: break
            assert nsent.value == 0
        nsent = nsent.value
        if res:
            print("%s:%d lcurl.ws_send() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            assert nsent == 0
            return res

        assert nsent == 0

        return lcurl.CURLE_OK

    def recv_header(curl: ct.POINTER(lcurl.CURL),
                    flags:     ct.c_int,
                    offset:    lcurl.off_t,
                    bytesleft: lcurl.off_t) -> lcurl.CURLcode:

        res: lcurl.CURLcode = lcurl.CURLE_OK

        flags.value     = 0
        offset.value    = 0
        bytesleft.value = 0

        nread = ct.c_size_t()
        meta  = ct.POINTER(lcurl.ws_frame)()
        while True:
            res = lcurl.ws_recv(curl, None, 0, ct.byref(nread), ct.byref(meta))
            if res != lcurl.CURLE_AGAIN: break
            assert nread.value == 0
        nread = nread.value
        if res:
            print("%s:%d lcurl.ws_recv() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            assert nread == 0
            return res

        assert nread == 0
        assert bool(meta)

        meta = meta.contents

        assert meta.flags
        assert meta.offset == 0

        flags.value     = meta.flags
        offset.value    = meta.offset
        bytesleft.value = meta.bytesleft

        print("%s [%d]" % (descr_flags(meta.flags), meta.bytesleft), end="")
        if meta.bytesleft > 0: print(" ", end="")

        res = send_header(curl, meta.flags, meta.bytesleft)
        if res:
            return res

        return lcurl.CURLE_OK

    def send_chunk(curl: ct.POINTER(lcurl.CURL),
                   flags: int, buff: bytes, size: int,
                   offset: ct.c_size_t) -> lcurl.CURLcode:

        res: lcurl.CURLcode = lcurl.CURLE_OK

        nsent = ct.c_size_t()
        while True:
            res = lcurl.ws_send(curl,
                                buff[offset.value:], size - offset.value,
                                ct.byref(nsent), 0, flags)
            if res != lcurl.CURLE_AGAIN: break
            assert nsent.value == 0
        nsent = nsent.value
        if res:
            print("%s:%d lcurl.ws_send() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            assert nsent == 0
            return res

        assert nsent <= size - offset.value

        offset.value += nsent

        return lcurl.CURLE_OK

    def recv_chunk(curl: ct.POINTER(lcurl.CURL),
                   flags:     ct.c_int,
                   offset:    lcurl.off_t,
                   bytesleft: lcurl.off_t) -> lcurl.CURLcode:

        res: lcurl.CURLcode = lcurl.CURLE_OK

        buff  = (ct.c_char * 256)()
        nread = ct.c_size_t()
        meta  = ct.POINTER(lcurl.ws_frame)()
        while True:
            res = lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                                ct.byref(nread), ct.byref(meta))
            if res != lcurl.CURLE_AGAIN: break
            assert nread.value == 0
        nread = nread.value
        if res:
            print("%s:%d lcurl.ws_recv() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            assert nread == 0
            return res

        assert nread <= ct.sizeof(buff)
        assert bool(meta)

        meta = meta.contents

        assert meta.flags == flags.value
        assert meta.offset == offset.value
        assert meta.bytesleft == (bytesleft.value - nread)

        offset.value    += nread
        bytesleft.value -= nread

        sys.stdout.buffer.write(buff[:nread])

        sendoffset = ct.c_size_t(0)
        while sendoffset.value < nread:
            res = send_chunk(curl, flags.value, buff[:], nread, sendoffset)
            if res:
                return res

        return lcurl.CURLE_OK

    def recv_frame(curl: ct.POINTER(lcurl.CURL)) -> Tuple[lcurl.CURLcode, bool]:

        res: lcurl.CURLcode = lcurl.CURLE_OK
        stop: bool = False

        flags     = ct.c_int(0)
        offset    = lcurl.off_t(0)
        bytesleft = lcurl.off_t(0)

        res = recv_header(curl, flags, offset, bytesleft)
        if res:
            return res, stop
        flags = flags.value

        while bytesleft.value > 0:
            res = recv_chunk(curl, flags, offset, bytesleft)
            if res:
                return res, stop

        if flags & lcurl.CURLWS_CLOSE:
            stop = True

        print()

        return res, stop

    @curl_test_decorator
    def test(URL: str) -> lcurl.CURLcode:

        global libtest_debug_config, libtest_debug_cb

        res: lcurl.CURLcode = lcurl.CURLE_OK

        if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
            return TEST_ERR_MAJOR_BAD

        lcurl.global_trace(b"ws")
       
        curl: ct.POINTER(lcurl.CURL) = easy_init()

        with curl_guard(True, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"client/test2700")
            libtest_debug_config.nohex     = 1
            libtest_debug_config.tracetime = 1
            easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
            easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
            easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            easy_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 2)
            if not os.environ.get("LIB2700_AUTO_PONG"):
                easy_setopt(curl, lcurl.CURLOPT_WS_OPTIONS, lcurl.CURLWS_NOAUTOPONG)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK:  # pragma: no cover
                print("%s:%d lcurl.easy_perform() failed with code %d (%s)" %
                      (current_file(), current_line(),
                       res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
                raise guard.Break

            while True:
                res, stop = recv_frame(curl)
                if res or stop:
                    break

        return res

else:  # no WebSockets # pragma: no cover

    from curl_test import test_missing_support as test

# endif
