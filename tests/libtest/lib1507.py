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

import libcurl as lcurl
from curl_test import *  # noqa
#include "timediff.h"

#
# This is the list of basic details you need to tweak to get things right.
#

RECIPIENT: str = "<1507-recipient@example.com>"
MAILFROM:  str = "<1507-realuser@example.com>"

MULTI_PERFORM_HANG_TIMEOUT = 60 * 1000


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    return lcurl.CURL_READFUNC_ABORT


@curl_test_decorator
def test(URL: str,
         user_name: str = "user@example.com",
         user_password: str = "123qwerty") -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    mp_start = lcurl.timeval()

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        rcpt_list: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                                   RECIPIENT.encode("utf-8"))
        # more addresses can be added here
        # rcpt_list = lcurl.slist_append(rcpt_list, b"<others@example.com>")
        guard.add_slist(rcpt_list)

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        if 0:
           lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME,
                                   user_name.encode("utf-8") if user_name else None)
           lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD,
                                   user_password.encode("utf-8") if user_password else None)
        # endif
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_FROM, MAILFROM.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_RCPT, rcpt_list)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        multi_add_handle(multi, curl)

        mp_start = tutil.tvnow()

        # we start some action by calling perform right away
        still_running = ct.c_int(1)
        lcurl.multi_perform(multi, ct.byref(still_running))

        while still_running.value:

            curl_timeout = ct.c_long(-1)
            lcurl.multi_timeout(multi, ct.byref(curl_timeout))
            curl_timeout = curl_timeout.value

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            # get file descriptors from the transfers
            max_fd = ct.c_int(-1)
            lcurl.multi_fdset(multi,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(max_fd));
            max_fd = max_fd.value

            # In a real-world program you OF COURSE check the return code of the
            # function calls.  On success, the value of max_fd is guaranteed to be
            # greater or equal than -1.  We call select(max_fd + 1, ...), specially in
            # case of (max_fd == -1), we call select(0, ...), which is basically equal
            # to sleep.

            # set a suitable timeout to play around with
            timeout = (lcurl.timeval(tv_sec=curl_timeout // 1000,
                                     tv_usec=(curl_timeout % 1000) * 1000)
                       if 0 <= curl_timeout < 1000 else
                       lcurl.timeval(tv_sec=1, tv_usec=0))  # 1 sec
            rc: int = lcurl.select(max_fd + 1,
                                   ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                   ct.byref(timeout))

            if tutil.tvdiff(tutil.tvnow(), mp_start) > MULTI_PERFORM_HANG_TIMEOUT:
                print("ABORTING TEST, since it seems that it "
                      "would have run forever.", file=sys.stderr)
                break

            if rc == -1:
                pass  # select error
            elif rc == 0 or rc:  # timeout or action
                lcurl.multi_perform(multi, ct.byref(still_running))

    return res
