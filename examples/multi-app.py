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
A basic application source code using the multi interface doing two
transfers in parallel.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


HANDLECOUNT = 2  # Number of simultaneous transfers
HTTP_HANDLE = 0  # Index for the HTTP transfer
FTP_HANDLE  = 1  # Index for the FTP transfer


#
# Download a HTTP file and upload an FTP file simultaneously.
#

def main(argv=sys.argv[1:]):

    http_url: str = argv[0] if len(argv) >= 1 else "https://example.com"
    ftp_url:  str = argv[1] if len(argv) >= 2 else "ftp://example.com"

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)

    # Allocate one CURL handle per transfer
    curl_handles = (ct.POINTER(lcurl.CURL) * HANDLECOUNT)()
    for i in range(len(curl_handles)):
        curl_handles[i] = lcurl.easy_init()

    # set the options (I left out a few, you will get the point anyway)
    lcurl.easy_setopt(curl_handles[HTTP_HANDLE], lcurl.CURLOPT_URL, http_url.encode("utf-8"))
    if defined("SKIP_PEER_VERIFICATION"):
        lcurl.easy_setopt(curl_handles[HTTP_HANDLE], lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    lcurl.easy_setopt(curl_handles[FTP_HANDLE], lcurl.CURLOPT_URL, ftp_url.encode("utf-8"))
    lcurl.easy_setopt(curl_handles[FTP_HANDLE], lcurl.CURLOPT_UPLOAD, 1)

    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    # add the individual transfers
    for curl in curl_handles:
        lcurl.multi_add_handle(mcurl, curl)

    still_running = ct.c_int(1)  # keep number of running handles
    while still_running.value:
        mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
        if still_running.value:
            # wait for activity, timeout or "nothing"
            mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
        if mc:
            break

    # See how the transfers went
    while True:
        # for picking up messages with the transfer status
        msgs_left = ct.c_int(0)  # how many messages are left
        msg: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(mcurl,
                                                               ct.byref(msgs_left))
        if not msg: break
        msg = msg.contents

        if msg.msg != lcurl.CURLMSG_DONE:
            continue

        # Find out which handle this message is about
        for idx, curl in enumerate(curl_handles):
            found = (id(msg.easy_handle.contents) == id(curl.contents))
            if found: break
        else: idx = len(curl_handles)

        if idx == HTTP_HANDLE:
            print("HTTP transfer completed with status %d" % msg.data.result)
        elif idx == FTP_HANDLE:
            print("FTP transfer completed with status %d" % msg.data.result)

    # remove the transfers and cleanup the handles
    for curl in curl_handles:
        lcurl.multi_remove_handle(mcurl, curl)
        lcurl.easy_cleanup(curl)

    lcurl.multi_cleanup(mcurl)

    lcurl.global_cleanup()

    return 0


sys.exit(main())
