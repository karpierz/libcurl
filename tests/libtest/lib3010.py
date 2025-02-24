# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Nicolas Sterchele, <nicolas@sterchelen.net>
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


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    ret: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))

        ret = lcurl.easy_perform(curl)
        if ret:
            print("%s:%d lcurl.easy_perform() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   ret, lcurl.easy_strerror(ret).decode("utf-8")), file=sys.stderr)
            raise guard.Break

        follow_url  = ct.c_char_p(None)
        retry_after = lcurl.off_t()
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_REDIRECT_URL, ct.byref(follow_url))
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_RETRY_AFTER,  ct.byref(retry_after))
        print(("Retry-After %" + lcurl.CURL_FORMAT_CURL_OFF_T) % retry_after.value)
        if follow_url:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, follow_url.value)

        ret = lcurl.easy_perform(curl)
        if ret:
            print("%s:%d lcurl.easy_perform() failed with code %d (%s)" %
                  (current_file(), current_line(),
                   ret, lcurl.easy_strerror(ret).decode("utf-8")), file=sys.stderr)
            raise guard.Break

        lcurl.easy_reset(curl)
        lcurl.easy_getinfo(curl, lcurl.CURLINFO_RETRY_AFTER, ct.byref(retry_after))
        print(("Retry-After %" + lcurl.CURL_FORMAT_CURL_OFF_T) % retry_after.value)

    return ret
