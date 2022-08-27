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
Checks if HTTP/3 support is present in libcurl.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def main(argv=sys.argv[1:]):

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    with curl_guard(True):
        # lcurl.version_info_data* ver
        ver = lcurl.version_info(lcurl.CURLVERSION_NOW).contents

        if ver.features & lcurl.CURL_VERSION_HTTP2:
          print("HTTP/2 support is present")

        if ver.features & lcurl.CURL_VERSION_HTTP3:
          print("HTTP/3 support is present")

        if ver.features & lcurl.CURL_VERSION_ALTSVC:
          print("Alt-svc support is present")

    return 0


sys.exit(main())
