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
Using the multi interface to do a single download
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


#
# Simply download a HTTP file.
#

def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    curl:  ct.POINTER(lcurl.CURL)  = lcurl.easy_init()

    with curl_guard(True, curl, mcurl):

        # set the options (I left out a few, you will get the point anyway)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

        # add the individual transfers
        lcurl.multi_add_handle(mcurl, curl)

        still_running = ct.c_int(1)  # keep number of running handles
        while still_running.value:
            mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            if not mc:
                # wait for activity, timeout or "nothing"
                mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mc:
                print("libcurl.multi_poll() failed, code %d." % mc,
                      file=sys.stderr)
                break

    return 0


sys.exit(main())
