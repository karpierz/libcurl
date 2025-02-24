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
A basic application source code using the multi interface doing two
transfers in parallel without lcurl.multi_wait/poll.
"""

import sys
import ctypes as ct
import select
import time

import libcurl as lcurl
from curl_utils import *  # noqa

HANDLECOUNT = 2  # Number of simultaneous transfers

HTTP_HANDLE = 0  # Index for the HTTP transfer
FTP_HANDLE  = 1  # Index for the FTP transfer


#
# Download an HTTP file and upload an FTP file simultaneously.
#

def main(argv=sys.argv[1:]):

    http_url: str = argv[0] if len(argv) >= 1 else "https://example.com"
    ftp_url:  str = argv[1] if len(argv) >= 2 else "ftp://ftp.gnu.org/gnu/binutils/"

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)

    # Allocate one curl handle per transfer
    curl_handles = (ct.POINTER(lcurl.CURL) * HANDLECOUNT)()
    for i in range(len(curl_handles)):
        curl_handles[i] = lcurl.easy_init()

    # set the options (I left out a few, you get the point anyway)
    lcurl.easy_setopt(curl_handles[HTTP_HANDLE], lcurl.CURLOPT_URL, http_url.encode("utf-8"))
    if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
        lcurl.easy_setopt(curl_handles[HTTP_HANDLE], lcurl.CURLOPT_SSL_VERIFYPEER, 0)

    lcurl.easy_setopt(curl_handles[FTP_HANDLE], lcurl.CURLOPT_URL, ftp_url.encode("utf-8"))
    lcurl.easy_setopt(curl_handles[FTP_HANDLE], lcurl.CURLOPT_UPLOAD, 1)

    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    with curl_guard(True, None, mcurl) as guard:

        # add the individual transfers
        for curl in curl_handles:
            lcurl.multi_add_handle(mcurl, curl)

        still_running = ct.c_int(0)  # keep number of running handles
        # we start some action by calling perform right away
        lcurl.multi_perform(mcurl, ct.byref(still_running))

        while still_running.value:

            # set a suitable timeout to play around with

            curl_timeout = ct.c_long(-1)
            lcurl.multi_timeout(mcurl, ct.byref(curl_timeout))
            curl_timeout = curl_timeout.value

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            max_fd = ct.c_int(-1)
            # get file descriptors from the transfers
            mc: lcurl.CURLMcode = lcurl.multi_fdset(mcurl,
                                      ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                      ct.byref(max_fd))
            max_fd = max_fd.value
            if mc != lcurl.CURLM_OK:
                print("libcurl.multi_fdset() failed, code %d." % mc, file=sys.stderr)
                break

            # On success the value of max_fd is guaranteed to be >= -1. We call
            # select(max_fd + 1, ...); specially in case of (max_fd == -1) there are
            # no fds ready yet so we call select(0, ...) --or Sleep() on Windows--
            # to sleep 100ms, which is the minimum suggested value in the
            # curl_multi_fdset() doc.

            timeout = (lcurl.timeval(tv_sec=curl_timeout // 1000,
                                     tv_usec=(curl_timeout % 1000) * 1000)
                       if 0 <= curl_timeout < 1000 else
                       lcurl.timeval(tv_sec=1, tv_usec=0))  # 1 sec
            rc: int  # select() return code
            if max_fd == -1:
                time.sleep(100 / 1000)
                rc = 0
            else:
                rc = lcurl.select(max_fd + 1,
                                  ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                  ct.byref(timeout))
                if rc == -1:
                    # select error
                    continue

            lcurl.multi_perform(mcurl, ct.byref(still_running))

        # See how the transfers went
        while True:
            # for picking up messages with the transfer status
            msgs_left = ct.c_int(0)  # how many messages are left
            msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(mcurl,
                                                                    ct.byref(msgs_left))
            if not msgp: break
            msg = msgp.contents

            if msg.msg != lcurl.CURLMSG_DONE:
                continue

            # Find out which handle this message is about
            for idx, curl in enumerate(curl_handles):
                found = (msg.easy_handle == curl)
                if found: break
            else: idx = len(curl_handles)

            if idx == HTTP_HANDLE:
                print("HTTP transfer completed with status %d" % msg.data.result)
            elif idx == FTP_HANDLE:
                print("FTP transfer completed with status %d" % msg.data.result)

        lcurl.multi_cleanup(mcurl)
        # Free the curl handles
        for curl in curl_handles:
            lcurl.easy_cleanup(curl)

    return 0


sys.exit(main())
