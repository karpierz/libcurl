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
SMTP example showing how to verify an email address
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 34, 0):
    print("This example requires curl 7.34.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to verify an email address from an
# SMTP server.
#
# Notes:
#
# 1) Not all email servers support this command and even if your email server
#    does support it, it may respond with a 252 response code even though the
#    address does not exist.

def main(argv=sys.argv[1:]):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # This is the URL for your mailserver
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, b"smtp://mail.example.com")
        # Note that the CURLOPT_MAIL_RCPT takes a list, not a char array
        recipients = ct.POINTER(lcurl.slist)()
        recipients = lcurl.slist_append(recipients, b"<recipient@example.com>")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_RCPT, recipients)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # Free the list of recipients
        lcurl.slist_free_all(recipients)
        # curl will not send the QUIT command until you call cleanup, so you
        # should be able to re-use this connection for additional requests. It
        # may not be a good idea to keep the connection open for a very long time
        # though (more than a few minutes may result in the server timing out the
        # connection) and you do want to clean up in the end.

    return 0


sys.exit(main())
