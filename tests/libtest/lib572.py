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

#
# Test GET_PARAMETER: PUT, HEARTBEAT, and POST
#


# build request url
def suburl(base: str, i: int) -> str:
    return "%s%.4d" % (base, i)


@curl_test_decorator
def test(URL: str, filename: str) -> lcurl.CURLcode:
    filename = str(filename)

    res: lcurl.CURLcode

    request: int = 1

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, lcurl.write_to_file)
        test_setopt(curl, lcurl.CURLOPT_HEADERDATA, id(sys.stdout.buffer))
        test_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_to_file)
        test_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sys.stdout.buffer))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # SETUP
        stream_uri = suburl(URL, request)
        request += 1
        test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_RTSP_TRANSPORT, b"Planes/Trains/Automobiles")
        test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_SETUP)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        stream_uri = suburl(URL, request)
        request += 1
        test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))

        # PUT style GET_PARAMETERS

        try:
            paramsf = open(filename, "rb")
        except OSError as exc:
            print("can't open %s" % filename, file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        with paramsf:

            file_len: int = file_size(paramsf)

            custom_headers: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
            guard.add_slist(custom_headers)

            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_GET_PARAMETER)
            test_setopt(curl, lcurl.CURLOPT_READFUNCTION, lcurl.read_from_file)
            test_setopt(curl, lcurl.CURLOPT_READDATA, id(paramsf))
            test_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
            test_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, file_len)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            test_setopt(curl, lcurl.CURLOPT_UPLOAD, 0)

            # paramsf.close() ; paramsf = None

            # Heartbeat GET_PARAMETERS
            stream_uri = suburl(URL, request)
            request += 1
            test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            # POST GET_PARAMETERS
            stream_uri = suburl(URL, request)
            request += 1
            test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_GET_PARAMETER)
            test_setopt(curl, lcurl.CURLOPT_POSTFIELDS, b"packets_received\njitter\n")

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            test_setopt(curl, lcurl.CURLOPT_POSTFIELDS, None)
            # Make sure we can do a normal request now
            stream_uri = suburl(URL, request)
            request += 1
            test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_OPTIONS)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

    return res
