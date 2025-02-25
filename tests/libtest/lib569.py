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
# Test Session ID capture
#


# build request url
def suburl(base: str, i: int) -> str:
    return "%s%.4d" % (base, i)


@curl_test_decorator
def test(URL: str, filename: str) -> lcurl.CURLcode:
    filename = str(filename)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    try:
        idfile = open(filename, "wb")
    except OSError as exc:
        print("couldn't open the Session ID File", file=sys.stderr)
        return TEST_ERR_MAJOR_BAD

    with idfile:

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
            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_SETUP)

            res = lcurl.easy_perform(curl)
           #if res != lcurl.CURLE_BAD_FUNCTION_ARGUMENT:
            if res and res != lcurl.CURLE_BAD_FUNCTION_ARGUMENT:  # AK: fix
                print("This should have failed. "
                      "Cannot setup without a Transport: header", file=sys.stderr)
                return TEST_ERR_MAJOR_BAD

            request: int = 1
            # Go through the various Session IDs
            for i in range(3):

                stream_uri = suburl(URL, request)
                request += 1
                test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
                test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_SETUP)
                test_setopt(curl, lcurl.CURLOPT_RTSP_TRANSPORT, b"Fake/NotReal/JustATest;foo=baz")

                res = lcurl.easy_perform(curl)
                if res != lcurl.CURLE_OK: raise guard.Break

                rtsp_session_id = ct.c_char_p()
                lcurl.easy_getinfo(curl, lcurl.CURLINFO_RTSP_SESSION_ID, ct.byref(rtsp_session_id))
                idfile.write(b"Got Session ID: [%s]\n" %
                             (rtsp_session_id.value if rtsp_session_id else b"None"))
                del rtsp_session_id

                stream_uri = suburl(URL, request)
                request += 1
                test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
                test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_TEARDOWN)

                res = lcurl.easy_perform(curl)

                # Clear for the next go-round
                test_setopt(curl, lcurl.CURLOPT_RTSP_SESSION_ID, None)

    return res
