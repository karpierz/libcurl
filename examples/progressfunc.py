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
Use the progress callbacks, old and/or new one depending on available
libcurl version.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 61, 0):
    # 1. xferinfo was introduced in 7.32.0, no earlier libcurl versions
    #    will compile as they will not have the symbols around.
    # 2. In libcurl 7.61.0, support was added for extracting the time in
    #    plain microseconds.
    print("This example requires curl 7.61.0 or later", file=sys.stderr)
    sys.exit(-1)


MINIMAL_PROGRESS_FUNCTIONALITY_INTERVAL = 3000000
STOP_DOWNLOAD_AFTER_THIS_MANY_BYTES     = 6000


class myprogress(ct.Structure):
    _fields_ = [
    ("lastruntime", lcurl.off_t),
    ("curl",        ct.POINTER(lcurl.CURL)),
]


@lcurl.xferinfo_callback
def xferinfo(clientp, dltotal, dlnow, ultotal, ulnow):
    # this is how the CURLOPT_XFERINFOFUNCTION callback works
    client = ct.cast(clientp, ct.POINTER(myprogress)).contents
    curl   = ct.POINTER(lcurl.CURL)(client.curl)

    curtime = lcurl.off_t(0)
    lcurl.easy_getinfo(curl, lcurl.CURLINFO_TOTAL_TIME_T, ct.byref(curtime))
    curtime_value = curtime.value

    # under certain circumstances it may be desirable for certain functionality
    # to only run every N seconds, in order to do this the transaction time can
    # be used
    time_difference = curtime_value - client.lastruntime
    if time_difference >= MINIMAL_PROGRESS_FUNCTIONALITY_INTERVAL:
        client.lastruntime = curtime_value
        print("TOTAL TIME: %u.%06u" %
              (curtime_value // 1000000, curtime_value % 1000000),
              file=sys.stderr)

    print("UP: %u of %u  DOWN: %u of %u" %
          (ulnow, ultotal, dlnow, dltotal), file=sys.stderr)

    if dlnow > STOP_DOWNLOAD_AFTER_THIS_MANY_BYTES:
        return 1

    return 0


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://example.com/"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        progress = myprogress(0, curl)

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_XFERINFOFUNCTION, xferinfo)
        # pass the struct pointer into the xferinfo function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_XFERINFODATA, ct.byref(progress))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
