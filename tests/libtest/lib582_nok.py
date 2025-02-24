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

# from warnless.c
def curlx_sztosi(sznum) -> int: return int(sznum)


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


def remove_fd(sockets: Sockets, fd: lcurl.socket_t, mention: bool = False):
    #
    # Remove a file descriptor from a sockets array.
    #
    if mention:
        print("Remove socket fd %d" % fd, file=sys.stderr)

    for i in range(sockets.count):
        if sockets.sockets[i] == fd:
            if i < sockets.count - 1:
                ct.memmove(ct.byref(sockets.sockets, i),
                           ct.byref(sockets.sockets, i + 1),
                           (sockets.count - (i + 1)) *
                           ct.sizeof(lcurl.socket_t))
            sockets.count -= 1


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
        sockets.sockets = libc.malloc(20 * ct.sizeof(lcurl.socket_t))
        if not sockets.sockets:
            return 1
        sockets.max_count = 20
    elif sockets.count >= sockets.max_count:
        # this can't happen in normal cases
        print("too many file handles error", file=sys.stderr)
        exit(2);

    # Add file descriptor to array.
    #
    sockets.sockets[sockets.count] = fd
    sockets.count += 1

    return 0


@lcurl.socket_callback
def curlSocketCallback(easy, s, what, userp, socketp):
    #
    # Callback invoked by curl to poll reading / writing of a socket.
    #
    sockets = ct.cast(userp, ct.POINTER(ReadWriteSockets)).contents

    if what == lcurl.CURL_POLL_IN or what == lcurl.CURL_POLL_INOUT:
        add_fd(sockets.read, s, "read")

    if what == lcurl.CURL_POLL_OUT or what == lcurl.CURL_POLL_INOUT:
        add_fd(sockets.write, s, "write")

    if what == lcurl.CURL_POLL_REMOVE:
        remove_fd(sockets.read,  s, True)
        remove_fd(sockets.write, s)

    return 0


@lcurl.multi_timer_callback
def timer_callback(multi, timeout_ms, userp):
    #
    # Callback invoked by curl to set a timeout.
    #
    timeout = ct.cast(userp, ct.POINTER(lcurl.timeval)).contents
    if timeout_ms != -1:
        time_now = tutil.tvnow()
        ct.memmove(ct.byref(timeout), ct.byref(time_now),
                   min(ct.sizeof(timeout), ct.sizeof(time_now)))
        timeout.tv_usec += timeout_ms * 1000
    else:
        timeout.tv_sec = -1

    return 0


def checkForCompletion(curl: ct.POINTER(lcurl.CURLM), success: ct.c_int) -> int:
    #
    # Check for curl completion.
    #
    result: int = 0

    success.value = 0
    while True:
        msgs_left = ct.c_int()
        msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(curl,
                                                                ct.byref(msgs_left))
        if not msgp: break
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


def getMicroSecondTimeout(timeout: lcurl.timeval) -> int:
    now: lcurl.timeval = tutil.tvnow()
    result = ct.c_ssize_t((timeout.tv_sec  - now.tv_sec) * 1_000_000 +
                          (timeout.tv_usec - now.tv_usec)).value
    if result < 0: result = 0
    return curlx_sztosi(result)


def update_fd_set(sockets: Sockets, fdset: lcurl.fd_set, max_fd: lcurl.socket_t):
    #
    # Update a fd_set with all of the sockets in use.
    #
    for i in range(sockets.count):
        FD_SET(sockets.sockets[i], ct.byref(fdset))
        if max_fd.value < sockets.sockets[i] + 1:
            max_fd.value = sockets.sockets[i] + 1

