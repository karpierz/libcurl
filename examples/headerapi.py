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
Extract headers post transfer with the header API
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    # take care of the data here, ignored in this example
    return size * nitems


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://example.com"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url)
        # example.com is redirected, so we tell libcurl to follow redirection
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
        # this example just ignores the content
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)

        # Perform the request, res will get the return code
        res: int = lcurl.easy_perform(curl)
        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        header = ct.POINTER(lcurl.header)()
        resh = lcurl.easy_header(curl, "Content-Type", 0, lcurl.CURLH_HEADER, -1,
                                 ct.byref(header))
        if resh == lcurl.CURLHE_OK:
            header = header.contents
            print("Got content-type: %s" % header.value.decode("utf-8"))

        print("All server headers:")
        header = ct.POINTER(lcurl.header)()
        while True:
            header = lcurl.easy_nextheader(curl, lcurl.CURLH_HEADER, -1, header)
            if not header: break
            header = header.contents
            print(" %s: %s (%u)" % (header.name.decode("utf-8"),
                                    header.value.decode("utf-8"),
                                    header.amount))

  return 0


sys.exit(main())
