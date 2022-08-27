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
HTTP PUT using CURLOPT_POSTFIELDS
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


olivertwist: bytes = (
    b"Among other public buildings in a certain town, which for many reasons "
    b"it will be prudent to refrain from mentioning, and to which I will assign "
    b"no fictitious name, there is one anciently common to most towns, great or "
    b"small: to wit, a workhouse; and in this workhouse was born; on a day and "
    b"date which I need not trouble myself to repeat, inasmuch as it can be of "
    b"no possible consequence to the reader, in this stage of the business at "
    b"all events; the item of mortality whose name is prefixed to the head of "
    b"this chapter."
)

#
# This example shows a HTTP PUT operation that sends a fixed buffer
# with CURLOPT_POSTFIELDS to the URL given as an argument.
#

def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 1:
        print("Usage: %s <URL>" % app_name)
        return 1

    url: str = argv[0]

    # In windows, this will init the winsock stuff
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        # specify target URL, and note that this URL should include a file
        # name, not only a directory
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # default type with postfields is application/x-www-form-urlencoded,
        # change it if you want
        headers = ct.POINTER(lcurl.slist)()
        headers = lcurl.slist_append(headers, b"Content-Type: literature/classic")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headers)
        # pass on content in request body. When CURLOPT_POSTFIELDSIZE is not used,
        # curl does strlen to get the size.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, olivertwist)
        # override the POST implied by CURLOPT_POSTFIELDS
        #
        # Warning: CURLOPT_CUSTOMREQUEST is problematic, especially if you want
        # to follow redirects. Be aware.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CUSTOMREQUEST, b"PUT")

        # Now run off and do what you have been told!
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # free headers
        lcurl.slist_free_all(headers)

    return 0


sys.exit(main())
