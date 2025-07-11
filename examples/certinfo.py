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
Extract lots of TLS certificate info.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # we are not interested in the downloaded data itself
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_skipped)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE,  0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CERTINFO, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        handle_easy_perform_error(res)
        if res != lcurl.CURLE_OK:
            raise guard.Break

        certinfo = ct.POINTER(lcurl.certinfo)()
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_CERTINFO, ct.byref(certinfo))

        if res != lcurl.CURLE_OK or not certinfo:
            raise guard.Break

        certinfo = certinfo.contents
        print("%d certs!" % certinfo.num_of_certs)
        for i in range(certinfo.num_of_certs):
            print()
            slist: ct.POINTER(lcurl.slist) = certinfo.certinfo[i]
            while slist:
                 slist = slist[0]
                 print("%s" % slist.data.decode("utf-8"))
                 slist = slist.next

    return 0


if __name__ == "__main__":
    sys.exit(main())
