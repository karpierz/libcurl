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
# Written by Lars Nilsson
#
# SPDX-License-Identifier: curl
#
#***************************************************************************

"""
Get a web page, extract the title with libxml.
"""

from dataclasses import dataclass
import sys
import io
import ctypes as ct

from lxml import etree
import libcurl as lcurl
from curltestutils import *  # noqa


@dataclass
class Context:
    """Context structure"""
    title: str = ""
    add_title: bool = False


class HTMLhandler:
    """Handler class"""

    def __init__(self):
        self.context = Context()

    def start(self, name, attrs):
        # start element callback function
        if name.upper() == "TITLE":
            self.context.title = ""
            self.context.add_title = True

    def end(self, name):
        # end element callback function
        if name.upper() == "TITLE":
            self.context.add_title = False

    def data(self, content):
        # PCDATA/CDATA callback function
        if self.context.add_title:
            self.context.title += (content.decode("utf-8")
                                   if isinstance(content, bytes) else
                                   content)
    def close(self):
        return self.context.title


def parse_HTML(html: bytes) -> str:
    """Parse given (assumed to be) HTML text and return the title"""
    html_handler = HTMLhandler()
    html_parser  = etree.HTMLParser(target=html_handler)
    etree.parse(io.BytesIO(html), html_parser)
    return html_handler.context.title


#
# libcurl variables for error strings and returned data

error_buffer = (ct.c_char * lcurl.CURL_ERROR_SIZE)()
data_buffer  = bytearray(b"")


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    # libcurl write callback function
    data_buffer = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    data_buffer += bytes(buffer[:buffer_size])
    return buffer_size


def init(curl: ct.POINTER(lcurl.CURL), url: str) -> bool:
    # libcurl connection initialization
    global error_buffer, data_buffer

    code: lcurl.CURLcode = lcurl.CURLE_OK

    code = lcurl.easy_setopt(curl, lcurl.CURLOPT_ERRORBUFFER, error_buffer)
    if code != lcurl.CURLE_OK:
        print("Failed to set error buffer [%d]" % code,
              file=sys.stderr)
        return False
    code = lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    if code != lcurl.CURLE_OK:
        print("Failed to set URL [%s]" % error_buffer.raw.decode("utf-8"),
              file=sys.stderr)
        return False
    if defined("SKIP_PEER_VERIFICATION"):
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    code = lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
    if code != lcurl.CURLE_OK:
        print("Failed to set redirect option [%s]" %
              error_buffer.raw.decode("utf-8"), file=sys.stderr)
        return False
    code = lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
    if code != lcurl.CURLE_OK:
        print("Failed to set writer [%s]" % error_buffer.raw.decode("utf-8"),
              file=sys.stderr)
        return False
    code = lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(data_buffer))
    if code != lcurl.CURLE_OK:
        print("Failed to set write data [%s]" % error_buffer.raw.decode("utf-8"),
              file=sys.stderr)
        return False

    return True


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    # Ensure one argument is given

    if len(argv) < 1:
        print("Usage: %s <URL>" % app_name)
        return 1

    url: str = argv[0]

    global error_buffer, data_buffer

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl:
            print("Failed to create CURL connection", file=sys.stderr)
            return 2

        # Initialize CURL connection
        if not init(curl, url):
            print("Connection initializion failed", file=sys.stderr)
            return 1

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            print("Failed to get '%s' [%s]" %
                  (url, error_buffer.raw.decode("utf-8")),
                  file=sys.stderr)
            return 1

    # Parse the (assumed) HTML code
    title = parse_HTML(data_buffer)

    # Display the extracted title
    print("Title: %s" % title)

    return 0


sys.exit(main())
