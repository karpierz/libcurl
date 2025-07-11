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
Search for new IMAP emails
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 30, 0):
    print("This example requires curl 7.30.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to search for new messages
# using libcurl's IMAP capabilities.

def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "imap://imap.example.com/INBOX"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This is mailbox folder to select
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # Set the SEARCH command specifying what we want to search for. Note that
        # this can contain a message sequence set and a number of search criteria
        # keywords including flags such as ANSWERED, DELETED, DRAFT, FLAGGED, NEW,
        # RECENT and SEEN. For more information about the search criteria please
        # see RFC-3501 section 6.4.4.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CUSTOMREQUEST, b"SEARCH NEW")

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


if __name__ == "__main__":
    sys.exit(main())
