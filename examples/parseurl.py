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
Basic URL API use.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 62, 0):
    print("This example requires curl 7.62.0 or later", file=sys.stderr)
    sys.exit(-1)


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "http://example.com/path/index.html"

    # get a handle to work with
    curlu: ct.POINTER(lcurl.CURLU) = lcurl.url()
    if not curlu:
        return 1

    uc: lcurl.CURLUcode

    # parse a full URL
    uc = lcurl.url_set(curlu, lcurl.CURLUPART_URL, url.encode("utf-8"), 0)
    if uc:
        lcurl.url_cleanup(curlu)  # free url handle
        return 1

    # extract host name from the parsed URL
    host = ct.c_char_p()
    uc = lcurl.url_get(curlu, lcurl.CURLUPART_HOST, ct.byref(host), 0)
    if not uc:
        print("Host name: %s" % host.value.decode("utf-8"))
        lcurl.free(host)

    # extract the path from the parsed URL
    path = ct.c_char_p()
    uc = lcurl.url_get(curlu, lcurl.CURLUPART_PATH, ct.byref(path), 0)
    if not uc:
        print("Path: %s" % path.value.decode("utf-8"))
        lcurl.free(path)

    # redirect with a relative URL
    uc = lcurl.url_set(curlu, lcurl.CURLUPART_URL, b"../another/second.html", 0)
    if uc:
        lcurl.url_cleanup(curlu)  # free url handle
        return 1

    # extract the new, updated path
    uc = lcurl.url_get(curlu, lcurl.CURLUPART_PATH, ct.byref(path), 0)
    if not uc:
        print("Path: %s" % path.value.decode("utf-8"))
        lcurl.free(path)

    lcurl.url_cleanup(curlu)  # free url handle

    return 0


sys.exit(main())