def notifyCurl(curl: ct.POINTER(lcurl.CURLM),
               s: lcurl.socket_t, evBitmask: int, info: str) -> int:
    num_handles = ct.c_int(0)
    result: lcurl.CURLMcode = lcurl.multi_socket_action(curl, s, evBitmask,
                                                        ct.byref(num_handles))
    if result != lcurl.CURLM_OK:
        print("Curl error on %s: %i (%s)" %
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
            notifyCurl(curl, sockets.sockets[i], evBitmask, name)

    return result


@curl_test_decorator
def test(URL: str, filename: str = None, user_login: str = None,
         client_pub_key: str = None, client_priv_key: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    sockets = ReadWriteSockets((None, 0, 0),
                               (None, 0, 0))
    timer_timeout = lcurl.timeval(tv_sec=-1, tv_usec=0)

    start_test_timing()

    if not user_login:
        print("Usage: lib582 [url] [filename] [username]", file=sys.stderr)
        return TEST_ERR_USAGE

    try:
        hd_src = open(filename, "rb")
    except OSError as exc:
        print("fopen() failed with error: %d (%s)" %
              (exc.errno, exc.strerror), file=sys.stderr)
        print("Error opening file: (%s)" % filename,
              file=sys.stderr)
        return TEST_ERR_FOPEN

    with hd_src:

        try:
            # get the file size of the local file
            file_len: int = file_size(hd_src)
        except OSError as exc:
            # can't open file, bail out
            print("fstat() failed with error: %d (%s)" %
                  (exc.errno, exc.strerror), file=sys.stderr)
            print("ERROR: cannot open file (%s)" % filename,
                  file=sys.stderr)
            return TEST_ERR_FSTAT

        print("Set to upload %d bytes" % file_len, file=sys.stderr)

        res = res_global_init(lcurl.CURL_GLOBAL_ALL)
        if res != lcurl.CURLE_OK: return res

        curl:  ct.POINTER(lcurl.CURL)  = easy_init()
        multi: ct.POINTER(lcurl.CURLM) = multi_init()

        with curl_guard(True, curl, multi) as guard:
            if not curl:  return TEST_ERR_EASY_INIT
            if not multi: return TEST_ERR_MULTI

            # specify target
            easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # enable uploading
            easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
            # go verbose
            easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            # we want to use our own read function
            test_setopt(curl, lcurl.CURLOPT_READFUNCTION, lcurl.read_from_file)
            # now specify which file to upload
            easy_setopt(curl, lcurl.CURLOPT_READDATA, id(hd_src))
            easy_setopt(curl, lcurl.CURLOPT_USERPWD,
                              user_login.encode("utf-8") if user_login else None)
            easy_setopt(curl, lcurl.CURLOPT_SSH_PUBLIC_KEYFILE,
                              client_pub_key.encode("utf-8") if client_pub_key else None)
            easy_setopt(curl, lcurl.CURLOPT_SSH_PRIVATE_KEYFILE,
                              client_priv_key.encode("utf-8") if client_priv_key else None)
            easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
            easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, file_len)

            multi_setopt(multi, lcurl.CURLMOPT_SOCKETFUNCTION, curlSocketCallback)
            multi_setopt(multi, lcurl.CURLMOPT_SOCKETDATA, ct.byref(sockets))
            multi_setopt(multi, lcurl.CURLMOPT_TIMERFUNCTION, timer_callback)
            multi_setopt(multi, lcurl.CURLMOPT_TIMERDATA, ct.byref(timer_timeout))

            multi_add_handle(multi, curl)

            success = ct.c_int(0)
            while not checkForCompletion(multi, success):

                fd_read  = lcurl.fd_set()
                fd_write = lcurl.fd_set()

                max_fd = lcurl.socket_t(0)
                update_fd_set(sockets.read,  ct.byref(fd_read),  max_fd)
                update_fd_set(sockets.write, ct.byref(fd_write), max_fd)
                max_fd = max_fd.value

                if timer_timeout.tv_sec != -1:
                    usTimeout: int = getMicroSecondTimeout(timer_timeout)
                    timeout = lcurl.timeval(tv_sec=usTimeout // 1_000_000,
                                            tv_usec=usTimeout % 1_000_000)
                elif max_fd <= 0:
                    timeout = lcurl.timeval(tv_sec=0, tv_usec=100_000)  # 100 ms
                else:
                    timeout = lcurl.timeval(tv_sec=10, tv_usec=0)  # 10 sec
                select_test(max_fd,
                            ct.byref(fd_read), ct.byref(fd_write), None,
                            ct.byref(timeout))

                # Check the sockets for reading / writing
                check_fd_set(multi, sockets.read,  fd_read,  lcurl.CURL_CSELECT_IN,  "read")
                check_fd_set(multi, sockets.write, fd_write, lcurl.CURL_CSELECT_OUT, "write")

                if timer_timeout.tv_sec != -1 and getMicroSecondTimeout(timer_timeout) == 0:
                    # Curl's timer has elapsed.
                    notifyCurl(multi, lcurl.CURL_SOCKET_TIMEOUT, 0, "timeout")

                abort_on_test_timeout()

            if not success.value:
                print("Error uploading file.", file=sys.stderr)
                res = TEST_ERR_MAJOR_BAD

    # free local memory
    libc.free(sockets.read.sockets)
    libc.free(sockets.write.sockets)

    return res
