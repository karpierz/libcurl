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
Access HTTP server over Unix domain socket
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

if is_windows:
    print("This example requires unix", file=sys.stderr)
    sys.exit(0)

if defined("USE_ABSTRACT"):
  # The abstract socket namespace is a nonportable Linux extension.
  # The name has no connection with filesystem pathnames.
  ABSTRACT = "http-unix-domain"
else:
  PATH = "/tmp/http-unix-domain"


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "http://example.com"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        if defined("USE_ABSTRACT"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_ABSTRACT_UNIX_SOCKET, ABSTRACT)
        else:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_UNIX_SOCKET_PATH, PATH)

        # Perform the request, res gets the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
