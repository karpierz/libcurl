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
Simple HTTPS GET
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://example.com/"

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            # If you want to connect to a site who is not using a certificate that is
            # signed by one of the certs in the CA bundle you have, you can skip the
            # verification of the server's certificate. This makes the connection
            # A LOT LESS SECURE.
            #
            # If you have a CA cert for the server stored someplace else than in the
            # default bundle, then the CURLOPT_CAPATH option might come handy for
            # you.
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        if defined("SKIP_HOSTNAME_VERIFICATION"):
            # If the site you are connecting to uses a different host name that what
            # they have mentioned in their server certificate's commonName (or
            # subjectAltName) fields, libcurl refuses to connect. You can skip this
            # check, but it makes the connection insecure.
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
        # cache the CA cert bundle in memory for a week
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CA_CACHE_TIMEOUT, 604800)

        # Perform the request, res gets the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
