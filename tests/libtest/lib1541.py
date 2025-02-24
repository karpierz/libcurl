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


class transfer_status(ct.Structure):
    _fields_ = [
    ("easy",     ct.POINTER(lcurl.CURL)),
    ("hd_count", ct.c_int),
    ("bd_count", ct.c_int),
    ("result",   lcurl.CURLcode),
]


def geterr(name: str, val: lcurl.CURLcode, lineno: int) -> int:
    print('CURLINFO_%s returned %d, "%s" on line %d' %
          (name, val, lcurl.easy_strerror(val).decode("utf-8"), lineno))
    return int(val)


def report_time(key: str, where: str, time: int, ok: bool):
    if ok:
        print("%s on %s is OK" % (key, where))
    else:
        print(("%s on %s is WRONG: %" + lcurl.CURL_FORMAT_CURL_OFF_T) %
              (key, where, time))


def check_time(easy: ct.POINTER(lcurl.CURL), key: int, name: str, where: str):
    tval = lcurl.off_t()
    res: lcurl.CURLcode = lcurl.easy_getinfo(easy, key, ct.byref(tval))
    tval = tval.value
    if res != lcurl.CURLE_OK:
        geterr(name, res, current_line(2))
    else:
        report_time(name, where, tval, tval > 0)


def check_time0(easy: ct.POINTER(lcurl.CURL), key: int, name: str, where: str):
    tval = lcurl.off_t()
    res: lcurl.CURLcode = lcurl.easy_getinfo(easy, key, ct.byref(tval))
    tval = tval.value
    if res != lcurl.CURLE_OK:
        geterr(name, res, current_line(2))
    else:
        report_time(name, where, tval, not tval)


@lcurl.write_callback
def header_callback(buffer, size, nitems, userp):
    st = ct.cast(userp, ct.POINTER(transfer_status)).contents
    total_size = nitems * size
    if st.hd_count == 0:
        # first header, check some CURLINFO value to be reported. See #13125
        check_time(st.easy, lcurl.CURLINFO_CONNECT_TIME_T,
                            "CURLINFO_CONNECT_TIME_T",       "1st header")
        check_time(st.easy, lcurl.CURLINFO_PRETRANSFER_TIME_T,
                            "CURLINFO_PRETRANSFER_TIME_T",   "1st header")
        check_time(st.easy, lcurl.CURLINFO_STARTTRANSFER_TIME_T,
                            "CURLINFO_STARTTRANSFER_TIME_T", "1st header")
        # continuously updated
        check_time(st.easy, lcurl.CURLINFO_TOTAL_TIME_T,
                            "CURLINFO_TOTAL_TIME_T",         "1st header")
        # no SSL, must be 0
        check_time0(st.easy, lcurl.CURLINFO_APPCONNECT_TIME_T,
                            "CURLINFO_APPCONNECT_TIME_T",    "1st header")
        # download not really started
        check_time0(st.easy, lcurl.CURLINFO_SPEED_DOWNLOAD_T,
                            "CURLINFO_SPEED_DOWNLOAD_T",     "1st header")
    sys.stdout.buffer.write(bytes(buffer[:total_size]))
    st.hd_count += 1
    return total_size


@lcurl.write_callback
def write_callback(buffer, size, nitems, userp):
    st = ct.cast(userp, ct.POINTER(transfer_status)).contents
    total_size = nitems * size
    sys.stdout.buffer.write(bytes(buffer[:total_size]))
    return total_size


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    st = transfer_status()
    ct.memset(ct.byref(st), 0, ct.sizeof(st))

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()
    st.easy = curl  # to allow callbacks access

    with curl_guard(True, curl) as guard:

        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback)
        easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(st))
        easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, header_callback)
        easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, ct.byref(st))

        easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)

        res = lcurl.easy_perform(curl)

        check_time(curl, lcurl.CURLINFO_CONNECT_TIME_T,
                         "CURLINFO_CONNECT_TIME_T",       "done")
        check_time(curl, lcurl.CURLINFO_PRETRANSFER_TIME_T,
                         "CURLINFO_PRETRANSFER_TIME_T",   "done")
        check_time(curl, lcurl.CURLINFO_POSTTRANSFER_TIME_T,
                         "CURLINFO_POSTTRANSFER_TIME_T",  "done")
        check_time(curl, lcurl.CURLINFO_STARTTRANSFER_TIME_T,
                         "CURLINFO_STARTTRANSFER_TIME_T", "done")
        # no SSL, must be 0
        check_time0(curl, lcurl.CURLINFO_APPCONNECT_TIME_T,
                         "CURLINFO_APPCONNECT_TIME_T",    "done")
        check_time(curl, lcurl.CURLINFO_SPEED_DOWNLOAD_T,
                         "CURLINFO_SPEED_DOWNLOAD_T",     "done")
        check_time(curl, lcurl.CURLINFO_TOTAL_TIME_T,
                         "CURLINFO_TOTAL_TIME_T",         "done")

    return res  # return the final return code
