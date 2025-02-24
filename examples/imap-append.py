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
Send email with IMAP
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 30, 0):
    print("This example requires curl 7.30.0 or later", file=sys.stderr)
    sys.exit(-1)

# This is a simple example showing how to send mail using libcurl's
# IMAP capabilities.

FROM_MAIL = "<sender@example.org>"
TO_MAIL   = "<addressee@example.net>"
CC_MAIL   = "<info@example.org>"

payload_text: str = (
    "Date: Mon, 29 Nov 2010 21:54:29 +1100\r\n"
    f"To: {TO_MAIL}\r\n"
    f"From: {FROM_MAIL}(Example User)\r\n"
    f"Cc: {CC_MAIL}(Another example User)\r\n"
    "Message-ID: "
    "<dcd7cb36-11db-487a-9f3a-e652a9458efd@rfcpedant.example.org>\r\n"
    "Subject: IMAP example message\r\n"
    "\r\n"  # empty line to divide headers from body, see RFC 5322
    "The body of the message starts here.\r\n"
    "\r\n"
    "It could be a lot of lines, could be MIME encoded, whatever.\r\n"
    "Check RFC 5322.\r\n"
)

payload_data: bytes = payload_text.encode("utf-8")


class upload_status(ct.Structure):
    _fields_ = [
    ("bytes_read", ct.c_size_t),
]


@lcurl.read_callback
def payload_source(buffer, size, nitems, userp):
    upload_ctx = ct.cast(userp, ct.POINTER(upload_status)).contents
    buffer_size = nitems * size
    if buffer_size == 0: return 0
    data = payload_data[upload_ctx.bytes_read:]
    if not data: return 0
    nread = min(len(data), buffer_size)
    ct.memmove(buffer, data, nread)
    upload_ctx.bytes_read += nread
    return nread


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "imap://imap.example.com/Sent"

    upload_ctx = upload_status(0)

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        # Set username and password
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERNAME, b"user")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PASSWORD, b"secret")
        # This creates a new message in folder "Sent".
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # In this case, we are using a callback function to specify the data. You
        # could just use the CURLOPT_READDATA option to specify a FILE pointer to
        # read from.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, payload_source)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(upload_ctx))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE, min(len(payload_data),
                                                              LONG_MAX))
        # Send the message
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
