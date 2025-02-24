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
Download many files in parallel, in the same thread.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

MAX_PARALLEL = 10  # number of simultaneous transfers

urls = [
    b"https://www.microsoft.com",
    b"https://opensource.org",
    b"https://www.google.com",
    b"https://www.yahoo.com",
    b"https://www.ibm.com",
    b"https://www.mysql.com",
    b"https://www.oracle.com",
    b"https://www.ripe.net",
    b"https://www.iana.org",
    b"https://www.amazon.com",
    b"https://www.netcraft.com",
    b"https://www.heise.de",
    b"https://www.chip.de",
    b"https://www.ca.com",
    b"https://www.cnet.com",
    b"https://www.mozilla.org",
    b"https://www.cnn.com",
    b"https://www.wikipedia.org",
    b"https://www.dell.com",
    b"https://www.hp.com",
    b"https://www.cert.org",
    b"https://www.mit.edu",
    b"https://www.nist.gov",
    b"https://www.ebay.com",
    b"https://www.playstation.com",
    b"https://www.uefa.com",
    b"https://www.ieee.org",
    b"https://www.apple.com",
    b"https://www.symantec.com",
    b"https://www.zdnet.com",
    b"https://www.fujitsu.com/global/",
    b"https://www.supermicro.com",
    b"https://www.hotmail.com",
    b"https://www.ietf.org",
    b"https://www.bbc.co.uk",
    b"https://news.google.com",
    b"https://www.foxnews.com",
    b"https://www.msn.com",
    b"https://www.wired.com",
    b"https://www.sky.com",
    b"https://www.usatoday.com",
    b"https://www.cbs.com",
    b"https://www.nbc.com/",
    b"https://slashdot.org",
    b"https://www.informationweek.com",
    b"https://apache.org",
    b"https://www.un.org",
]


def add_transfer(mcurl: ct.POINTER(lcurl.CURLM), url: bytes, left: int):
    curl: ct.POINTER(CURL) = lcurl.easy_init()
    # we are not interested in the downloaded data itself
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_skipped)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL,     url)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_PRIVATE, url)
    if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    lcurl.multi_add_handle(mcurl, curl)
    return left + 1


def main(argv=sys.argv[1:]):

    global urls

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    with curl_guard(True, None, mcurl) as guard:
        if not mcurl: return 2

        # Limit the amount of simultaneous connections curl should allow:
        lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_MAXCONNECTS, MAX_PARALLEL)

        left: int = 0
        for transfers in range(min(MAX_PARALLEL, len(urls))):
            left = add_transfer(mcurl, urls[transfers], left)
        transfers = min(MAX_PARALLEL, len(urls))

        while True:
            still_running = ct.c_int(1)
            lcurl.multi_perform(mcurl, ct.byref(still_running))

            while True:
                msgs_left = ct.c_int(-1)
                msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(mcurl,
                                                                        ct.byref(msgs_left))
                if not msgp: break
                msg = msgp.contents

                if msg.msg == lcurl.CURLMSG_DONE:
                    curl: ct.POINTER(lcurl.CURL) = msg.easy_handle
                    url = ct.c_char_p()
                    lcurl.easy_getinfo(curl, lcurl.CURLINFO_PRIVATE, ct.byref(url))
                    print("R: %d - %s <%s" %
                          (msg.data.result,
                           lcurl.easy_strerror(msg.data.result).decode("utf-8"),
                           url.value.decode("utf-8")),
                          file=sys.stderr)
                    lcurl.multi_remove_handle(mcurl, curl)
                    lcurl.easy_cleanup(curl)
                    left -= 1
                else:
                    print("E: CURLMsg (%d)" % msg.msg, file=sys.stderr)

                if transfers < len(urls):
                    left = add_transfer(mcurl, urls[transfers], left)
                    transfers += 1

            if left == 0:
                break

            lcurl.multi_wait(mcurl, None, 0, 1000, None)

    return 0


sys.exit(main())
