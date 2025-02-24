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


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    with curl_guard(True) as guard:

        o: ct.POINTER(lcurl.easyoption)  = lcurl.easy_option_next(None)
        while o:
            ob = o[0]

            ename: lcurl.easyoption = lcurl.easy_option_by_name(ob.name)[0]
            eid:   lcurl.easyoption = lcurl.easy_option_by_id(ob.id)[0]

            if ename.id != ob.id:
                print("name lookup id %d doesn't match %d" % (ename.id, ob.id))
            elif eid.id != ob.id:
                print("ID lookup %d doesn't match %d" % (eid.id, ob.id))

            o = lcurl.easy_option_next(o)

    return lcurl.CURLE_OK
