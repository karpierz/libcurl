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
Connection cache shared between easy handles with the share interface
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


@lcurl.lock_function
def my_lock(handle, data, locktype, useptr):
    print("-> Mutex lock", file=sys.stderr)


@lcurl.unlock_function
def my_unlock(handle, data, useptr):
    print("<- Mutex unlock", file=sys.stderr)


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://curl.se/"

    share: ct.POINTER(lcurl.CURLSH) = lcurl.share_init()

    lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE, lcurl.CURL_LOCK_DATA_CONNECT)
    lcurl.share_setopt(share, lcurl.CURLSHOPT_LOCKFUNC,   my_lock)
    lcurl.share_setopt(share, lcurl.CURLSHOPT_UNLOCKFUNC, my_unlock)

    # Loop the transfer and cleanup the handle properly every lap. This will
    # still reuse connections since the pool is in the shared object!

    for i in range(3):

        curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

        with curl_guard(False, curl):
            if not curl: continue

            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
            if defined("SKIP_PEER_VERIFICATION"):
                lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
            # use the share object
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SHARE, share)

            # Perform the request, res will get the return code
            res: int = lcurl.easy_perform(curl)

            # Check for errors
            if res != lcurl.CURLE_OK:
                handle_easy_perform_error(res)

    lcurl.share_cleanup(share)

    return 0


sys.exit(main())
