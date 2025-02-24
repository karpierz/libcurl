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


THREADS = 2


class Tdata(ct.Structure):
    _fields_ = [
    # struct containing data of a thread
    ("share", ct.POINTER(lcurl.CURLSH)),
    ("url",   ct.c_char_p),
]


class userdata(ct.Structure):
    _fields_ = [
    ("text",    ct.c_char_p),
    ("counter", ct.c_int),
]


@lcurl.lock_function
def test_lock(handle, data, locktype, useptr):
    # lock callback
    user = ct.cast(useptr, ct.POINTER(userdata)).contents

    if   data == lcurl.CURL_LOCK_DATA_SHARE:       what = "share"
    elif data == lcurl.CURL_LOCK_DATA_DNS:         what = "dns"
    elif data == lcurl.CURL_LOCK_DATA_COOKIE:      what = "cookie"
    elif data == lcurl.CURL_LOCK_DATA_SSL_SESSION: what = "ssl_session"
    else:
        print("lock: no such data: %d" % data, file=sys.stderr)
        return

    print("lock:   %-6s [%s]: %d" % (what, user.text.decode("utf-8"), user.counter))
    user.counter += 1


@lcurl.unlock_function
def test_unlock(handle, data, useptr):
    # unlock callback
    user = ct.cast(useptr, ct.POINTER(userdata)).contents

    if   data == lcurl.CURL_LOCK_DATA_SHARE:       what = "share"
    elif data == lcurl.CURL_LOCK_DATA_DNS:         what = "dns"
    elif data == lcurl.CURL_LOCK_DATA_COOKIE:      what = "cookie"
    elif data == lcurl.CURL_LOCK_DATA_SSL_SESSION: what = "ssl_session"
    else:
        print("unlock: no such data: %d" % data, file=sys.stderr)
        return

    print("unlock: %-6s [%s]: %d" % (what, user.text.decode("utf-8"), user.counter))
    user.counter += 1


def test_fire(ptr: ct.c_void_p) -> ct.c_void_p:
    # the dummy thread function
    tdata = ct.cast(ptr, ct.POINTER(Tdata)).contents

    code: lcurl.CURLcode

    curl: ct.POINTER(lcurl.CURL) = easy_init()
    if not curl:
        return None  # NULL

    with curl_guard(False, curl) as guard:

        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, tdata.url)
        print("CURLOPT_SHARE")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SHARE, tdata.share)

        print("PERFORM")
        code = lcurl.easy_perform(curl)

        if code != lcurl.CURLE_OK:
            i: int = 0
            print("perform url '%s' repeat %d failed, curlcode %d" %
                  (tdata.url.decode("utf-8"), i, code), file=sys.stderr)

        print("CLEANUP")

    return None  # NULL


# test function

@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res:   lcurl.CURLcode   = lcurl.CURLE_OK
    scode: lcurl.CURLSHcode = lcurl.CURLSHE_OK

    tdata = Tdata()

    user = userdata()
    user.text    = b"Pigs in space"
    user.counter = 0

    print("GLOBAL_INIT")
    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    # prepare share
    print("SHARE_INIT")
    share: ct.POINTER(lcurl.CURLSH) = lcurl.share_init()
    if not share:
        print("libcurl.share_init() failed", file=sys.stderr)
        lcurl.global_cleanup()
        return TEST_ERR_MAJOR_BAD

    if scode == lcurl.CURLSHE_OK:
        print("CURLSHOPT_LOCKFUNC")
        scode = lcurl.share_setopt(share, lcurl.CURLSHOPT_LOCKFUNC, test_lock)
    if scode == lcurl.CURLSHE_OK:
        print("CURLSHOPT_UNLOCKFUNC")
        scode = lcurl.share_setopt(share, lcurl.CURLSHOPT_UNLOCKFUNC, test_unlock)
    if scode == lcurl.CURLSHE_OK:
        print("CURLSHOPT_USERDATA")
        scode = lcurl.share_setopt(share, lcurl.CURLSHOPT_USERDATA, ct.byref(user))
    if scode == lcurl.CURLSHE_OK:
        print("CURL_LOCK_DATA_SSL_SESSION")
        scode = lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE,
                                          lcurl.CURL_LOCK_DATA_SSL_SESSION)
    if scode != lcurl.CURLSHE_OK:
        print("libcurl.share_setopt() failed", file=sys.stderr)
        lcurl.share_cleanup(share)
        lcurl.global_cleanup()
        return TEST_ERR_MAJOR_BAD

    # start treads
    for i in range(1, THREADS + 1):
        # set thread data
        tdata.url   = URL.encode("utf-8")
        tdata.share = share

        # simulate thread, direct call of "thread" function
        print("*** run %d" % i)
        test_fire(ct.byref(tdata))

    # fetch another one
    print("*** run %d" % i)
    curl: ct.POINTER(lcurl.CURL) = easy_init()
    if not curl:
        lcurl.share_cleanup(share)
        lcurl.global_cleanup()
        return TEST_ERR_MAJOR_BAD

    test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
    print("CURLOPT_SHARE")
    test_setopt(curl, lcurl.CURLOPT_SHARE, share)

    print("PERFORM")
    res = lcurl.easy_perform(curl)

    # try to free share, expect to fail because share is in use
    print("try SHARE_CLEANUP...")
    scode = lcurl.share_cleanup(share)
    if scode == lcurl.CURLSHE_OK:
        print("libcurl.share_cleanup() succeed but error expected",
              file=sys.stderr)
        share = ct.POINTER(lcurl.CURLSH)()
    else:
        print("SHARE_CLEANUP failed, correct")

    # test_cleanup:

    # clean up last handle
    print("CLEANUP")
    lcurl.easy_cleanup(curl)
    # free share
    print("SHARE_CLEANUP")
    scode = lcurl.share_cleanup(share)
    if scode != lcurl.CURLSHE_OK:
        print("libcurl.share_cleanup() failed, code errno %d" % scode,
              file=sys.stderr)
    # global clean up
    print("GLOBAL_CLEANUP")
    lcurl.global_cleanup()

    return res
