# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Max Dymond, <max.dymond@microsoft.com>
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


class PRCS(ct.Structure):
    _fields_ = [
    ("prereq_retcode", ct.c_int),
    ("ipv6",           ct.c_bool),
]


@lcurl.prereq_callback
def prereq_callback(clientp,
                    conn_primary_ip,   conn_local_ip,
                    conn_primary_port, conn_local_port):
    prereq_cb = ct.cast(clientp, ct.POINTER(PRCS)).contents

    if prereq_cb.ipv6:
        print("Connected to [%s]" % conn_primary_ip.decode("utf-8"))
        print("Connected from [%s]" % conn_local_ip.decode("utf-8"))
    else:
        print("Connected to %s" % conn_primary_ip.decode("utf-8"))
        print("Connected from %s" % conn_local_ip.decode("utf-8"))
    print("Remote port = %d" % conn_primary_port)
    print("Local port = %d" % conn_local_port)
    print("Returning = %d" % prereq_cb.prereq_retcode)

    return prereq_cb.prereq_retcode


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    prereq_cb = PRCS()
    prereq_cb.prereq_retcode = lcurl.CURL_PREREQFUNC_OK
    prereq_cb.ipv6 = False

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        if "#ipv6" in URL:
            # The IP addresses should be surrounded by brackets!
            prereq_cb.ipv6 = True
        if "#err" in URL:
            # Set the callback to exit with failure
            prereq_cb.prereq_retcode = lcurl.CURL_PREREQFUNC_ABORT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PREREQFUNCTION, prereq_callback)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PREREQDATA, ct.byref(prereq_cb))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_to_file)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sys.stderr.buffer))
        if "#redir" in URL:
            # Enable follow-location
            lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("%s:%d libcurl.easy_perform() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
            raise guard.Break

    return res
