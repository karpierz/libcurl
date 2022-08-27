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
Send email on behalf of another user with SMTP
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


# This is a simple example show how to send an email using libcurl's SMTP
# capabilities.
#
# Note that this example requires libcurl 7.66.0 or above.

# The libcurl options want plain addresses, the viewable headers in the mail
# can very well get a full name as well.

FROM_ADDR   = "<ursel@example.org>"
SENDER_ADDR = "<kurt@example.org>"
TO_ADDR     = "<addressee@example.net>"

FROM_MAIL   = f"Ursel {FROM_ADDR}"
SENDER_MAIL = f"Kurt {SENDER_ADDR}"
TO_MAIL     = f"A Receiver {TO_ADDR}"

payload_text: str = (
    "Date: Mon, 29 Nov 2010 21:54:29 +1100\r\n"
    f"To: {TO_MAIL}\r\n"
    f"From: {FROM_MAIL}\r\n"
    f"Sender: {SENDER_MAIL}\r\n"
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

    upload_ctx = upload_status(0)

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # This is the URL for your mailserver. In this example we connect to the
        # smtp-submission port as we require an authenticated connection.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, b"smtp://mail.example.com:587")
        # Set the username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"kurt")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"xipj3plmq")
        # Set the authorization identity (identity to act as)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SASL_AUTHZID, b"ursel")
        # Force PLAIN authentication
        lcurl.easy_setopt(curl, lcurl.CURLOPT_LOGIN_OPTIONS, b"AUTH=PLAIN")
        # Note that this option is not strictly required, omitting it will result
        # in libcurl sending the MAIL FROM command with empty sender data. All
        # autoresponses should have an empty reverse-path, and should be directed
        # to the address in the reverse-path which triggered them. Otherwise,
        # they could cause an endless loop. See RFC 5321 Section 4.5.5 for more
        # details.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_FROM, FROM_ADDR.encode("utf-8"))
        # Add a recipient, in this particular case it corresponds to the
        # To: addressee in the header.
        recipients = ct.POINTER(lcurl.slist)()
        recipients = lcurl.slist_append(recipients, TO_ADDR.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MAIL_RCPT, recipients)
        # We are using a callback function to specify the payload (the headers and
        # body of the message). You could just use the CURLOPT_READDATA option to
        # specify a FILE pointer to read from.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, payload_source)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(upload_ctx))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)

        # Send the message
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # Free the list of recipients
        lcurl.slist_free_all(recipients)
        # curl will not send the QUIT command until you call cleanup, so you
        # should be able to re-use this connection for additional messages
        # (setting CURLOPT_MAIL_FROM and CURLOPT_MAIL_RCPT as required, and
        # calling libcurl.easy_perform() again. It may not be a good idea to keep
        # the connection open for a very long time though (more than a few
        # minutes may result in the server timing out the connection), and you do
        # want to clean up in the end.

    return int(res)


sys.exit(main())
