# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Dmitry Karpov <dkarpov1970@gmail.com>
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

# The purpose of this test is to test behavior of curl_multi_waitfds
# function in different scenarios:
#  empty multi handle (expected zero descriptors),
#  HTTP1 amd HTTP2 (no multiplexing) two transfers (expected two descriptors),
#  HTTP2 with multiplexing (expected one descriptors)
#  Improper inputs to the API result in CURLM_BAD_FUNCTION_ARGUMENT.
#  Sending a empty ufds, and size = 0 will return the number of fds needed.
#  Sending a non-empty ufds, but smaller than the fds needed will result in a
#    CURLM_OUT_OF_MEMORY, and a number of fds that is >= to the number needed.
#
#  It is also expected that all transfers run by multi-handle should complete
#  successfully.

from typing import Tuple
import sys
import enum
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa


class TEST_USE(enum.IntEnum):
    HTTP1       = 0
    HTTP2       = 1
    HTTP2_MPLEX = 2


def set_easy(URL: str, easy: ct.POINTER(lcurl.CURL), option: ct.c_long) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    # First set the URL that is about to receive our POST.
    easy_setopt(easy, lcurl.CURLOPT_URL, URL.encode("utf-8"))

    # get verbose debug output please
    easy_setopt(easy, lcurl.CURLOPT_VERBOSE, 1)

    if option == TEST_USE.HTTP1:
        # go http1
        easy_setopt(easy, lcurl.CURLOPT_HTTP_VERSION,
                          lcurl.CURL_HTTP_VERSION_1_1)
    elif option == TEST_USE.HTTP2:
        # go http2
        easy_setopt(easy, lcurl.CURLOPT_HTTP_VERSION,
                          lcurl.CURL_HTTP_VERSION_2_0)
    elif option == TEST_USE.HTTP2_MPLEX:
        # go http2 with multiplexing
        easy_setopt(easy, lcurl.CURLOPT_HTTP_VERSION,
                          lcurl.CURL_HTTP_VERSION_2_0)
        easy_setopt(easy, lcurl.CURLOPT_PIPEWAIT, 1)

    # no peer verify
    easy_setopt(easy, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    easy_setopt(easy, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

    # include headers
    easy_setopt(easy, lcurl.CURLOPT_HEADER, 1)

    # empty write function
    easy_setopt(easy, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_skipped)

    #test_cleanup:

    return res


def test_run(URL: str, option: ct.c_long) -> Tuple[lcurl.CURLcode, ct.c_uint]:

    res: lcurl.CURLcode  = lcurl.CURLE_OK
    mc:  lcurl.CURLMcode = lcurl.CURLM_OK

    max_count: int = 0

    ufds  = (lcurl.waitfd * 10)()
    ufds1 = (lcurl.waitfd * 10)()

    easy1: ct.POINTER(lcurl.CURL) = easy_init()
    easy2: ct.POINTER(lcurl.CURL) = easy_init()

    if set_easy(URL, easy1, option) != lcurl.CURLE_OK:
        goto(test_cleanup)

    if set_easy(URL, easy2, option) != lcurl.CURLE_OK:
        goto(test_cleanup)

    multi:  ct.POINTER(lcurl.CURLM) = multi_init()
    multi1: ct.POINTER(lcurl.CURLM) = multi_init()

    if option == TEST_USE.HTTP2_MPLEX:
        multi_setopt(multi, lcurl.CURLMOPT_PIPELINING,
                            lcurl.CURLPIPE_MULTIPLEX)

    multi_add_handle(multi, easy1)
    multi_add_handle(multi, easy2)

    while not mc:
        # get the count of file descriptors from the transfers
        fd_count     = ct.c_uint(0)
        fd_count_chk = ct.c_uint(0)

        still_running = ct.c_int()  # keep number of running handles
        mc = lcurl.multi_perform(multi, ct.byref(still_running))
        if not still_running.value or mc != lcurl.CURLM_OK:
            break

        # verify improper inputs are treated correctly.
        mc = lcurl.multi_waitfds(multi, None, 0, None)

        if mc != lcurl.CURLM_BAD_FUNCTION_ARGUMENT:
            print("libcurl.multi_waitfds() return code %d instead of "
                  "CURLM_BAD_FUNCTION_ARGUMENT." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        mc = lcurl.multi_waitfds(multi, None, 1, None)

        if mc != lcurl.CURLM_BAD_FUNCTION_ARGUMENT:
            print("libcurl.multi_waitfds() return code %d instead of "
                  "CURLM_BAD_FUNCTION_ARGUMENT." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        mc = lcurl.multi_waitfds(multi, None, 1, ct.byref(fd_count))

        if mc != lcurl.CURLM_BAD_FUNCTION_ARGUMENT:
            print("libcurl.multi_waitfds() return code %d instead of "
                  "CURLM_BAD_FUNCTION_ARGUMENT." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        mc = lcurl.multi_waitfds(multi, ufds, 10, ct.byref(fd_count))
        if mc != lcurl.CURLM_OK:
            print("libcurl.multi_waitfds() failed, code %d." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        if fd_count.value == 0:
            continue  # no descriptors yet

        # verify that sending nothing but the fd_count results in at least the
        # same number of fds
        mc = lcurl.multi_waitfds(multi, None, 0, ct.byref(fd_count_chk))

        if mc != lcurl.CURLM_OK:
            print("libcurl.multi_waitfds() failed, code %d." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        if fd_count_chk.value < fd_count.value:
            print("libcurl.multi_waitfds() should return at least the number "
                  "of fds needed", file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        # checking case when we don't have enough space for waitfds
        mc = lcurl.multi_waitfds(multi, ufds1, fd_count.value - 1, ct.byref(fd_count_chk))

        if mc != lcurl.CURLM_OUT_OF_MEMORY:
            print("libcurl.multi_waitfds() return code %d instead of "
                  "CURLM_OUT_OF_MEMORY." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        if fd_count_chk.value < fd_count.value:
            print("libcurl.multi_waitfds() sould return the amount of fds "
                  "needed if enough isn't passed in.", file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        # sending ufds with zero size, is valid
        mc = lcurl.multi_waitfds(multi, ufds, 0, None)

        if mc != lcurl.CURLM_OUT_OF_MEMORY:
            print("libcurl.multi_waitfds() return code %d instead of "
                  "CURLM_OUT_OF_MEMORY." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        mc = lcurl.multi_waitfds(multi, ufds, 0, ct.byref(fd_count_chk))

        if mc != lcurl.CURLM_OUT_OF_MEMORY:
            print("libcurl.multi_waitfds() return code %d instead of "
                  "CURLM_OUT_OF_MEMORY." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        if fd_count_chk.value < fd_count.value:
            print("libcurl.multi_waitfds() sould return the amount of fds "
                  "needed if enough isn't passed in.", file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

        if fd_count.value > max_count:
           max_count = fd_count.value

        # Do polling on descriptors in ufds in Multi 1
        numfds = ct.c_int()
        mc = lcurl.multi_poll(multi1, ufds, fd_count.value, 500, ct.byref(numfds))

        if mc != lcurl.CURLM_OK:
            print("libcurl.multi_poll() failed, code %d." % mc, file=sys.stderr)
            res = TEST_ERR_FAILURE
            break

    while True:
        msgs_left = ct.c_int()  # how many messages are left
        msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                ct.byref(msgs_left))
        if not msgp: break
        msg = msgp.contents

        if msg.msg == lcurl.CURLMSG_DONE:
            result: lcurl.CURLcode = msg.data.result
            if not res:
                res = result

    lcurl.multi_remove_handle(multi, easy1)
    lcurl.multi_remove_handle(multi, easy2)

    #test_cleanup:

    lcurl.easy_cleanup(easy1)
    lcurl.easy_cleanup(easy2)

    lcurl.multi_cleanup(multi)
    lcurl.multi_cleanup(multi1)

    return res, ct.c_uint(max_count)


def empty_multi_test() -> lcurl.CURLcode:

    res: lcurl.CURLcode  = lcurl.CURLE_OK
    mc:  lcurl.CURLMcode = lcurl.CURLM_OK

    ufds = (lcurl.waitfd * 10)()

    multi: ct.POINTER(lcurl.CURLM) = multi_init()
    easy:  ct.POINTER(lcurl.CURL)  = easy_init()

    fd_count = ct.c_uint(0)
    with curl_guard(False, easy, multi) as guard:

        # calling curl_multi_waitfds() on an empty multi handle.
        mc = lcurl.multi_waitfds(multi, ufds, 10, ct.byref(fd_count))
        if mc != lcurl.CURLM_OK:
            print("libcurl.multi_waitfds() failed, code %d." % mc, file=sys.stderr)
            return TEST_ERR_FAILURE
        elif fd_count.value > 0:
            print("libcurl.multi_waitfds() returned non-zero count of "
                  "waitfds: %d." % fd_count.value, file=sys.stderr)
            return TEST_ERR_FAILURE

        if set_easy("http://example.com", easy,
                    TEST_USE.HTTP1) != lcurl.CURLE_OK:
            return res

        # calling curl_multi_waitfds() on multi handle with added easy handle.
        multi_add_handle(multi, easy);

        mc = lcurl.multi_waitfds(multi, ufds, 10, ct.byref(fd_count))
        if mc != lcurl.CURLM_OK:
            print("libcurl.multi_waitfds() failed, code %d." % mc, file=sys.stderr)
            return TEST_ERR_FAILURE
        elif fd_count.value > 0:
            print("libcurl.multi_waitfds() returned non-zero count of "
                  "waitfds: %d." % fd_count.value, file=sys.stderr)
            return TEST_ERR_FAILURE

    return res


def test_run_check(URL: str, option, expected_fds):
    res, fd_count = test_run(URL, option)
    #_test_check(res, fd_count.value, expected_fds)
    if res != lcurl.CURLE_OK:
        print("test failed with code: %d" % res, file=sys.stderr)
    elif fd_count.value != expected_fds:
        print("Max number of waitfds: %d not as expected: %d" %
              (fd_count.value, expected_fds), file=sys.stderr)
        res = TEST_ERR_FAILURE
    return res


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        # Testing curl_multi_waitfds on empty and not started handles
        res = empty_multi_test()
        if res != lcurl.CURLE_OK: raise guard.Break

        # HTTP1, expected 2 waitfds - one for each transfer
        res = test_run_check(URL, TEST_USE.HTTP1, 2)
        if res != lcurl.CURLE_OK: raise guard.Break

        # HTTP2, expected 2 waitfds - one for each transfer
        res = test_run_check(URL, TEST_USE.HTTP2, 2)
        if res != lcurl.CURLE_OK: raise guard.Break

        # HTTP2 with multiplexing, expected 1 waitfds - one for all transfers
        res = test_run_check(URL, TEST_USE.HTTP2_MPLEX, 1)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
