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
Expand an SMTP email mailing list
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 34, 0):
    print("This example requires curl 7.34.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to expand an email mailing list.
#
# Notes:
#
# 1) Not all email servers support this command.

def main(argv=sys.argv[1:]):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        # This is the URL for your mailserver
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, b"smtp://mail.example.com")
        # Note that the CURLOPT_MAIL_RCPT takes a list, not a char array
        recipients = ct.POINTER(lcurl.slist)()
        recipients = lcurl.slist_append(recipients, b"Friends")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_RCPT, recipients)
        # Set the EXPN command
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CUSTOMREQUEST, b"EXPN")

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

        # Free the list of recipients
        lcurl.slist_free_all(recipients)
        # curl does not send the QUIT command until you call cleanup, so you
        # should be able to reuse this connection for additional requests. It may
        # not be a good idea to keep the connection open for a long time though
        # (more than a few minutes may result in the server timing out the
        # connection) and you do want to clean up in the end.

    return int(res)


if __name__ == "__main__":
    sys.exit(main())
