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
Use getinfo to get content-type after completed transfer.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)
        else:
            # ask for the content-type
            ctype = ct.c_char_p()
            res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_CONTENT_TYPE, ct.byref(ctype))

            if res == lcurl.CURLE_OK and ctype:
                print("We received Content-Type: %s" % ctype.value.decode("utf-8"))

    return 0


sys.exit(main())
