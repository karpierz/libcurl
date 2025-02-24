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

# This test case is based on the sample code provided by Saqib Ali
# https://curl.se/mail/lib-2011-03/0066.html


@curl_test_decorator
def test(URL: str,
         user_login: str = None,
         client_pub_key: str = None,
         client_priv_key: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_USERPWD,
                           user_login.encode("utf-8") if user_login else None)
        easy_setopt(curl, lcurl.CURLOPT_SSH_PUBLIC_KEYFILE,
                          client_pub_key.encode("utf-8") if client_pub_key else None)
        easy_setopt(curl, lcurl.CURLOPT_SSH_PRIVATE_KEYFILE,
                          client_priv_key.encode("utf-8") if client_priv_key else None)
        easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1);
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_INFILESIZE, 5)

        multi_add_handle(multi, curl)

        # this tests if removing an easy handle immediately after multi
        # perform has been called succeeds or not.

        print("libcurl.multi_perform()...", file=sys.stderr)

        still_running = ct.c_int()
        multi_perform(multi, ct.byref(still_running))

        print("libcurl.multi_perform() succeeded", file=sys.stderr)

        print("libcurl.multi_remove_handle()...", file=sys.stderr)
        mres: lcurl.CURLMcode = lcurl.multi_remove_handle(multi, curl)
        if mres:
            print("libcurl.multi_remove_handle() failed, with code %d" % mres,
                  file=sys.stderr)
            res = TEST_ERR_MULTI
        else:
            print("libcurl.multi_remove_handle() succeeded", file=sys.stderr)

    return res
