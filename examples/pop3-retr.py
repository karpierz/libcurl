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

"""
Retrieve POP3 email
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 20, 0):
    print("This example requires curl 7.20.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to retrieve mail using libcurl's POP3
# capabilities.

def main(argv=sys.argv[1:]):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This retrieves message 1 from the user's mailbox
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, b"pop3://pop.example.com/1")

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


if __name__ == "__main__":
    sys.exit(main())
