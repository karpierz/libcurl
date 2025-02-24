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
Outputs all protocols and features supported
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 87, 0):
    print("This example requires curl 7.87.0 or later", file=sys.stderr)
    sys.exit(-1)


def main(argv=sys.argv[1:]):

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    with curl_guard(True) as guard:
        ver = lcurl.version_info(lcurl.CURLVERSION_NOW).contents

        print("Protocols:")
        for protocol in ver.protocols:
            if not protocol: break
            print("  %s" % protocol)
        print("Features:")
        for feature in ver.feature_names:
            if not feature: break
            print("  %s" % feature)

    return 0


sys.exit(main())
