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

from typing import List
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# This is the 'proxyauth.c' test app posted by Shmulik Regev on the libcurl
# mailing list on 10 Jul 2007, converted to a test case.
#
# argv1 = URL
# argv2 = proxy
# argv3 = proxyuser:password
# argv4 = host name to use for the custom Host: header


NUM_HANDLES = 2

testcurls: List[ct.POINTER(lcurl.CURL)] = [ct.POINTER(lcurl.CURL)()] * NUM_HANDLES


def init(num: int, cm: ct.POINTER(lcurl.CURLM), URL: str,
         proxy: str, proxy_login: str, headers: ct.POINTER(lcurl.slist)) -> lcurl.CURLcode:

    global testcurls

    res: lcurl.CURLcode = lcurl.CURLE_OK

    curl = testcurls[num]
    try:
        res_easy_init(curl)
        if res: raise RuntimeError()

        res_easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        if res: raise RuntimeError()
        res_easy_setopt(curl, lcurl.CURLOPT_PROXY,
                        proxy.encode("utf-8") if proxy else None)
        if res: raise RuntimeError()
        res_easy_setopt(curl, lcurl.CURLOPT_PROXYUSERPWD,
                        proxy_login.encode("utf-8") if proxy_login else None)
        if res: raise RuntimeError()
        res_easy_setopt(curl, lcurl.CURLOPT_PROXYAUTH, lcurl.CURLAUTH_ANY)
        if res: raise RuntimeError()
        res_easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        if res: raise RuntimeError()
        res_easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        if res: raise RuntimeError()
        res_easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headers)  # custom Host:
        if res: raise RuntimeError()

        res_multi_add_handle(cm, curl)
        if res: raise RuntimeError()
    except:
        #init_failed:
        lcurl.easy_cleanup(curl)
        testcurls[num] = ct.POINTER(lcurl.CURL)()  # NULL
        return res  # failure

    return lcurl.CURLE_OK  # success


def loop(num: int, multi: ct.POINTER(lcurl.CURLM), URL: str,
         proxy: str, proxy_login: str, headers: ct.POINTER(lcurl.slist)) -> lcurl.CURLcode:

    global testcurls

    res: lcurl.CURLcode = lcurl.CURLE_OK

    res = init(num, multi, URL, proxy, proxy_login, headers)
    if res: return res

    still_running = ct.c_int(-1)
    while still_running.value:
        res = res_multi_perform(multi, ct.byref(still_running))
        if res: return res

        res = res_test_timedout()
        if res: return res

        if still_running.value:

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            max_fd = ct.c_int(-99)
            res = res_multi_fdset(multi,
                                  ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                  ct.byref(max_fd))
            max_fd = max_fd.value
            if res: return res
            # At this point, max_fd is guaranteed to be greater or equal than -1.

            curl_timeout = ct.c_long()
            res = res_multi_timeout(multi, ct.byref(curl_timeout))
            if res: return res
            curl_timeout = curl_timeout.value

            # At this point, curl_timeout is guaranteed to be greater or equal than -1.
            if curl_timeout != -1:
                curl_timeout = min(LONG_MAX, INT_MAX, curl_timeout)
                timeout = lcurl.timeval(tv_sec=curl_timeout // 1000,
                                        tv_usec=(curl_timeout % 1000) * 1000)
            else:
                timeout = lcurl.timeval(tv_sec=5, tv_usec=0)  # 5 sec
            res = res_select_test(max_fd + 1,
                                  ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                  ct.byref(timeout))
            if res: return res

        while True:
            msgs_left = ct.c_int()
            msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                    ct.byref(msgs_left))
            if not msgp: break
            msg = msgp.contents

            if msg.msg == lcurl.CURLMSG_DONE:
                curl: ct.POINTER(lcurl.CURL) = msg.easy_handle
                print("fd_read: %d - %s" %
                      (msg.data.result,
                       lcurl.easy_strerror(msg.data.result).decode("utf-8")), file=sys.stderr)
                lcurl.multi_remove_handle(multi, curl)
                lcurl.easy_cleanup(curl)
                for i in range(len(testcurls)):
                    if testcurls[i] == curl:
                        testcurls[i] = ct.POINTER(lcurl.CURL)()  # NULL
                        break
            else:
                print("fd_excep: libcurl.CURLMsg (%d)" % msg.msg, file=sys.stderr)

        res = res_test_timedout()
        if res: return res

    return lcurl.CURLE_OK


@curl_test_decorator
def test(URL: str,
         host: str,
         proxy: str = None,
         proxy_login: str = None) -> lcurl.CURLcode:

    global testcurls

    res: lcurl.CURLcode = lcurl.CURLE_OK

    for i in range(len(testcurls)):
        testcurls[i] = ct.POINTER(lcurl.CURL)()  # NULL

    start_test_timing()

    res = res_global_init(lcurl.CURL_GLOBAL_ALL)
    if res: return res

    multi: ct.POINTER(lcurl.CURLM) = res_multi_init()

    with curl_guard(True, mcurl=multi) as guard:
        if res: return res

        # now add a custom Host: header
        headers: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                           b"Host: %s" % host.encode("utf-8"))
        if not headers:
            print("libcurl.slist_append() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD
        guard.add_slist(headers)

        res = loop(0, multi, URL, proxy, proxy_login, headers)
        if res == lcurl.CURLE_OK:
            print("lib540: now we do the request again", file=sys.stderr)
            res = loop(1, multi, URL, proxy, proxy_login, headers)

        # proper cleanup sequence - type PB
        for curl in testcurls:
            lcurl.multi_remove_handle(multi, curl)
            lcurl.easy_cleanup(curl)

    return res
