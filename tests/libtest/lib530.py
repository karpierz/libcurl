# **************************************************************************
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
# **************************************************************************

import sys
import ctypes as ct

import libcurl as lcurl
from libcurl._platform import FD_ISSET, FD_SET
from curl_test import *  # noqa

# The purpose of this test is to make sure that if libcurl.CURLMOPT_SOCKETFUNCTION
# or libcurl.CURLMOPT_TIMERFUNCTION returns error, the associated transfer should be
# aborted correctly.


class Sockets(ct.Structure):
    _fields_ = [
    ("sockets",   ct.POINTER(lcurl.socket_t)),
    ("count",     ct.c_int),  # number of sockets actually stored in array
    ("max_count", ct.c_int),  # max number of sockets that fit in allocated array
]


class ReadWriteSockets(ct.Structure):
    _fields_ = [
    ("read",  Sockets),
    ("write", Sockets),
]


def add_fd(sockets: Sockets, fd: lcurl.socket_t, what: str) -> int:
    #
    # Add a file descriptor to a sockets array.
    # Return 0 on success, 1 on error.
    #

    # To ensure we only have each file descriptor once, we remove it then
    # add it again.
    print("Add socket fd %d for %s" % (fd, what), file=sys.stderr)

    remove_fd(sockets, fd)
    # Allocate array storage when required.
    #
    if not sockets.sockets:
        sockets.sockets = (20 * lcurl.socket_t)()
        if not sockets.sockets:
            return 1
        sockets.max_count = 20
    elif sockets.count >= sockets.max_count:
        old_sockets = sockets.sockets
        sockets.sockets = ((sockets.max_count + 20) * lcurl.socket_t)()
        if not sockets.sockets:
            # cleanup in test_cleanup
            return 1
        for i in range(sockets.max_count):
            sockets.sockets[i] = old_sockets[i]
        sockets.max_count += 20

    # Add file descriptor to array.
    #
    sockets.sockets[sockets.count] = fd
    sockets.count += 1

    return 0


def remove_fd(sockets: Sockets, fd: lcurl.socket_t, mention: bool = False):
    #
    # Remove a file descriptor from a sockets array.
    #
    if mention:
        print("Remove socket fd %d" % fd, file=sys.stderr)

    for i in range(sockets.count):
        if sockets.sockets[i] == fd:
            if i < sockets.count - 1:
                for j in range(i, sockets.count - 1):
                    sockets.sockets[i] = sockets.sockets[i + 1]
            sockets.count -= 1


max_socket_calls: int = 0
socket_calls:     int = 0

@lcurl.socket_callback
def socket_callback(easy, s, what, userp, socketp):
    #
    # Callback invoked by curl to poll reading / writing of a socket.
    #
    sockets = ct.cast(userp, ct.POINTER(ReadWriteSockets)).contents

    global socket_calls, max_socket_calls

    print("CURLMOPT_SOCKETFUNCTION called: %d" % socket_calls, file=sys.stderr)

    socket_calls += 1
    if socket_calls == max_socket_calls:
        print("socket_callback returns error", file=sys.stderr)
        return -1

    if what == lcurl.CURL_POLL_IN or what == lcurl.CURL_POLL_INOUT:
        if add_fd(sockets.read, s, "read"):
            return -1  # bail out

    if what == lcurl.CURL_POLL_OUT or what == lcurl.CURL_POLL_INOUT:
        if add_fd(sockets.write, s, "write"):
            return -1  # bail out

    if what == lcurl.CURL_POLL_REMOVE:
        remove_fd(sockets.read,  s, True)
        remove_fd(sockets.write, s)

    return 0


max_timer_calls: int = 0
timer_calls:     int = 0

@lcurl.multi_timer_callback
def timer_callback(multi, timeout_ms, userp):
    #
    # Callback invoked by curl to set a timeout.
    #
    timeout = ct.cast(userp, ct.POINTER(lcurl.timeval)).contents

    global timer_calls, max_timer_calls

    print("CURLMOPT_TIMERFUNCTION called: %d" % timer_calls, file=sys.stderr)

    timer_calls += 1
    if timer_calls == max_timer_calls:
        print("timer_callback returns error", file=sys.stderr)
        return -1

    if timeout_ms != -1:
        time_now = tutil.tvnow()
        ct.memmove(ct.byref(timeout), ct.byref(time_now),
                   min(ct.sizeof(timeout), ct.sizeof(time_now)))
        timeout.tv_usec += timeout_ms * 1000
    else:
        timeout.tv_sec = -1

    return 0


def check_for_completion(curl: ct.POINTER(lcurl.CURLM), success: ct.c_int) -> int:
    #
    # Check for curl completion.
    #
    result: int = 0

    success.value = 0
    while True:
        msgs_left = ct.c_int()
        msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(curl,
                                                                ct.byref(msgs_left))
        if not msgp: break  # pragma: no branch
        msg = msgp.contents

        if msg.msg == lcurl.CURLMSG_DONE:
            result = 1
            if msg.data.result == lcurl.CURLE_OK:
                success.value = 1
            else:
                success.value = 0
        else:
            print("Got an unexpected message from curl: %i" % msg.msg,
                  file=sys.stderr)
            result = 1
            success.value = 0

    return result


def get_microsec_timeout(timeout: lcurl.timeval) -> int:
    now: lcurl.timeval = tutil.tvnow()
    result = ct.c_ssize_t((timeout.tv_sec  - now.tv_sec) * 1_000_000 +
                          (timeout.tv_usec - now.tv_usec)).value
    if result < 0: result = 0
    return result


