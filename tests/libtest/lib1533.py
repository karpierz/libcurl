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

# This test sends data with CURLOPT_KEEP_SENDING_ON_ERROR.
# The server responds with an early error response.
# The test is successful if the connection can be reused for the next request,
# because this implies that the data has been sent completely to the server.


class cb_data(ct.Structure):
    _fields_ = [
    ("easy_handle",       ct.POINTER(lcurl.CURL)),
    ("response_received", ct.c_bool),
    ("paused",            ct.c_bool),
    ("remaining_bytes",   ct.c_size_t),
]


def reset_data(data: cb_data, curl: ct.POINTER(lcurl.CURL)):
    data.easy_handle       = curl
    data.response_received = False
    data.paused            = False
    data.remaining_bytes   = 3


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    data = ct.cast(userp, ct.POINTER(cb_data)).contents
    # wait until the server has sent all response headers
    if not data.response_received:
        data.paused = True
        return lcurl.CURL_READFUNC_PAUSE
    total_size = nitems * size
    bytes_to_send = min(data.remaining_bytes, total_size)
    ct.memset(buffer, ord(b'a'), bytes_to_send)
    data.remaining_bytes -= bytes_to_send
    return bytes_to_send


@lcurl.write_callback
def write_callback(buffer, size, nitems, userp):
    data = ct.cast(userp, ct.POINTER(cb_data)).contents
    total_size = nitems * size
    # all response headers have been received
    data.response_received = True
    if data.paused:
        # continue to send request body data
        data.paused = False
        lcurl.easy_pause(data.easy_handle, lcurl.CURLPAUSE_CONT)
    return total_size


def perform_and_check_connections(curl: ct.POINTER(lcurl.CURL),
                                  description: str, expected_connections: int) -> int:
    res: lcurl.CURLcode

    res = lcurl.easy_perform(curl)
    if res != lcurl.CURLE_OK:
        print("libcurl.easy_perform() failed with %d" % res,
              file=sys.stderr)
        return TEST_ERR_MAJOR_BAD

    connections = ct.c_long(0)
    res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_NUM_CONNECTS,
                             ct.byref(connections))
    if res != lcurl.CURLE_OK:
        print("libcurl.easy_getinfo() failed", file=sys.stderr)
        return TEST_ERR_MAJOR_BAD

    print("%s: expected: %ld connections; actual: %ld connections" %
          (description, expected_connections, connections.value),
          file=sys.stderr)

    if connections.value != expected_connections:
        return TEST_ERR_FAILURE

    return TEST_ERR_SUCCESS


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = TEST_ERR_FAILURE
    result: int

    data = cb_data()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        reset_data(data, curl)

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE_LARGE,
                          data.remaining_bytes)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        test_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(data))
        test_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback)
        test_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(data))

        result = perform_and_check_connections(curl,
                 "First request without CURLOPT_KEEP_SENDING_ON_ERROR", 1)
        if result != TEST_ERR_SUCCESS:
            return lcurl.CURLcode(result).value

        reset_data(data, curl)

        result = perform_and_check_connections(curl,
                 "Second request without CURLOPT_KEEP_SENDING_ON_ERROR", 1)
        if result != TEST_ERR_SUCCESS:
            return lcurl.CURLcode(result).value

        test_setopt(curl, lcurl.CURLOPT_KEEP_SENDING_ON_ERROR, 1)

        reset_data(data, curl)

        result = perform_and_check_connections(curl,
                 "First request with CURLOPT_KEEP_SENDING_ON_ERROR", 1)
        if result != TEST_ERR_SUCCESS:
            return lcurl.CURLcode(result).value

        reset_data(data, curl)

        result = perform_and_check_connections(curl,
                 "Second request with CURLOPT_KEEP_SENDING_ON_ERROR", 0)
        if result != TEST_ERR_SUCCESS:
            return lcurl.CURLcode(result).value

        res = TEST_ERR_SUCCESS

    return res
