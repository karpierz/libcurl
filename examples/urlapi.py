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
Set working URL with CURLU *.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 80, 0):
    print("This example requires curl 7.80.0 or later", file=sys.stderr)
    sys.exit(-1)


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "http://example.com/path/index.html"

    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # init Curl URL
        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        uc:   ct.CURLUcode = lcurl.url_set(urlp, lcurl.CURLUPART_URL,
                                           url.encode("utf-8"), 0)
        if uc:
            print("libcurl.url_set() failed: %s" %
                  lcurl.url_strerror(uc).decode("utf-8"),
                  file=sys.stderr)
            lcurl.url_cleanup(urlp)
            return 0

        # set urlp to use as working URL
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CURLU, urlp)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # Cleanup
        lcurl.url_cleanup(urlp)

    return 0


sys.exit(main())
