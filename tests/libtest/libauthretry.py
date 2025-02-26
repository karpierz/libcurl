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

from typing import Optional
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# argv1 = URL
# argv2 = main auth type
# argv3 = second auth type


def send_request(curl: ct.POINTER(lcurl.CURL), url: str, seq: int,
                 auth_scheme: int, user_login: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode
    full_url: str = "%s/%04d" % (url.rstrip("/"), seq)

    print("Sending new request %d to %s with credential %s (auth %ld)" %
          (seq, full_url, user_login, auth_scheme), file=sys.stderr)

    test_setopt(curl, lcurl.CURLOPT_URL, full_url.encode("utf-8"))
    test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
    test_setopt(curl, lcurl.CURLOPT_HEADER,  1)
    test_setopt(curl, lcurl.CURLOPT_HTTPGET, 1)
    test_setopt(curl, lcurl.CURLOPT_USERPWD, user_login.encode("utf-8"))
    test_setopt(curl, lcurl.CURLOPT_HTTPAUTH, auth_scheme)

    res = lcurl.easy_perform(curl)

    return res


def send_wrong_password(curl: ct.POINTER(lcurl.CURL), url: str, seq: int,
                        auth_scheme: int) -> lcurl.CURLcode:
    return send_request(curl, url, seq, auth_scheme, "testuser:wrongpass")


def send_right_password(curl: ct.POINTER(lcurl.CURL), url: str, seq: int,
                        auth_scheme: int) -> lcurl.CURLcode:
    return send_request(curl, url, seq, auth_scheme, "testuser:testpass")


def parse_auth_name(arg: Optional[str]) -> int:
    if not arg:
        return lcurl.CURLAUTH_NONE
    barg = arg.encode("utf-8")
    if barg == b"basic":
        return lcurl.CURLAUTH_BASIC
    if barg == b"digest":
        return lcurl.CURLAUTH_DIGEST
    if barg == b"ntlm":
        return lcurl.CURLAUTH_NTLM
    return lcurl.CURLAUTH_NONE


@curl_test_decorator
def test(URL: str,
         main_auth_scheme: str = None,
         fallback_auth_scheme: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    main_auth_scheme     = parse_auth_name(main_auth_scheme)
    fallback_auth_scheme = parse_auth_name(fallback_auth_scheme)

    if (main_auth_scheme     == lcurl.CURLAUTH_NONE or
        fallback_auth_scheme == lcurl.CURLAUTH_NONE):
        print("auth schemes not found on commandline", file=sys.stderr)
        return TEST_ERR_MAJOR_BAD

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    # Send wrong password, then right password

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        res = send_wrong_password(curl, URL, 100, main_auth_scheme)
        if res != lcurl.CURLE_OK: raise guard.Break

        res = send_right_password(curl, URL, 200, fallback_auth_scheme)
        if res != lcurl.CURLE_OK: raise guard.Break

        lcurl.easy_cleanup(curl)

        # Send wrong password twice, then right password

        curl = easy_init()
        if not curl: return TEST_ERR_EASY_INIT

        res = send_wrong_password(curl, URL, 300, main_auth_scheme)
        if res != lcurl.CURLE_OK: raise guard.Break

        res = send_wrong_password(curl, URL, 400, fallback_auth_scheme)
        if res != lcurl.CURLE_OK: raise guard.Break

        res = send_right_password(curl, URL, 500, fallback_auth_scheme)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
