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
Download a given URL into a local file named page.out.
"""

import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curl_utils import *  # noqa

here = Path(__file__).resolve().parent

PAGE_FILENAME = here/"page.out"


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 1:
        print("Usage: python %s <URL>" % app_name)
        return 1

    url: str = argv[0]

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # init the curl session
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return 1

        # set URL to get here
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # Switch on full protocol/debug output while testing
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # disable progress meter, set to 0 to enable it
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        # send all data to this function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_to_file)

        # open the file
        with PAGE_FILENAME.open("wb") as page_file:
            # write the page body to this file handle
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(page_file))

            # get it!
            lcurl.easy_perform(curl)

    return 0


sys.exit(main())
