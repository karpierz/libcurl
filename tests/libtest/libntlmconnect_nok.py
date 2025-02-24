# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 2012 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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

from typing import List
import sys
import enum
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# from warnless.c
def curlx_sztosi(sznum) -> int: return int(sznum)


TEST_HANG_TIMEOUT = 60 * 1000
MAX_EASY_HANDLES  = 3

ntlm_curls:    List[ct.POINTER(lcurl.CURL)] = [ct.POINTER(lcurl.CURL)()] * MAX_EASY_HANDLES
ntlm_sockets:  List[lcurl.socket_t]         = [lcurl.CURL_SOCKET_BAD]    * MAX_EASY_HANDLES
ntlm_counters: List[int]                    = [0]                        * MAX_EASY_HANDLES

ntlmcb_res: lcurl.CURLcode = lcurl.CURLE_OK


@lcurl.write_callback
def write_callback(buffer, size, nitems, userp):
    idx: int = int(userp)

    global ntlmcb_res

    buffer_size = nitems * size
    failure = 0 if buffer_size else 1

    global ntlm_curls, ntlm_sockets, ntlm_counters

    curl: ct.POINTER(lcurl.CURL) = ntlm_curls[idx]

    ntlm_counters[idx] += buffer_size

    # Get socket being used for this easy handle, otherwise libcurl.CURL_SOCKET_BAD
    last_sock = ct.c_long()
    # CURL_IGNORE_DEPRECATION(
    code: lcurl.CURLcode = lcurl.easy_getinfo(curl, lcurl.CURLINFO_LASTSOCKET,
                                              ct.byref(last_sock))
    # )
    if code != lcurl.CURLE_OK:
        print("%s:%d libcurl.easy_getinfo() failed, with code %d (%s)" %
              (current_file(), current_line(),
               code, lcurl.easy_strerror(code).decode("utf-8")), file=sys.stderr)
        ntlmcb_res = TEST_ERR_MAJOR_BAD
        return failure

    last_sock = last_sock.value

    sock: lcurl.socket_t = last_sock if last_sock != -1 else lcurl.CURL_SOCKET_BAD

    if sock != lcurl.CURL_SOCKET_BAD:
        # Track relationship between this easy handle and the socket.
        if ntlm_sockets[idx] == lcurl.CURL_SOCKET_BAD:
            # An easy handle without previous socket, record the socket.
            ntlm_sockets[idx] = sock
        elif sock != ntlm_sockets[idx]:
            # An easy handle with a socket different to previously
            # tracked one, log and fail right away. Known bug #37.
            print("Handle %d started on socket %d and moved to %d" %
                  (curlx_sztosi(idx), ntlm_sockets[idx], sock),
                  file=sys.stderr)
            ntlmcb_res = TEST_ERR_MAJOR_BAD
            return failure

    return buffer_size


@curl_test_decorator
def test(URL: str, user_login: str = "testuser:testpass") -> lcurl.CURLcode:

    global ntlm_curls, ntlm_sockets, ntlm_counters
    global ntlmcb_res

    class HandleState(enum.IntEnum):
        ReadyForNewHandle      = 0
        NeedSocketForNewHandle = 1
        NoMoreHandles          = 3

    res: lcurl.CURLcode = lcurl.CURLE_OK

    state: HandleState = HandleState.ReadyForNewHandle

    start_test_timing()

    for i in range(len(ntlm_curls)):
        ntlm_curls[i]   = ct.POINTER(lcurl.CURL)()
        ntlm_sockets[i] = lcurl.CURL_SOCKET_BAD

    res = res_global_init(lcurl.CURL_GLOBAL_ALL)
    if res: return res
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, mcurl=multi) as guard:

        num_handles: int = 0
        while True:

            found_new_socket = False

            # Start a new handle if we aren't at the max
            if state == HandleState.ReadyForNewHandle:

                ntlm_curls[num_handles] = curl = easy_init()

                if num_handles % 3 == 2:
                    full_url: str = "%s0200" % URL
                    easy_setopt(curl, lcurl.CURLOPT_HTTPAUTH, lcurl.CURLAUTH_NTLM)
                else:
                    full_url: str = "%s0100" % URL
                    easy_setopt(curl, lcurl.CURLOPT_HTTPAUTH, lcurl.CURLAUTH_BASIC)
                easy_setopt(curl, lcurl.CURLOPT_FRESH_CONNECT, 1)
                easy_setopt(curl, lcurl.CURLOPT_URL, full_url.encode("utf-8"))
                easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
                easy_setopt(curl, lcurl.CURLOPT_HTTPGET, 1)
                easy_setopt(curl, lcurl.CURLOPT_USERPWD,
                                  user_login.encode("utf-8") if user_login else None)
                easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback)
                easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, num_handles)
                easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)

                multi_add_handle(multi, curl)

                num_handles += 1
                state = HandleState.NeedSocketForNewHandle
                res = ntlmcb_res

            running = ct.c_int()
            multi_perform(multi, ct.byref(running))

            print("%s:%d running %d state %d" %
                  (current_file(), current_line(), running.value, state),
                  file=sys.stderr)

            abort_on_test_timeout(TEST_HANG_TIMEOUT)

            if not running.value and state == HandleState.NoMoreHandles:
                break  # done

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            max_fd = ct.c_int(-99)
            multi_fdset(multi,
                        ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                        ct.byref(max_fd))
            max_fd = max_fd.value

            # At this point, max_fd is guaranteed to be greater or equal than -1.

            if state == HandleState.NeedSocketForNewHandle:
                if max_fd != -1 and not found_new_socket:
                    print("Warning: socket did not open immediately for new "
                          "handle (trying again)", file=sys.stderr)
                    continue
                state = (HandleState.ReadyForNewHandle
                         if num_handles < len(ntlm_curls) else
                         HandleState.NoMoreHandles)
                print("%s:%d new state %d" %
                      (current_file(), current_line(), state), file=sys.stderr)

            curl_timeout = ct.c_long(-99)
            multi_timeout(multi, ct.byref(curl_timeout))
            curl_timeout = curl_timeout.value

            # At this point, timeout is guaranteed to be greater or equal than -1.

            print("%s:%d num_handles %d timeout %ld running %d" %
                  (current_file(), current_line(),
                   num_handles, curl_timeout, running.value), file=sys.stderr)

            # if there's no timeout and we get here on the last handle, we may
            # already have read the last part of the stream so waiting makes no
            # sense
            if curl_timeout == -1 and not running.value and num_handles >= len(ntlm_curls):
                break

            if curl_timeout != -1:
                tv_usec = min(LONG_MAX, INT_MAX, curl_timeout)
                timeout = lcurl.timeval(tv_sec=tv_usec // 1000,
                                        tv_usec=(tv_usec % 1000) * 1000)
            else:
                timeout = lcurl.timeval(tv_sec=0, tv_usec=5_000)  # 5 ms
            select_test(max_fd + 1,
                        ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                        ct.byref(timeout))

            abort_on_test_timeout(TEST_HANG_TIMEOUT)

        # test_cleanup:

        for i, curl in ntlm_curls:
            print("Data connection %d: %d" % (i, ntlm_counters[i]))
            lcurl.multi_remove_handle(multi, curl)
            curl_easy_cleanup(curl)

    return res
