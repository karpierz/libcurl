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

# See https://github.com/curl/curl/issues/3371
#
# This test case checks whether libcurl.multi_remove_handle() cancels
# asynchronous DNS resolvers without blocking where possible.  Obviously, it
# only tests whichever resolver cURL is actually built with.

# We're willing to wait a very generous two seconds for the removal.  This is
# as low as we can go while still easily supporting SIGALRM timing for the
# non-threaded blocking resolver.  It doesn't matter that much because when
# the test passes, we never wait this long. We set it much higher to avoid
# issues when running on overloaded CI machines.
#
TEST_HANG_TIMEOUT = 60 * 1000


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res:  lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        timeout: int
        # Set a DNS server that hopefully will not respond when using c-ares.
        if lcurl.easy_setopt(curl, lcurl.CURLOPT_DNS_SERVERS,
                                   b"0.0.0.0") == lcurl.CURLE_OK:
            # Since we could set the DNS server, presume we are working with a
            # resolver that can be cancelled (i.e. c-ares).  Thus,
            # libcurl.multi_remove_handle() should not block even when the resolver
            # request is outstanding.  So, set a request timeout _longer_ than the
            # test hang timeout so we will fail if the handle removal call incorrectly
            # blocks.
            timeout = TEST_HANG_TIMEOUT * 2
        else:
            # If we can't set the DNS server, presume that we are configured to use a
            # resolver that can't be cancelled (i.e. the threaded resolver or the
            # non-threaded blocking resolver).  So, we just test that the
            # libcurl.multi_remove_handle() call does finish well within our test
            # timeout.
            #
            # But, it is very unlikely that the resolver request will take any time at
            # all because we haven't been able to configure the resolver to use an
            # non-responsive DNS server.  At least we exercise the flow.
            print("CURLOPT_DNS_SERVERS not supported; "
                  "assuming libcurl.multi_remove_handle() will block",
                  file=sys.stderr)
            timeout = TEST_HANG_TIMEOUT // 2

        # Setting a timeout on the request should ensure that even if we have to
        # wait for the resolver during libcurl.multi_remove_handle(), it won't take
        # longer than this, because the resolver request inherits its timeout from
        # this.
        easy_setopt(curl, lcurl.CURLOPT_TIMEOUT_MS, timeout)

        multi_add_handle(multi, curl)

        # This should move the handle from INIT => CONNECT => WAITRESOLVE.
        print("libcurl.multi_perform()...", file=sys.stderr)
        still_running = ct.c_int()
        multi_perform(multi, ct.byref(still_running))
        print("libcurl.multi_perform() succeeded", file=sys.stderr)

        # Start measuring how long it takes to remove the handle.
        print("libcurl.multi_remove_handle()...", file=sys.stderr)
        start_test_timing()

        mres: lcurl.CURLMcode = lcurl.multi_remove_handle(multi, curl)
        if mres:
            print("libcurl.multi_remove_handle() failed, with code %d" % mres,
                  file=sys.stderr)
            return int(TEST_ERR_MULTI)

        print("libcurl.multi_remove_handle() succeeded", file=sys.stderr)

        # Fail the test if it took too long to remove.  This happens after the fact,
        # and says "it seems that it would have run forever", which isn't true, but
        # it's close enough, and simple to do.
        abort_on_test_timeout(TEST_HANG_TIMEOUT)

    return res