def update_fd_set(sockets: Sockets, fdset: lcurl.fd_set, max_fd: lcurl.socket_t):
    #
    # Update a fd_set with all of the sockets in use.
    #
    #print("**************************", sockets.count)
    for i in range(sockets.count):
        FD_SET(sockets.sockets[i], ct.byref(fdset))
        fd = sockets.sockets[i] + 1
        if fd > max_fd.value:
            max_fd.value = fd
    print("**************************", sockets.count, max_fd.value)


def socket_action(curl: ct.POINTER(lcurl.CURLM),
                  s: lcurl.socket_t, evBitmask: int, info: str) -> int:
    num_handles = ct.c_int(0)
    result: lcurl.CURLMcode = lcurl.multi_socket_action(curl, s, evBitmask,
                                                        ct.byref(num_handles))
    if result != lcurl.CURLM_OK:
        print("Curl error on %s (%i) %s" %
              (info, result, lcurl.multi_strerror(result).decode("utf-8")),
              file=sys.stderr)
    return int(result)


def check_fd_set(curl: ct.POINTER(lcurl.CURLM),
                 sockets: Sockets, fdset: lcurl.fd_set, evBitmask: int, name: str) -> int:
    #
    # Invoke curl when a file descriptor is set.
    #
    result: int = 0
    for i in range(sockets.count):
        if FD_ISSET(sockets.sockets[i], ct.byref(fdset)):
            result = socket_action(curl, sockets.sockets[i], evBitmask, name)
            if result:
                break
    return result


def test_one(URL: str, timercb: int, socketcb: int) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    sockets = ReadWriteSockets(Sockets(None, 0, 0),
                               Sockets(None, 0, 0))
    timer_timeout = lcurl.timeval(tv_sec=-1, tv_usec=0)

    # set the limits
    global timer_calls,  max_timer_calls
    global socket_calls, max_socket_calls
    max_timer_calls  = timercb
    max_socket_calls = socketcb
    timer_calls  = 0  # reset the globals
    socket_calls = 0

    print("start test: %d %d" % (timercb, socketcb), file=sys.stderr)
    start_test_timing()

    res = res_global_init(lcurl.CURL_GLOBAL_ALL)
    if res != lcurl.CURLE_OK: return res

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        # specify target
        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # go verbose
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        multi_setopt(multi, lcurl.CURLMOPT_SOCKETFUNCTION, socket_callback)
        multi_setopt(multi, lcurl.CURLMOPT_SOCKETDATA, ct.byref(sockets))
        multi_setopt(multi, lcurl.CURLMOPT_TIMERFUNCTION, timer_callback)
        multi_setopt(multi, lcurl.CURLMOPT_TIMERDATA, ct.byref(timer_timeout))

        multi_add_handle(multi, curl)

        if socket_action(multi, lcurl.CURL_SOCKET_TIMEOUT, 0, b"timeout"):
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break

        success = ct.c_int(0)
        while not check_for_completion(multi, success):

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()

            max_fd = lcurl.socket_t(-1)
            update_fd_set(sockets.read,  fd_read,  max_fd)
            update_fd_set(sockets.write, fd_write, max_fd)
            max_fd = max_fd.value - 1
            print("################################", max_fd)

            if timer_timeout.tv_sec != -1:
                tv_usec: int = get_microsec_timeout(timer_timeout)
                timeout = lcurl.timeval(tv_sec=tv_usec // 1_000_000,
                                        tv_usec=tv_usec % 1_000_000)
            elif max_fd == -1:
                timeout = lcurl.timeval(tv_sec=0, tv_usec=100_000)  # 100 ms
            else:
                timeout = lcurl.timeval(tv_sec=10, tv_usec=0)  # 10 sec
            assert max_fd >= 0
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), None,
                              ct.byref(timeout))
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", res)

            # Check the sockets for reading / writing
            if check_fd_set(multi, sockets.read,  fd_read,  lcurl.CURL_CSELECT_IN, "read"):
                res = TEST_ERR_MAJOR_BAD
                raise guard.Break
            if check_fd_set(multi, sockets.write, fd_write, lcurl.CURL_CSELECT_OUT, "write"):
                res = TEST_ERR_MAJOR_BAD
                raise guard.Break

            if timer_timeout.tv_sec != -1 and get_microsec_timeout(timer_timeout) == 0:
                # Curl's timer has elapsed.
                if socket_action(multi, lcurl.CURL_SOCKET_TIMEOUT, 0, b"timeout"):
                    res = TEST_ERR_BAD_TIMEOUT
                    raise guard.Break

            abort_on_test_timeout()

        if not success.value:
            print("Error getting file.", file=sys.stderr)
            res = TEST_ERR_MAJOR_BAD

    # proper cleanup sequence
    print("cleanup: %d %d" % (timercb, socketcb), file=sys.stderr)

    # free local memory
    sockets.read.sockets  = None
    sockets.write.sockets = None

    return res


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    rc: lcurl.CURLcode

    # rerun the same transfer multiple times and make it fail in different
    # callback calls
    rc = test_one(URL, 0, 0)
    if rc:
        print("test 0/0 failed: %d" % rc, file=sys.stderr)

    rc = test_one(URL, 1, 0)
    if not rc:
        print("test 1/0 failed: %d" % rc, file=sys.stderr)

    rc = test_one(URL, 2, 0)
    if not rc:
        print("test 2/0 failed: %d" % rc, file=sys.stderr)

    rc = test_one(URL, 0, 1)
    if not rc:
        print("test 0/1 failed: %d" % rc, file=sys.stderr)

    rc = test_one(URL, 0, 2)
    if not rc:
        print("test 0/2 failed: %d" % rc, file=sys.stderr)

    return lcurl.CURLE_OK
