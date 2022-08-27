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
Shows HTTPS usage with client certs and optional ssl engine use.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


# An SSL-enabled libcurl is required for this sample to work (at least
# one SSL backend has to be configured).
#
#  **** This example only works with libcurl 7.56.0 and later! ****

def main(argv=sys.argv[1:]):

    name: str = argv[0] if len(argv) >= 1 else "openssl"

    result: lcurl.CURLsslset

    if name == "list":
        backend_list = ct.POINTER(ct.POINTER(lcurl.ssl_backend))()
        result = lcurl.global_sslset(lcurl.sslbackend(-1), None, ct.byref(backend_list))
        assert result == lcurl.CURLSSLSET_UNKNOWN_BACKEND

        i = 0
        while backend_list[i]:
            item = backend_list[i][0]
            print("SSL backend #%d: '%s' (ID: %d)" %
                  (i, item.name.decode("utf-8"), item.id))
            i += 1
        return 0
    elif name[0].isdigit():
        id = int(name)
        result = lcurl.global_sslset(lcurl.sslbackend(id), None, None)
    else:
        result = lcurl.global_sslset(lcurl.sslbackend(-1), name.encode("utf-8"), None)

    if result == lcurl.CURLSSLSET_UNKNOWN_BACKEND:
        print("Unknown SSL backend id: %s" % name, file=sys.stderr)
        return 1

    assert result == lcurl.CURLSSLSET_OK

    print("Version with SSL backend '%s':\n\n\t%s" %
          (name, lcurl.version().decode("utf-8")))

    return 0


sys.exit(main())
