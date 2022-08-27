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
Use CURLOPT_RESOLVE to feed custom IP addresses for given host name + port
number combinations.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def main(argv=sys.argv[1:]):

    url:   str = argv[0] if len(argv) >= 1 else "https://example.com"
    rhost: str = argv[1] if len(argv) >= 2 else "93.184.216.34:443:127.0.0.1"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # Each single name resolve string should be written using the format
        # HOST:PORT:ADDRESS where HOST is the name libcurl will try to resolve,
        # PORT is the port number of the service where libcurl wants to connect to
        # the HOST and ADDRESS is the numerical IP address
        host: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                           rhost.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_RESOLVE, host)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    # Cleanup
    lcurl.slist_free_all(host)

    return int(res)


sys.exit(main())
