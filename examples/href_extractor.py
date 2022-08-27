#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 2012 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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
Uses the "Streaming HTML parser" to extract the href pieces in a streaming
manner from a downloaded HTML.
"""

import sys
import ctypes as ct
from html.parser import HTMLParser

import libcurl as lcurl
from curltestutils import *  # noqa


class HTML_Parser(HTMLParser):

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, value in attrs:
                if attr == "href":
                    print("%s" % value)

    def handle_endtag(self, tag):
        if tag == "a":
            pass


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    html_parser = lcurl.from_oid(stream)
    buffer_size = size * nitems
    #if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    html_parser.feed(bwritten.decode("utf-8"))
    return buffer_size


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 1:
        print("Usage: %s <URL>" % app_name)
        return 1

    url: str = argv[0]

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):

        html_parser = HTML_Parser()

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(html_parser))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        html_parser.close()

    return 0


sys.exit(main())
