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
IMAP example showing how to retreieve e-mails from a shared mailed box
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


# This is a simple example showing how to fetch mail using libcurl's
# IMAP capabilities.
#
# Note that this example requires libcurl 7.66.0 or above.

def main(argv=sys.argv[1:]):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # Set the username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # Set the authorization identity (identity to act as)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SASL_AUTHZID, b"shared-mailbox")
        # Force PLAIN authentication
        lcurl.easy_setopt(curl, lcurl.CURLOPT_LOGIN_OPTIONS, b"AUTH=PLAIN")
        # This will fetch message 1 from the user's inbox
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL,
                          b"imap://imap.example.com/INBOX/;UID=1")

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
