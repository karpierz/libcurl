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


testpost = [
    "one",
    "two",
    "three",
    "and a final longer crap: four",
    None
]


class WriteThis(ct.Structure):
    _fields_ = [
    ("counter", ct.c_int),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(WriteThis)).contents
    buffer_size = nitems * size
    if buffer_size < 1: return 0
    data = testpost[pooh.counter]
    if data is None: return 0  # no more data left to deliver
    data = data.encode("utf-8")
    data_size = len(data)
    ct.memmove(buffer, data, data_size)
    pooh.counter += 1  # advance pointer
    return data_size


raport_file: str = None
started: bool = False
last_ul:       int = 0
last_ul_total: int = 0


def progress_start_report():
    global raport_file
    global started
    global last_ul
    global last_ul_total
    with open(raport_file, "ab") as moo:
        moo.write(b"Progress: start UL %lu/%lu\n" % (last_ul, last_ul_total))
        started = True


def progress_final_report():
    global raport_file
    global started
    global last_ul
    global last_ul_total
    with open(raport_file, "ab") as moo:
        moo.write(b"Progress: end UL %lu/%lu\n" % (last_ul, last_ul_total))
        started = False


@lcurl.progress_callback
def progress_callback(clientp, dltotal, dlnow, ultotal, ulnow):
    global started
    global last_ul
    global last_ul_total

    if started and ulnow <= 0.0 and last_ul:
        progress_final_report()

    last_ul       = int(ulnow)
    last_ul_total = int(ultotal)
    if not started:
        progress_start_report()

    return 0


@curl_test_decorator
def test(URL: str, raportfile: str,
         user_login: str = "foo:bar") -> lcurl.CURLcode:
    raportfile = str(raportfile)

    global raport_file
    raport_file = raportfile

    res: lcurl.CURLcode = lcurl.CURLE_OK

    pooh = WriteThis()
    pooh.counter = 0

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        slist: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                               b"Transfer-Encoding: chunked")
        if not slist:
            print("libcurl.slist_append() failed", file=sys.stderr)
            return TEST_ERR_MAJOR_BAD
        guard.add_slist(slist)

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # Now specify we want to POST data
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        # we want to use our own read function
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        # pointer to pass to our read function
        test_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(pooh))
        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        # enforce chunked transfer by setting the header
        test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, slist)
        test_setopt(curl, lcurl.CURLOPT_HTTPAUTH, lcurl.CURLAUTH_DIGEST)
        test_setopt(curl, lcurl.CURLOPT_USERPWD,
                          user_login.encode("utf-8") if user_login else None)
        # we want to use our own progress function
        test_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        # CURL_IGNORE_DEPRECATION(
        test_setopt(curl, lcurl.CURLOPT_PROGRESSFUNCTION, progress_callback)
        # )

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

        progress_final_report()

    return res
