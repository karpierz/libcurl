#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 1998 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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
#***************************************************************************

"""
IMAP example showing how to modify the properties of an email
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 30, 0):
    print("This example requires curl 7.30.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to modify an existing mail
# using libcurl's IMAP capabilities with the STORE command.

def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "imap://imap.example.com/INBOX"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This is the mailbox folder to select
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # Set the STORE command with the Deleted flag for message 1. Note that
        # you can use the STORE command to set other flags such as Seen, Answered,
        # Flagged, Draft and Recent.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CUSTOMREQUEST, b"STORE 1 +Flags \\Deleted")

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)
        else:
            # Set the EXPUNGE command, although you can use the CLOSE command
            # if you do not want to know the result of the STORE
            lcurl.easy_setopt(curl, lcurl.CURLOPT_CUSTOMREQUEST, b"EXPUNGE")

            # Perform the second custom request
            res = lcurl.easy_perform(curl)

            # Check for errors
            if res != lcurl.CURLE_OK:
                handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
