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

HOSTHEADER: str = "Host: www.host.foo.com"


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


locks = [0] * 3


@lcurl.lock_function
def test_lock(handle, data, locktype, useptr):
    # lock callback
    user = ct.cast(useptr, ct.POINTER(userdata)).contents

    global locks

    if   data == lcurl.CURL_LOCK_DATA_SHARE:  what = "share"  ; locknum = 0
    elif data == lcurl.CURL_LOCK_DATA_DNS:    what = "dns"    ; locknum = 1
    elif data == lcurl.CURL_LOCK_DATA_COOKIE: what = "cookie" ; locknum = 2
    else:
        print("lock: no such data: %d" % data, file=sys.stderr)
        return

    # detect locking of locked locks
    if locks[locknum]:
        print("lock: double locked %s" % what)
        return

    locks[locknum] += 1

    print("lock:   %-6s [%s]: %d" % (what, user.text.decode("utf-8"), user.counter))
    user.counter += 1


@lcurl.unlock_function
def test_unlock(handle, data, useptr):
    # unlock callback
    user = ct.cast(useptr, ct.POINTER(userdata)).contents

    global locks

    if   data == lcurl.CURL_LOCK_DATA_SHARE:  what = "share"  ; locknum = 0
    elif data == lcurl.CURL_LOCK_DATA_DNS:    what = "dns"    ; locknum = 1
    elif data == lcurl.CURL_LOCK_DATA_COOKIE: what = "cookie" ; locknum = 2
    else:
        print("unlock: no such data: %d" % data, file=sys.stderr)
        return

    # detect unlocking of unlocked locks
    if not locks[locknum]:
        print("unlock: double unlocked %s" % what)
        return

    locks[locknum] -= 1

    print("unlock: %-6s [%s]: %d" % (what, user.text.decode("utf-8"), user.counter))
    user.counter += 1


def set_host(headers: ct.POINTER(lcurl.slist) = None) -> ct.POINTER(lcurl.slist):
    # build host entry
    return lcurl.slist_append(headers, HOSTHEADER.encode("utf-8"))


def test_fire(ptr: ct.c_void_p) -> ct.c_void_p:
    # the dummy thread function
    tdata = ct.cast(ptr, ct.POINTER(Tdata)).contents

    code: lcurl.CURLcode

    curl: ct.POINTER(lcurl.CURL) = easy_init()
    if not curl:
        return None  # NULL

    with curl_guard(False, curl) as guard:

        headers: ct.POINTER(lcurl.slist) = set_host()
        guard.add_slist(headers)

        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headers)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, tdata.url)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_COOKIEFILE, b"")
        print("CURLOPT_SHARE")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SHARE, tdata.share)

        print("PERFORM")
        code = lcurl.easy_perform(curl)

        if code:
            i: int = 0
            print("perform url '%s' repeat %d failed, curlcode %d" %
                  (tdata.url.decode("utf-8"), i, code), file=sys.stderr)

        print("CLEANUP")

    return None  # NULL


def suburl(base: str, i: int) -> str:
    # build request url
    return "%s%.4d" % (base, i)


# test function

