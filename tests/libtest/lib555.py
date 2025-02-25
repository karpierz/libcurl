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

# This test case is supposed to be identical to 547 except that this uses the
# multi interface and 547 is easy interface.
#
# argv1 = URL
# argv2 = proxy
# argv3 = proxyuser:password


uploadthis = b"this is the blurb we want to upload\n"


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    counter = ct.cast(userp, ct.POINTER(ct.c_int)).contents

    if counter.value:
        # only do this once and then require a clearing of this
        print("READ ALREADY DONE!", file=sys.stderr)
        return 0

    counter.value += 1  # bump

    data_size = len(uploadthis)

    if data_size > nitems * size:
        print("READ NOT FINE!", file=sys.stderr)
        return 0

    print("READ!", file=sys.stderr)
    ct.memmove(buffer, uploadthis, data_size + 1)
    return data_size


@lcurl.ioctl_callback
def ioctl_callback(handle, cmd, clientp):
    counter = ct.cast(clientp, ct.POINTER(ct.c_int)).contents

    if cmd == lcurl.CURLIOCMD_RESTARTREAD:
        print("REWIND!", file=sys.stderr)
        counter.value = 0  # clear counter to make the read callback restart

    return lcurl.CURLIOE_OK


@curl_test_decorator
def test(URL: str,
         proxy: str = None,
         proxy_login: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    counter = ct.c_int(0)

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl:  ct.POINTER(lcurl.CURL)  = easy_init()
    multi: ct.POINTER(lcurl.CURLM) = multi_init()

    with curl_guard(True, curl, multi) as guard:
        if not curl:  return TEST_ERR_EASY_INIT
        if not multi: return TEST_ERR_MULTI

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)

        # read the POST data from a callback
        # CURL_IGNORE_DEPRECATION(
        easy_setopt(curl, lcurl.CURLOPT_IOCTLFUNCTION, ioctl_callback)
        easy_setopt(curl, lcurl.CURLOPT_IOCTLDATA, ct.byref(counter))
        # )
        easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(counter))
        # We CANNOT do the POST fine without setting the size (or choose
        # chunked)!
        easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, len(uploadthis))

        easy_setopt(curl, lcurl.CURLOPT_POST, 1)
        easy_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)
        easy_setopt(curl, lcurl.CURLOPT_PROXYUSERPWD,
                          proxy_login.encode("utf-8") if proxy_login else None)
        easy_setopt(curl, lcurl.CURLOPT_PROXYAUTH, lcurl.CURLAUTH_BASIC |
                          lcurl.CURLAUTH_DIGEST | lcurl.CURLAUTH_NTLM)

        multi_add_handle(multi, curl)

        still_running = ct.c_int(1)
        while still_running.value:
            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

            if not still_running.value:
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

            timeout = lcurl.timeval(tv_sec=0, tv_usec=100_000)  # 100 ms
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout()

    return res
