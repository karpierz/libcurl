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


if defined("LIB585"):

    testcounter: int
    sock_obj = None


    @lcurl.opensocket_callback
    def tst_opensocket(clientp, purpose, address):
        address = address.contents
        global testcounter
        global sock_obj
        testcounter += 1
        print("[OPEN] counter: %d" % testcounter)
        sock_obj = socket.socket(address.family, address.socktype, address.protocol)
        return sock_obj.fileno()


    @lcurl.closesocket_callback
    def tst_closesocket(clientp, sock):
        global testcounter
        global sock_obj
        print("[CLOSE] counter: %d" % testcounter)
        testcounter -= 1
        try:
            sock_obj.close()
        except:
            return -1
        finally:
            sock_obj = None
        return 0


    def setupcallbacks(curl: ct.POINTER(lcurl.CURL)):
        global testcounter
        global sock_obj
        lcurl.easy_setopt(curl, lcurl.CURLOPT_OPENSOCKETFUNCTION,  tst_opensocket)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CLOSESOCKETFUNCTION, tst_closesocket)
        testcounter  = 0
        sock_obj = None

else:

    def setupcallbacks(curl: ct.POINTER(lcurl.CURL)):
        pass

# endif


@curl_test_decorator
def test(URL: str, filename: str = None, ftp_type: str = None) -> lcurl.CURLcode:
    if filename: filename = str(filename)

    global libtest_debug_config, libtest_debug_cb

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        libtest_debug_config.nohex     = 1
        libtest_debug_config.tracetime = 1
        test_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
        test_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        if ftp_type and ftp_type == "activeftp":
            test_setopt(curl, lcurl.CURLOPT_FTPPORT, b"-")

        setupcallbacks(curl)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        ipstr = ct.c_char_p(None)
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_PRIMARY_IP, ct.byref(ipstr))
        if filename:
            with open(filename, "wb") as moo:

                moo.write(b"IP %s\n" % ipstr.value)

                time_namelookup    = lcurl.off_t()
                time_connect       = lcurl.off_t()
                time_pretransfer   = lcurl.off_t()
                time_posttransfer  = lcurl.off_t()
                time_starttransfer = lcurl.off_t()
                time_total         = lcurl.off_t()
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_NAMELOOKUP_TIME_T,    ct.byref(time_namelookup))
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_CONNECT_TIME_T,       ct.byref(time_connect))
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_PRETRANSFER_TIME_T,   ct.byref(time_pretransfer))
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_POSTTRANSFER_TIME_T,  ct.byref(time_posttransfer))
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_STARTTRANSFER_TIME_T, ct.byref(time_starttransfer))
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_TOTAL_TIME_T,         ct.byref(time_total))
                time_namelookup    = time_namelookup.value
                time_connect       = time_connect.value
                time_pretransfer   = time_pretransfer.value
                time_posttransfer  = time_posttransfer.value
                time_starttransfer = time_starttransfer.value
                time_total         = time_total.value

                # since the timing will always vary we only compare relative
                # differences between these 5 times
                if time_namelookup > time_connect:
                    moo.write((b"namelookup vs connect: %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8")
                               + b".%06ld %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8") + b".%06ld\n") %
                              (time_namelookup // 1_000_000, time_namelookup % 1_000_000,
                               time_connect    // 1_000_000, time_connect    % 1_000_000))
                if time_connect > time_pretransfer:
                    moo.write((b"connect vs pretransfer: %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8")
                               + b".%06ld %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8") + b".%06ld\n") %
                              (time_connect     // 1_000_000, time_connect     % 1_000_000,
                               time_pretransfer // 1_000_000, time_pretransfer % 1_000_000))
                if time_pretransfer > time_posttransfer:
                    moo.write((b"pretransfer vs posttransfer: %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8")
                               + b".%06ld %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8") + b".%06ld\n") %
                              (time_pretransfer  // 1_000_000, time_pretransfer  % 1_000_000,
                               time_posttransfer // 1_000_000, time_posttransfer % 1_000_000))
                if time_pretransfer > time_starttransfer:
                    moo.write((b"pretransfer vs starttransfer: %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8")
                               + b".%06ld %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8") + b".%06ld\n") %
                              (time_pretransfer   // 1_000_000, time_pretransfer   % 1_000_000,
                               time_starttransfer // 1_000_000, time_starttransfer % 1_000_000))
                if time_starttransfer > time_total:
                    moo.write((b"starttransfer vs total: %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8")
                               + b".%06ld %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8") + b".%06ld\n") %
                              (time_starttransfer // 1_000_000, time_starttransfer % 1_000_000,
                               time_total         // 1_000_000, time_total         % 1_000_000))
                if time_posttransfer > time_total:
                    moo.write((b"posttransfer vs total: %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8")
                               + b".%06ld %" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("utf-8") + b".%06ld\n") %
                              (time_posttransfer // 1_000_000, time_posttransfer % 1_000_000,
                               time_total        // 1_000_000, time_total        % 1_000_000))

    return res
