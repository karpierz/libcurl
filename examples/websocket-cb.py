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
WebSocket download-only using write callback
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


@lcurl.write_callback
def write_function(buffer, size, nitems, userp):
    easy = lcurl.from_oid(userp)
    frame = lcurl.ws_meta(easy).contents
    print("Type: %s" % ("binary" if frame.flags & lcurl.CURLWS_BINARY else "text"),
          file=sys.stderr)
    print("Bytes: %u" % (nitems * size), file=sys.stderr)
    for i in range(nitems):
        print("%02x " % buffer[i], end="", file=sys.stderr)
    return nitems


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "wss://example.com"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        # pass the easy handle to the callback
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(curl))

        # Perform the request, res gets the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
