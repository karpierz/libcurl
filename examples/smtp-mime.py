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
SMTP example showing how to send mime emails
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 56, 0):
    print("This example requires curl 7.56.0 or later", file=sys.stderr)
    sys.exit(-1)


# This is a simple example showing how to send mime mail using libcurl's
# SMTP capabilities. For an example of using the multi interface please
# see smtp-multi.c.

FROM_MAIL = "<sender@example.org>"
TO_MAIL   = "<addressee@example.net>"
CC_MAIL   = "<info@example.org>"

headers_text: str = (
    "Date: Tue, 22 Aug 2017 14:08:43 +0100\n"
    f"To: {TO_MAIL}\n"
    f"From: {FROM_MAIL} (Example User)\n"
    f"Cc: {CC_MAIL} (Another example User)\n"
    "Message-ID: <dcd7cb36-11db-487a-9f3a-e652a9458efd@rfcpedant.example.org>\n"
    "Subject: example sending a MIME-formatted message\n"
)

inline_text: str = (
    "This is the inline text message of the email.\r\n"
    "\r\n"
    "  It could be a lot of lines that would be displayed in an email\r\n"
    "viewer that is not able to handle HTML.\r\n"
)

inline_html: str = (
    "<html><body>\r\n"
    "<p>This is the inline <b>HTML</b> message of the email.</p>"
    "<br />\r\n"
    "<p>It could be a lot of HTML data that would be displayed by "
    "email viewers able to handle HTML.</p>"
    "</body></html>\r\n"
)


def main(argv=sys.argv[1:]):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        # This is the URL for your mailserver
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, b"smtp://mail.example.com")
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
        # Build and set the message header list.
        headers = ct.POINTER(lcurl.slist)()
        for header in headers_text.splitlines():
            headers = lcurl.slist_append(headers, header.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headers)

        # Build the mime message.
        mime: ct.POINTER(lcurl.mime) = lcurl.mime_init(curl)
        # The inline part is an alternative proposing the html and
        # the text versions of the email.
        alt: ct.POINTER(lcurl.mime) = lcurl.mime_init(curl)
        part: ct.POINTER(lcurl.mimepart)

        # HTML message.
        part = lcurl.mime_addpart(alt)
        lcurl.mime_string(part, inline_html.encode("utf-8"))
        lcurl.mime_type(part, b"text/html")

        # Text message.
        part = lcurl.mime_addpart(alt)
        lcurl.mime_string(part, inline_text.encode("utf-8"))

        # Create the inline part.
        part = lcurl.mime_addpart(mime)
        lcurl.mime_subparts(part, alt)
        lcurl.mime_type(part, b"multipart/alternative")
        slist = lcurl.slist_append(None, b"Content-Disposition: inline")
        lcurl.mime_headers(part, slist, 1)

        # Add the current source program as an attachment.
        part = lcurl.mime_addpart(mime)
        lcurl.mime_filedata(part, b"smtp-mime.py")

        lcurl.easy_setopt(curl, lcurl.CURLOPT_MIMEPOST, mime)

        # Send the message
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # Free lists.
        lcurl.slist_free_all(recipients)
        lcurl.slist_free_all(headers)
        # Free multipart message.
        lcurl.mime_free(mime)
        # curl will not send the QUIT command until you call cleanup, so you
        # should be able to re-use this connection for additional messages
        # (setting CURLOPT_MAIL_FROM and CURLOPT_MAIL_RCPT as required, and
        # calling libcurl.easy_perform() again. It may not be a good idea to keep
        # the connection open for a very long time though (more than a few
        # minutes may result in the server timing out the connection), and you do
        # want to clean up in the end.

    return int(res)


sys.exit(main())
