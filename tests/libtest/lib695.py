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


@lcurl.write_callback
def write_it(buffer, size, nitems, userp):
    # write callback that does nothing
    return size * nitems


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:
    #
    # Check proper rewind when reusing a mime structure.
    #
    res: lcurl.CURLcode = TEST_ERR_FAILURE

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    mime1: ct.POINTER(lcurl.mime) = ct.POINTER(lcurl.mime)()
    mime2: ct.POINTER(lcurl.mime) = ct.POINTER(lcurl.mime)()
    part:  ct.POINTER(lcurl.mimepart)

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our POST.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))

        # get verbose debug output please
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Do not write anything.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_it)

        # Build the first mime structure.
        mime1 = lcurl.mime_init(curl)
        part  = lcurl.mime_addpart(mime1)
        lcurl.mime_data(part, ct.cast(b"<title>hello</title>",
                                      ct.POINTER(ct.c_ubyte)),
                              lcurl.CURL_ZERO_TERMINATED)
        lcurl.mime_type(part, b"text/html")
        lcurl.mime_name(part, b"data")

        # Use first mime structure as top level MIME POST.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime1)

        # Perform the request, res gets the return code
        res = lcurl.easy_perform(curl)
        # Check for errors
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() 1 failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)
            raise guard.Break

        # phase two, create a mime struct using the mime1 handle
        mime2 = lcurl.mime_init(curl)
        part  = lcurl.mime_addpart(mime2)

        # use the new mime setup
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime2)

        # Reuse previous mime structure as a child.
        res = lcurl.mime_subparts(part, mime1)

        if res != lcurl.CURLE_OK:
            print("libcurl.mime_subparts() failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)
            raise guard.Break

        mime1 = ct.POINTER(lcurl.mime)()

        # Perform the request, res gets the return code
        res = lcurl.easy_perform(curl)
        # Check for errors
        if res != lcurl.CURLE_OK:
            print("libcurl.easy_perform() 2 failed: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)
            raise guard.Break

    # test_cleanup:

    lcurl.mime_free(mime1)
    lcurl.mime_free(mime2)
    lcurl.global_cleanup()

    return res
