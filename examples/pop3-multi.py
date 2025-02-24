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
Get POP3 email using the multi interface
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


# This is a simple example showing how to retrieve mail using libcurl's POP3
# capabilities. It builds on the pop3-retr.c example to demonstrate how to use
# libcurl's multi interface.

def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "pop3://pop.example.com/1"

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    curl:  ct.POINTER(lcurl.CURL)  = lcurl.easy_init()

    with curl_guard(True, curl, mcurl) as guard:
        if not curl:  return 1
        if not mcurl: return 2

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This retrieves message 1 from the user's mailbox
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))

        # Tell the multi stack about our easy handle
        lcurl.multi_add_handle(mcurl, curl)

        still_running = ct.c_int(1)
        while still_running.value:

            mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            # wait for activity, timeout or "nothing"
            if still_running.value: mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mc:
                break

    return 0


sys.exit(main())
