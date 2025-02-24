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
from curl_trace import *  # noqa


class transfer_status(ct.Structure):
    _fields_ = [
    ("easy",    ct.POINTER(lcurl.CURL)),
    ("halted",  ct.c_bool),
    ("counter", ct.c_int),  # count write callback invokes
    ("please",  ct.c_int),  # number of times xferinfo is called while halted
]


@lcurl.xferinfo_callback
def please_continue(clientp, dltotal, dlnow, ultotal, ulnow):
    st = ct.cast(clientp, ct.POINTER(transfer_status)).contents
    if st.halted:
        st.please += 1
        if st.please == 2:
            # waited enough, unpause!
            lcurl.easy_pause(st.easy, lcurl.CURLPAUSE_CONT)
    print("xferinfo: paused %r", st.halted, file=sys.stderr)
    return 0  # go on


@lcurl.write_callback
def header_callback(buffer, size, nitems, stream):
    file = sys.stdout.buffer
    buffer_size = nitems * size
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    file.write(bwritten)
    return buffer_size


@lcurl.write_callback
def write_callback(buffer, size, nitems, userp):
    st = ct.cast(userp, ct.POINTER(transfer_status)).contents
    file = sys.stdout.buffer
    buffer_size = nitems * size
    st.counter += 1
    if st.counter > 1:
        # the first call puts us on pause, so subsequent calls are after
        # unpause
        if buffer_size == 0: return 0
        bwritten = bytes(buffer[:buffer_size])
        file.write(bwritten)
        return buffer_size
    if buffer_size:
        print("Got bytes but pausing!")
    st.halted = True
    return lcurl.CURL_WRITEFUNC_PAUSE


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global libtest_debug_config, libtest_debug_cb

    res: lcurl.CURLcode = lcurl.CURLE_OK

    st = transfer_status()
    ct.memset(ct.byref(st), 0, ct.sizeof(st))

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        st.easy = curl  # to allow callbacks access

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback)
        easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(st))
        easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, header_callback)
        easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, ct.byref(st))
        easy_setopt(curl, lcurl.CURLOPT_XFERINFOFUNCTION, please_continue)
        easy_setopt(curl, lcurl.CURLOPT_XFERINFODATA, ct.byref(st))
        easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)

        libtest_debug_config.nohex     = 1
        libtest_debug_config.tracetime = 1
        test_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(libtest_debug_config))
        easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, libtest_debug_cb)
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res  # return the final return code
