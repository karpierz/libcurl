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
from curl_trace import *  # noqa


if not defined("CURL_DISABLE_WEBSOCKETS") or not CURL_DISABLE_WEBSOCKETS:

    def websocket(curl: ct.POINTER(lcurl.CURL)):
        global out_file
        with open(out_file, "wb") as save:
            # Three 4097-bytes frames are expected, 12291 bytes
            i = 0
            while i < 12291:
                buff  = (ct.c_char * 256)()
                nread = ct.c_size_t()
                meta  = ct.POINTER(lcurl.ws_frame)()
                result: lcurl.CURLcode = lcurl.ws_recv(curl, buff, ct.sizeof(buff),
                                                       ct.byref(nread), ct.byref(meta))
                if result:
                    if result == lcurl.CURLE_AGAIN:
                        # crude busy-loop
                        continue
                    print("libcurl.ws_recv returned %d", result)
                    return

                nread = nread.value
                meta  = meta.contents
                print("%d: nread %lu Age %d Flags %x "
                      "Offset %ld "
                      "Bytesleft %ld" %
                      (i, nread, meta.age, meta.flags, meta.offset, meta.bytesleft))

                save.write(buff[0:nread])
                i += meta.len

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
    def test(URL: str, output_file: str) -> lcurl.CURLcode:
        output_file = str(output_file)

        global libtest_debug_config, libtest_debug_cb

        global out_file
        out_file = output_file

        res: lcurl.CURLcode = lcurl.CURLE_OK

        if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
            return TEST_ERR_MAJOR_BAD

        curl: ct.POINTER(lcurl.CURL) = easy_init()

        with curl_guard(True, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # use the callback style
            lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"websocket/2304")
            libtest_debug_config.nohex     = 1
            libtest_debug_config.tracetime = 1
            lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
            lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
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
