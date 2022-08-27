#***************************************************************************
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
#***************************************************************************

"""
Import and export cookies with COOKIELIST.
"""

import sys
import time
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def print_cookies(curl: ct.POINTER(lcurl.CURL)):

    print("Cookies, curl knows:")
    cookies = ct.POINTER(lcurl.slist)()
    res: lcurl.CURLcode = lcurl.easy_getinfo(curl,
                                             lcurl.CURLINFO_COOKIELIST,
                                             ct.byref(cookies))
    if res != lcurl.CURLE_OK:
        print("Curl curl_easy_getinfo failed: %s" %
              lcurl.easy_strerror(res).decode("utf-8"),
              file=sys.stderr)
        assert res == lcurl.CURLE_OK

    try:
        nc = cookies ; i = 1
        while nc:
            nc = nc.contents
            print("[%d]: %s" % (i, nc.data.decode("utf-8")))
            nc = nc.next ; i += 1
        if i == 1:
            print("(none)")
    finally:
        lcurl.slist_free_all(cookies)


def main(argv=sys.argv[1:]):

    url:   str = argv[0] if len(argv) >= 1 else "https://www.example.com/"
    chost: str = ".".join(url.rstrip("/").rpartition("//")[2].rsplit(".", 2)[-2:])

    res: lcurl.CURLcode = lcurl.CURLE_OK

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl:
            print("Curl init failed!", file=sys.stderr)
            return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # start cookie engine
        lcurl.easy_setopt(curl, lcurl.CURLOPT_COOKIEFILE, b"")

        # Perform the request
        res = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)
            return 1

        print_cookies(curl)

        print("Erasing curl's knowledge of cookies!")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_COOKIELIST, "ALL")

        print_cookies(curl)

        print("-----------------------------------------------\n"
              "Setting a cookie \"PREF\" via cookie interface:")
        # Netscape format cookie
        nline = "%s\t%s\t%s\t%s\t%.0f\t%s\t%s" % (
                "." + chost, "TRUE", "/", "FALSE",
                time.time() + ((8 * 60 + 42) * 60 + 17),
                "PREF",
                "hello example, i like you very much!")
        res = lcurl.easy_setopt(curl,
                                lcurl.CURLOPT_COOKIELIST, nline.encode("utf-8"))

        if res != lcurl.CURLE_OK:
            print("Curl curl_easy_setopt failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"),
                  file=sys.stderr)
            return 1

        # HTTP-header style cookie. If you use the Set-Cookie format and do not
        # specify a domain then the cookie is sent for any domain and will not be
        # modified, likely not what you intended. Starting in 7.43.0 any-domain
        # cookies will not be exported either. For more information refer to the
        # CURLOPT_COOKIELIST documentation.
        nline = ("Set-Cookie: OLD_PREF=3d141414bf4209321; "
                 "expires=Sun, 17-Jan-2038 19:14:07 GMT; path=/; "
                 "domain=.%s" % chost)
        res = lcurl.easy_setopt(curl,
                                lcurl.CURLOPT_COOKIELIST, nline.encode("utf-8"))

        if res != lcurl.CURLE_OK:
            print("Curl curl_easy_setopt failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"),
                  file=sys.stderr)
            return 1

        print_cookies(curl)

        # Perform the request
        res = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)
            return 1

    return 0


sys.exit(main())
