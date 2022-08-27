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
POP3 example using TLS
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 20, 0):
    print("This example requires curl 7.20.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to retrieve mail using libcurl's POP3
# capabilities. It builds on the pop3-retr.c example adding transport security
# to protect the authentication details from being snooped.

def main(argv=sys.argv[1:]):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This will retrieve message 1 from the user's mailbox
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, b"pop3://pop.example.com/1")
        # In this example, we will start with a plain text connection, and upgrade
        # to Transport Layer Security (TLS) using the STLS command. Be careful of
        # using libcurl.CURLUSESSL_TRY here, because if TLS upgrade fails,
        # the transfer will continue anyway - see the security discussion in the
        # libcurl tutorial for more details.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USE_SSL, lcurl.CURLUSESSL_ALL)
        # If your server does not have a valid certificate, then you can disable
        # part of the Transport Layer Security protection by setting the
        # CURLOPT_SSL_VERIFYPEER and CURLOPT_SSL_VERIFYHOST options to 0 (false).
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        #   lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
        #
        # That is, in general, a bad idea. It is still better than sending your
        # authentication details in plain text though.  Instead, you should get
        # the issuer certificate (or the host certificate if the certificate is
        # self-signed) and add it to the set of certificates that are known to
        # libcurl using CURLOPT_CAINFO and/or CURLOPT_CAPATH. See docs/SSLCERTS
        # for more information.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CAINFO, b"/path/to/certificate.pem")
        # Since the traffic will be encrypted, it is very useful to turn on debug
        # information within libcurl to see what is happening during the
        # transfer
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the retr
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
