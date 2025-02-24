# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) Linus Nielsen Feltzing <linus@haxx.se>
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

# Use global DNS cache (while deprecated it should still work), populate it
# with libcurl.CURLOPT_RESOLVE in the first request and then make sure
# a subsequent easy transfer finds and uses the populated stuff.

NUM_HANDLES = 2


@curl_test_decorator
def test(URL: str, address: str, port: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    curls = [ct.POINTER(lcurl.CURL)()] * NUM_HANDLES

    # URL is setup in the code

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        dns_entry: str = "server.example.curl:%s:%s" % (port, address)
        print("%s" % dns_entry)
        slist: ct.POINTER(lcurl.slist) = lcurl.slist_append(None,
                                               dns_entry.encode("utf-8"))
        guard.add_slist(slist)

        # get NUM_HANDLES easy handles
        for i in range(NUM_HANDLES):
            # get an easy handle
            curls[i] = curl = easy_init()
            # specify target
            target_url = "http://server.example.curl:%s/path/1512%04i" % (
                         port, i + 1)
            easy_setopt(curl, lcurl.CURLOPT_URL, target_url.encode("utf-8"))
            # go verbose
            easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            # include headers
            easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
            # CURL_IGNORE_DEPRECATION(
            easy_setopt(curl, lcurl.CURLOPT_DNS_USE_GLOBAL_CACHE, 1)
            # )

        # make the first one populate the GLOBAL cache
        easy_setopt(curls[0], lcurl.CURLOPT_RESOLVE, slist)

        # run NUM_HANDLES transfers
        for curl in curls:
            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: break

        # test_cleanup:

        for curl in curls:
            lcurl.easy_cleanup(curl)

    return res
