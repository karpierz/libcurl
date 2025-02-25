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


WAKEUP_NUM = 10


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, mcurl=multi) as guard:

        numfds = ct.c_int()

        # no wakeup

        time_before_wait = tutil.tvnow()
        multi_poll(multi, None, 0, 1000, ct.byref(numfds))
        time_after_wait = tutil.tvnow()

        if tutil.tvdiff(time_after_wait, time_before_wait) < 500:
            print("%s:%d libcurl.multi_poll returned too early" %
                  (current_file(), current_line()), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        abort_on_test_timeout()

        # try a single wakeup

        res_multi_wakeup(multi)

        time_before_wait = tutil.tvnow()
        multi_poll(multi, None, 0, 1000, ct.byref(numfds))
        time_after_wait = tutil.tvnow()

        if tutil.tvdiff(time_after_wait, time_before_wait) > 500:
            print("%s:%d libcurl.multi_poll returned too late" %
                  (current_file(), current_line()), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        abort_on_test_timeout()

        # previous wakeup should not wake up this

        time_before_wait = tutil.tvnow()
        multi_poll(multi, None, 0, 1000, ct.byref(numfds))
        time_after_wait = tutil.tvnow()

        if tutil.tvdiff(time_after_wait, time_before_wait) < 500:
            print("%s:%d libcurl.multi_poll returned too early" %
                  (current_file(), current_line()), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        abort_on_test_timeout()

        # try lots of wakeup

        for i in range(WAKEUP_NUM):
            res_multi_wakeup(multi)

        time_before_wait = tutil.tvnow()
        multi_poll(multi, None, 0, 1000, ct.byref(numfds))
        time_after_wait = tutil.tvnow()

        if tutil.tvdiff(time_after_wait, time_before_wait) > 500:
            print("%s:%d libcurl.multi_poll returned too late" %
                  (current_file(), current_line()), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        abort_on_test_timeout()

        # Even lots of previous wakeups should not wake up this.

        time_before_wait = tutil.tvnow()
        multi_poll(multi, None, 0, 1000, ct.byref(numfds))
        time_after_wait = tutil.tvnow()

        if tutil.tvdiff(time_after_wait, time_before_wait) < 500:
            print("%s:%d libcurl.multi_poll returned too early" %
                  (current_file(), current_line()), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        abort_on_test_timeout()

    return res
