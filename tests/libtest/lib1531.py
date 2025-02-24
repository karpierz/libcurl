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

import sys
import ctypes as ct
import time

import libcurl as lcurl
from curl_test import *  # noqa
#include "timediff.h"


test_data = b".abc\0xyz"


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    # Allocate one curl handle per transfer
    curl: ct.POINTER(lcurl.CURL) = easy_init()
    # init a multi stack
    multi: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        # add the individual transfer
        lcurl.multi_add_handle(multi, curl)

        # set the options (I left out a few, you'll get the point anyway)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE_LARGE, len(test_data))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, test_data)

        # we start some action by calling perform right away
        still_running = ct.c_int()  # keep number of running handles
        lcurl.multi_perform(multi, ct.byref(still_running))

        abort_on_test_timeout()

        while True:

            curl_timeout = ct.c_long(-1)
            lcurl.multi_timeout(multi, ct.byref(curl_timeout))
            curl_timeout = curl_timeout.value

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            # get file descriptors from the transfers
            max_fd = ct.c_int(-1)
            mc: lcurl.CURLMcode = lcurl.multi_fdset(multi,
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
            # libcurl.multi_fdset() doc.

            # set a suitable timeout to play around with
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
                pass
            elif rc == 0 or rc:  # timeout or action
                # timeout
                lcurl.multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

            if not still_running.value: break

        # See how the transfers went
        while True:
            msgs_left = ct.c_int()  # how many messages are left
            msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                    ct.byref(msgs_left))
            if not msgp:
                abort_on_test_timeout()
                break
            msg = msgp.contents

            if msg.msg == lcurl.CURLMSG_DONE:
                print("HTTP transfer completed with status %d" % msg.data.result)
                break
            abort_on_test_timeout()

    return res
