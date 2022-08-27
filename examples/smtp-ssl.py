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
SMTP example using SSL
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 20, 0):
    print("This example requires curl 7.20.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to send mail using libcurl's SMTP
# capabilities. It builds on the smtp-mail.c example to add authentication
# and, more importantly, transport security to protect the authentication
# details from being snooped.

FROM_MAIL = "<sender@example.com>"
TO_MAIL   = "<recipient@example.com>"
CC_MAIL   = "<info@example.com>"

payload_text: str = (
    "Date: Mon, 29 Nov 2010 21:54:29 +1100\r\n"
    f"To: {TO_MAIL}\r\n"
    f"From: {FROM_MAIL}\r\n"
    f"Cc: {CC_MAIL}\r\n"
    "Message-ID: <dcd7cb36-11db-487a-9f3a-e652a9458efd@"
    "rfcpedant.example.org>\r\n"
    "Subject: SMTP example message\r\n"
    "\r\n"  # empty line to divide headers from body, see RFC5322
    "The body of the message starts here.\r\n"
    "\r\n"
    "It could be a lot of lines, could be MIME encoded, whatever.\r\n"
    "Check RFC5322.\r\n"
)

payload_data: bytes = payload_text.encode("utf-8")


class upload_status(ct.Structure):
    _fields_ = [
    ("bytes_read", ct.c_size_t),
]


@lcurl.read_callback
def payload_source(buffer, size, nitems, stream):
    upload_ctx = ct.cast(stream, ct.POINTER(upload_status)).contents
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    data = payload_data[upload_ctx.bytes_read:]
    if not data: return 0
    nread = min(len(data), buffer_size)
    ct.memmove(buffer, data, nread)
    upload_ctx.bytes_read += nread
    return nread


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "smtps://mainserver.example.net"

    res: lcurl.CURLcode = lcurl.CURLE_OK
    upload_ctx = upload_status(0)

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This is the URL for your mailserver. Note the use of smtps:// rather
        # than smtp:// to request a SSL based connection.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
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
        # Note that this option is not strictly required, omitting it will result
        # in libcurl sending the MAIL FROM command with empty sender data. All
        # autoresponses should have an empty reverse-path, and should be directed
        # to the address in the reverse-path which triggered them. Otherwise,
        # they could cause an endless loop. See RFC 5321 Section 4.5.5 for more
        # details.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_FROM, FROM_MAIL.encode("utf-8"))
        # Add two recipients, in this particular case they correspond to the
        # To: and Cc: addressees in the header, but they could be any kind of
        # recipient.
        recipients = ct.POINTER(lcurl.slist)()
        recipients = lcurl.slist_append(recipients, TO_MAIL.encode("utf-8"))
        recipients = lcurl.slist_append(recipients, CC_MAIL.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_RCPT, recipients)
        # We are using a callback function to specify the payload (the headers and
        # body of the message). You could just use the CURLOPT_READDATA option to
        # specify a FILE pointer to read from.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, payload_source)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(upload_ctx))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # Since the traffic will be encrypted, it is very useful to turn on debug
        # information within libcurl to see what is happening during the
        # transfer
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Send the message
        res = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # Free the list of recipients
        lcurl.slist_free_all(recipients)

    return int(res)


sys.exit(main())
