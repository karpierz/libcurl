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
Use CURLOPT_CONNECT_TO to connect to "wrong" hostname
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


def main(argv=sys.argv[1:]):

    # Each single string should be written using the format
    # HOST:PORT:CONNECT-TO-HOST:CONNECT-TO-PORT where HOST is the host of the
    # request, PORT is the port of the request, CONNECT-TO-HOST is the host name
    # to connect to, and CONNECT-TO-PORT is the port to connect to.

    # instead of curl.se:443, it resolves and uses example.com:443 but in other
    # aspects work as if it still is curl.se
    host = ct.POINTER(lcurl.slist)()
    host = lcurl.slist_append(host, b"curl.se:443:example.com:443")

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_CONNECT_TO, host)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, b"https://curl.se/")
        # since this connects to the wrong host, checking the host name in the
        # server certificate fails, so unless we disable the check libcurl
        # returns CURLE_PEER_FAILED_VERIFICATION
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

        # Letting the wrong host name in the certificate be okay, the transfer
        # goes through but (most likely) causes a 404 or similar because it sends
        # an unknown name in the Host: header field
        res: int = lcurl.easy_perform(curl)

    lcurl.slist_free_all(host)

    return int(res)


sys.exit(main())
