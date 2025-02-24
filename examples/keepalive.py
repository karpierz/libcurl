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
Use the TCP keep-alive options
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://curl.se/"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        # enable TCP keep-alive for this transfer
        lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPALIVE, 1)
        # keep-alive idle time to 120 seconds
        lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPIDLE, 120)
        # interval time between keep-alive probes: 60 seconds
        lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPINTVL, 60)
        # maximum number of keep-alive probes: 3
        lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPCNT, 3)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))

        res: int = lcurl.easy_perform(curl)

    return int(res)


sys.exit(main())