@curl_test_decorator
def test(URL: str, cookie_jar: str) -> lcurl.CURLcode:
    cookie_jar = str(cookie_jar)

    scode: lcurl.CURLSHcode = lcurl.CURLSHE_OK
    code:  lcurl.CURLcode   = lcurl.CURLE_OK

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
        print("CURL_LOCK_DATA_COOKIE")
        scode = lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE,
                                          lcurl.CURL_LOCK_DATA_COOKIE)
    if scode == lcurl.CURLSHE_OK:
        print("CURL_LOCK_DATA_DNS")
        scode = lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE,
                                          lcurl.CURL_LOCK_DATA_DNS)
    if scode != lcurl.CURLSHE_OK:
        print("libcurl.share_setopt() failed", file=sys.stderr)
        lcurl.share_cleanup(share)
        lcurl.global_cleanup()
        return TEST_ERR_MAJOR_BAD

    # initial cookie manipulation
    curl: ct.POINTER(lcurl.CURL) = easy_init()
    if not curl:
        lcurl.share_cleanup(share)
        lcurl.global_cleanup()
        return TEST_ERR_MAJOR_BAD

    headers: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()

    print("CURLOPT_SHARE")
    test_setopt(curl, lcurl.CURLOPT_SHARE, share)
    print("CURLOPT_COOKIELIST injected_and_clobbered")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST,
                b"Set-Cookie: injected_and_clobbered=yes; "
                b"domain=host.foo.com; expires=Sat Feb 2 11:56:27 GMT 2030")
    print("CURLOPT_COOKIELIST ALL")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST, b"ALL")
    print("CURLOPT_COOKIELIST session")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST, b"Set-Cookie: session=elephants")
    print("CURLOPT_COOKIELIST injected")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST,
                b"Set-Cookie: injected=yes; domain=host.foo.com; "
                b"expires=Sat Feb 2 11:56:27 GMT 2030")
    print("CURLOPT_COOKIELIST SESS")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST, b"SESS")

    print("CLEANUP")
    lcurl.easy_cleanup(curl)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    # start treads
    for i in range(1, THREADS + 1):
        # set thread data
        tdata.url   = suburl(URL, i).encode("utf-8")
        tdata.share = share

        # simulate thread, direct call of "thread" function
        print("*** run %d" % i)
        test_fire(ct.byref(tdata))

    # fetch another one and save cookies
    print("*** run %d" % i)
    curl = lcurl.easy_init()
    if not curl:
        print("libcurl.easy_init() failed", file=sys.stderr)
        lcurl.share_cleanup(share)
        lcurl.global_cleanup()
        return TEST_ERR_MAJOR_BAD

    url = suburl(URL, i)
    headers = set_host()
    test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headers)
    test_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    print("CURLOPT_SHARE")
    test_setopt(curl, lcurl.CURLOPT_SHARE, share)
    print("CURLOPT_COOKIEJAR")
    test_setopt(curl, lcurl.CURLOPT_COOKIEJAR, cookie_jar.encode("utf-8"))
    print("CURLOPT_COOKIELIST FLUSH")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST, b"FLUSH")

    print("PERFORM")
    lcurl.easy_perform(curl)

    print("CLEANUP")
    lcurl.easy_cleanup(curl)
    del url
    lcurl.slist_free_all(headers)

    # load cookies
    curl = lcurl.easy_init()
    if not curl:
        print("libcurl.easy_init() failed", file=sys.stderr)
        lcurl.share_cleanup(share)
        lcurl.global_cleanup()
        return TEST_ERR_MAJOR_BAD

    url = suburl(URL, i)
    headers = set_host()
    test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headers)
    test_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    print("CURLOPT_SHARE")
    test_setopt(curl, lcurl.CURLOPT_SHARE, share)
    print("CURLOPT_COOKIELIST ALL")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST, b"ALL")
    print("CURLOPT_COOKIEJAR")
    test_setopt(curl, lcurl.CURLOPT_COOKIEFILE, cookie_jar.encode("utf-8"))
    print("CURLOPT_COOKIELIST RELOAD")
    test_setopt(curl, lcurl.CURLOPT_COOKIELIST, b"RELOAD")

    cookies: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
    code = lcurl.easy_getinfo(curl, lcurl.CURLINFO_COOKIELIST, ct.byref(cookies))
    if code != lcurl.CURLE_OK:
        print("libcurl.easy_getinfo() failed", file=sys.stderr)
        res = TEST_ERR_MAJOR_BAD
        goto(test_cleanup)
    print("loaded cookies:")
    if not cookies:
        print("  reloading cookies from '%s' failed" % cookie_jar, file=sys.stderr)
        res = TEST_ERR_MAJOR_BAD
        goto(test_cleanup)
    print("-----------------")
    next_cookie: ct.POINTER(lcurl.slist) = cookies
    while next_cookie:
        next_cookie = next_cookie.contents
        print("  %s" % next_cookie.data.decode("utf-8"))
        next_cookie = next_cookie.next
    print("-----------------")
    lcurl.slist_free_all(cookies)

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
    lcurl.slist_free_all(headers)
    del url
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
