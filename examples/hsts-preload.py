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
Preload domains to HSTS
"""

from typing import List
import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


class entry(ct.Structure):
    _fields_ = [
    ("name", ct.c_char_p),
    ("exp",  ct.c_char_p),
]

class state(ct.Structure):
    _fields_ = [
    ("index", ct.c_int),
]

preload_hosts: List[entry] = [
    entry(b"example.com", b"20370320 01:02:03"),
    entry(b"curl.se",     b"20370320 03:02:01"),
    entry(None, None)  # end of list marker
]


@lcurl.hstsread_callback
def hstsread(easy, entry, userp):
    # "read" is from the point of the library, it wants data from us.
    # One domain entry per invoke.
    entry = entry.contents
    st = ct.cast(userp, ct.POINTER(state)).contents

    host   = preload_hosts[st.index].name
    expire = preload_hosts[st.index].exp
    st.index += 1

    if host and len(host) < entry.namelen:
        entry.name = host + b"\0"
        entry.includeSubDomains = 0
        entry.expire = expire + b"\0"
        print("HSTS preload '%s' until '%s'" %
              (host.decode("utf-8"), expire.decode("utf-8")), file=sys.stderr)
    else:
        return lcurl.CURLSTS_DONE

    return lcurl.CURLSTS_OK


@lcurl.hstswrite_callback
def hstswrite(easy, entry, index, userp):
    entry = entry.contents
    index = index.contents
    print("[%u/%u] %s %s" % (index.index, index.total, entry.name, entry.expire))
    return lcurl.CURLSTS_OK


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "http://curl.se"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        st = state(0)

        # enable HSTS for this handle
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HSTS_CTRL, lcurl.CURLHSTS_ENABLE)
        # function to call at first to populate the cache before the transfer
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HSTSREADFUNCTION, hstsread)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HSTSREADDATA, ct.byref(st))
        # function to call after transfer to store the new state of the HSTS
        # cache
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HSTSWRITEFUNCTION, hstswrite)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HSTSWRITEDATA, None)
        # use the domain with HTTP but due to the preload, it should do the
        # transfer using HTTPS
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the request, res gets the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
