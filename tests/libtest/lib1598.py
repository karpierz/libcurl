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

# This unit test PUT http data over proxy. Proxy header will be different
# from server http header


@lcurl.trailer_callback
def trailers_callback(list: ct.POINTER(ct.POINTER(lcurl.slist)), userdata):
    #
    # carefully not leak memory on OOM
    #
    nlist:  ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
    nlist2: ct.POINTER(lcurl.slist) = ct.POINTER(lcurl.slist)()
    nlist = lcurl.slist_append(list.contents, b"my-super-awesome-trailer: trail1")
    if nlist:
        nlist2 = lcurl.slist_append(nlist, b"my-other-awesome-trailer: trail2")
    if not nlist2:
        lcurl.slist_free_all(nlist)
        return lcurl.CURL_TRAILERFUNC_ABORT
    list.contents = nlist2
    return lcurl.CURL_TRAILERFUNC_OK


post_data = b"xxx=yyy&aaa=bbbbb"

@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global post_data

    res: lcurl.CURLcode = lcurl.CURLE_FAILED_INIT

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # http and proxy header list
        hhl: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                             b"Trailer: my-super-awesome-trailer,"
                                             b" my-other-awesome-trailer")
        if not hhl: return res
        phl: ct.POINTER(lcurl.slist) = lcurl.slist_append(hhl,
                                             b"Transfer-Encoding: chunked")
        if phl: hhl = phl
        guard.add_slist(hhl)
        if not hhl: return res

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_HTTPHEADER, hhl)
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, len(post_data))
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDS, post_data)
        test_setopt(curl, lcurl.CURLOPT_TRAILERFUNCTION, trailers_callback)
        test_setopt(curl, lcurl.CURLOPT_TRAILERDATA, None)
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
