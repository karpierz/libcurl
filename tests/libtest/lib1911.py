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


# The maximum string length limit (CURL_MAX_INPUT_LENGTH) is an internal
# define not publicly exposed so we set our own
MAX_INPUT_LENGTH = 8000000

testbuf = (ct.c_char * (MAX_INPUT_LENGTH + 2))()


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    error: int = 0

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return lcurl.CURLcode(1).value

    easy: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, easy):
        if not easy: return lcurl.CURLcode(1).value

        # make it a null-terminated C string with just As
        ct.memset(testbuf, ord(b'A'), MAX_INPUT_LENGTH + 1)
        testbuf[MAX_INPUT_LENGTH + 1] = 0

        print("string length: %d" % strlen(testbuf))

        o: ct.POINTER(lcurl.easyoption) = lcurl.easy_option_next(None)
        while o:
            opt: lcurl.easyoption = o.contents

            if opt.type == lcurl.CURLOT_STRING:
                # Whitelist string options that are safe for abuse
                # CURL_IGNORE_DEPRECATION(
                if opt.id in (lcurl.CURLOPT_PROXY_TLSAUTH_TYPE,
                              lcurl.CURLOPT_TLSAUTH_TYPE,
                              lcurl.CURLOPT_RANDOM_FILE,
                              lcurl.CURLOPT_EGDSOCKET):
                    o = lcurl.easy_option_next(o)
                    continue
                else:
                    # check this
                    pass
                # )

                # This is a string. Make sure that passing in a string longer
                # libcurl.CURL_MAX_INPUT_LENGTH returns an error
                result: lcurl.CURLcode = lcurl.easy_setopt(easy, opt.id, testbuf)

                if result not in (lcurl.CURLE_BAD_FUNCTION_ARGUMENT,  # the most normal
                                  lcurl.CURLE_UNKNOWN_OPTION,         # left out from the build
                                  lcurl.CURLE_NOT_BUILT_IN,           # not supported
                                  lcurl.CURLE_UNSUPPORTED_PROTOCOL):  # detected by protocol2num()
                    # all other return codes are unexpected
                    print("libcurl.easy_setopt(%s...) returned %d" %
                          (opt.name.decode("utf-8"), result), file=sys.stderr)
                    error += 1

            o = lcurl.easy_option_next(o)

    return lcurl.CURLE_OK if error == 0 else TEST_ERR_FAILURE
