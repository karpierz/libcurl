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
IMAP example using SSL
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 30, 0):
    print("This example requires curl 7.30.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to fetch mail using libcurl's
# IMAP capabilities. It builds on the imap-fetch.c example adding
# transport security to protect the authentication details from being
# snooped.

def main(argv=sys.argv[1:]):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This will fetch message 1 from the user's inbox. Note the use of
        # imaps:// rather than imap:// to request a SSL based connection.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL,
                          b"imaps://imap.example.com/INBOX/;UID=1")
        # If you want to connect to a site who is not using a certificate that is
        # signed by one of the certs in the CA bundle you have, you can skip the
        # verification of the server's certificate. This makes the connection
        # A LOT LESS SECURE.
        #
        # If you have a CA cert for the server stored someplace else than in the
        # default bundle, then the CURLOPT_CAPATH option might come handy for
        # you.
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # If the site you are connecting to uses a different host name that what
        # they have mentioned in their server certificate's commonName (or
        # subjectAltName) fields, libcurl will refuse to connect. You can skip
        # this check, but this will make the connection less secure.
        if defined("SKIP_HOSTNAME_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
        # Since the traffic will be encrypted, it is very useful to turn on debug
        # information within libcurl to see what is happening during the
        # transfer
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
