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

# Check range/resume returned error codes and data presence.
#
# The input parameters are:
# - libcurl.CURLOPT_RANGE / libcurl.CURLOPT_RESUME_FROM
# - libcurl.CURLOPT_FAILONERROR
# - Returned http code (2xx/416)
# - Content-Range header present in reply.


# for debugging:
# SINGLETEST = 9

F_RESUME       = (1 << 0)  # resume/range.
F_HTTP416      = (1 << 1)  # Server returns http code 416.
F_FAIL         = (1 << 2)  # Fail on error.
F_CONTENTRANGE = (1 << 3)  # Server sends content-range hdr.
F_IGNOREBODY   = (1 << 4)  # Body should be ignored.


class test_params(ct.Structure):
    _fields_ = [
    ("flags",  ct.c_uint),       # ORed flags as above.
    ("result", lcurl.CURLcode),  # Code that should be returned by libcurl.easy_perform().
]


testparams = [
    test_params(0,                                                             lcurl.CURLE_OK),
    test_params(                                F_CONTENTRANGE,                lcurl.CURLE_OK),
    test_params(                       F_FAIL,                                 lcurl.CURLE_OK),
    test_params(                       F_FAIL | F_CONTENTRANGE,                lcurl.CURLE_OK),
    test_params(           F_HTTP416,                                          lcurl.CURLE_OK),
    test_params(           F_HTTP416 |          F_CONTENTRANGE,                lcurl.CURLE_OK),
    test_params(           F_HTTP416 | F_FAIL |                  F_IGNOREBODY, lcurl.CURLE_HTTP_RETURNED_ERROR),
    test_params(           F_HTTP416 | F_FAIL | F_CONTENTRANGE | F_IGNOREBODY, lcurl.CURLE_HTTP_RETURNED_ERROR),
    test_params(F_RESUME |                                       F_IGNOREBODY, lcurl.CURLE_RANGE_ERROR),
    test_params(F_RESUME |                      F_CONTENTRANGE,                lcurl.CURLE_OK),
    test_params(F_RESUME |             F_FAIL |                  F_IGNOREBODY, lcurl.CURLE_RANGE_ERROR),
    test_params(F_RESUME |             F_FAIL | F_CONTENTRANGE,                lcurl.CURLE_OK),
    test_params(F_RESUME | F_HTTP416 |                           F_IGNOREBODY, lcurl.CURLE_OK),
    test_params(F_RESUME | F_HTTP416 |          F_CONTENTRANGE | F_IGNOREBODY, lcurl.CURLE_OK),
    test_params(F_RESUME | F_HTTP416 | F_FAIL |                  F_IGNOREBODY, lcurl.CURLE_OK),
    test_params(F_RESUME | F_HTTP416 | F_FAIL | F_CONTENTRANGE | F_IGNOREBODY, lcurl.CURLE_OK),
]


hasbody: bool = False

@lcurl.write_callback
def write_callback(buffer, size, nitems, stream):
    global hasbody
    buffer_size = nitems * size
    if buffer_size:
        hasbody = True
    return buffer_size


def onetest(curl: ct.POINTER(lcurl.CURL), url: str, param: test_params, num: int) -> int:

    global hasbody

    res: lcurl.CURLcode

    reply_selector: int = 1 if (param.flags & F_CONTENTRANGE) else 0
    if param.flags & F_HTTP416:
        reply_selector += 2

    urlbuf: str = "%s/%04u" % (url.rstrip("/"), reply_selector)
    test_setopt(curl, lcurl.CURLOPT_URL, urlbuf.encode("utf-8"))
    test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
    test_setopt(curl, lcurl.CURLOPT_RESUME_FROM, (3 if (param.flags & F_RESUME) else 0))
    test_setopt(curl, lcurl.CURLOPT_RANGE,
                      (b"3-1000000" if not (param.flags & F_RESUME) else None))
    test_setopt(curl, lcurl.CURLOPT_FAILONERROR, (1 if (param.flags & F_FAIL) else 0))

    hasbody = False
    res = lcurl.easy_perform(curl)

    if res != param.result:
        print("%d: bad error code (%d): resume=%s, fail=%s, http416=%s, "
              "content-range=%s, expected=%d" % (num, res,
              ("yes" if (param.flags & F_RESUME)       else "no"),
              ("yes" if (param.flags & F_FAIL)         else "no"),
              ("yes" if (param.flags & F_HTTP416)      else "no"),
              ("yes" if (param.flags & F_CONTENTRANGE) else "no"),
              param.result))
        return 1
    if hasbody and (param.flags & F_IGNOREBODY):
        print("body should be ignored and is not: resume=%s, fail=%s, "
              "http416=%s, content-range=%s" % (
              ("yes" if (param.flags & F_RESUME)       else "no"),
              ("yes" if (param.flags & F_FAIL)         else "no"),
              ("yes" if (param.flags & F_HTTP416)      else "no"),
              ("yes" if (param.flags & F_CONTENTRANGE) else "no")))
        return 1

    return 0

    #test_cleanup:

    return 1


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode
    status: int = 0

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        for i, param in enumerate(testparams):

            curl: ct.POINTER(lcurl.CURL) = easy_init()
            if not curl: return TEST_ERR_EASY_INIT
            guard.add_curl(curl)

            test_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback)

            if not defined("SINGLETEST") or i == SINGLETEST:
                status |= onetest(curl, URL, param, i)

    print("%d" % status)

    return lcurl.CURLcode(status).value

    #test_cleanup:

    return res
