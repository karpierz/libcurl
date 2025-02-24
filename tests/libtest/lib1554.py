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


ldata_names = [
  "NONE",
  "SHARE",
  "COOKIE",
  "DNS",
  "SESSION",
  "CONNECT",
  "PSL",
  "HSTS",
  "NULL",
]


@lcurl.lock_function
def test_lock(handle, data, locktype, useptr):
    print("-> Mutex lock %s" % ldata_names[data])


@lcurl.unlock_function
def test_unlock(handle, data, useptr):
    print("<- Mutex unlock %s" % ldata_names[data])


# test function

@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    share: ct.POINTER(lcurl.CURLSH) = lcurl.share_init()

    with curl_guard(True, share=share) as guard:
        if not share:
            print("libcurl.share_init() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE, lcurl.CURL_LOCK_DATA_CONNECT)
        lcurl.share_setopt(share, lcurl.CURLSHOPT_LOCKFUNC,   test_lock)
        lcurl.share_setopt(share, lcurl.CURLSHOPT_UNLOCKFUNC, test_unlock)

        # Loop the transfer and cleanup the handle properly every lap. This will
        # still reuse connections since the pool is in the shared object!

        for i in range(3):

            curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
            if not curl: continue
            guard.add_curl(curl)

            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # use the share object
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SHARE, share)

            # Perform the request, res will get the return code
            res = lcurl.easy_perform(curl)
            # Check for errors
            if res != lcurl.CURLE_OK:
                print("libcurl.easy_perform() failed: %s" %
                      lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)
                raise guard.Break

    return res
