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
Multi interface code doing two parallel HTTP transfers
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


#
# Simply download two HTTP files!
#

def main(argv=sys.argv[1:]):

    url1: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"
    url2: str = argv[1] if len(argv) >= 2 else "http://localhost/"

    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    curl:  ct.POINTER(lcurl.CURL) = lcurl.easy_init()
    curl2: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, [curl, curl2], mcurl):

        # set options
        lcurl.easy_setopt(curl,  lcurl.CURLOPT_URL, url1.encode("utf-8"))
        lcurl.easy_setopt(curl2, lcurl.CURLOPT_URL, url2.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl,  lcurl.CURLOPT_SSL_VERIFYPEER, 0)
            lcurl.easy_setopt(curl2, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

        # add the individual transfers
        lcurl.multi_add_handle(mcurl, curl)
        lcurl.multi_add_handle(mcurl, curl2)

        still_running = ct.c_int(1)  # keep number of running handles
        while still_running.value:
            mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            if still_running.value:
                # wait for activity, timeout or "nothing"
                mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mc:
                break

            while True:
                queued = ct.c_int()
                msg: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(mcurl,
                                                                       ct.byref(queued))
                if not msg: break
                msg = msg.contents

                if msg.msg == lcurl.CURLMSG_DONE:
                    # a transfer ended
                    print("Transfer completed", file=sys.stderr)

    return 0


sys.exit(main())
