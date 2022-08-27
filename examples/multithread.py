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
A multi-threaded example that uses pthreads to fetch several files at once
"""

import sys
import threading
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


# List of URLs to fetch.
#
# If you intend to use a SSL-based protocol here you might need to
# setup TLS library mutex callbacks as described here:
#
# https://curl.se/libcurl/c/threadsafe.html

urls = [
    "https://curl.se/",
    "ftp://example.com/",
    "https://example.net/",
    "www.example"
]


def pull_one_url(url: str):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)


def main(argv=sys.argv[1:]):

    # Must initialize libcurl before any threads are started
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    with curl_guard(True):

        threads = []
        for i, url in enumerate(urls):
            try:
                thread = threading.Thread(target=pull_one_url, args=(url,))
                thread.start()
            except Exception as exc:
                print("Couldn't run thread number %d, error %s" % (i, exc),
                      file=sys.stderr)
            else:
                threads.append(thread)
                print("Thread %d, gets %s" % (i, url), file=sys.stderr)

        # now wait for all threads to terminate
        for i, thread in enumerate(threads):
            thread.join()
            print("Thread %d terminated" % i, file=sys.stderr)

    return 0


sys.exit(main())
