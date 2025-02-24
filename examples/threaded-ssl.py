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
Show the required mutex callback setups for GnuTLS and OpenSSL when using
libcurl multi-threaded.
"""

import sys
import ctypes as ct
import threading

import libcurl as lcurl
from curl_utils import *  # noqa

# A multi-threaded example that uses pthreads and fetches 4 remote files at
# once over HTTPS.
#
# Recent versions of OpenSSL and GnuTLS are thread safe by design, assuming
# support for the underlying OS threading API is built-in. Older revisions
# of this example demonstrated locking callbacks for the SSL library, which
# are no longer necessary. An older revision with callbacks can be found at
# https://github.com/curl/curl/blob/curl-7_88_1/docs/examples/threaded-ssl.c

USE_OPENSSL = 1  # or USE_GNUTLS = 1 accordingly

# List of URLs to fetch.
urls = [
    "https://www.example.com/",
    "https://www2.example.com/",
    "https://www3.example.com/",
    "https://www4.example.com/",
]


def pull_one_url(url: str):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # this example does not verify the server's certificate,
        # which means we might be downloading stuff from an impostor
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

        # Perform the custom request
        lcurl.easy_perform(curl)  # ignores error


def main(argv=sys.argv[1:]):

    # Must initialize libcurl before any threads are started
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    with curl_guard(True) as guard:

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
