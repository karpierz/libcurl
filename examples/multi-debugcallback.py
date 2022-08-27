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
Multi interface and debug callback
"""

from dataclasses import dataclass
import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa
from debug import debug_function


@dataclass
class debug_config:
    trace_ascii: bool = False


#
# Simply download a HTTP file.
#

def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    config = debug_config(True)  # enable ascii tracing

    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    curl:  ct.POINTER(lcurl.CURL)  = lcurl.easy_init()

    with curl_guard(False, curl, mcurl):
        if not curl:  return 1
        if not mcurl: return 2

        # set the options (I left out a few, you will get the point anyway)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, id(config))
        # the DEBUGFUNCTION has no effect until we enable VERBOSE
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # example.com is redirected, so we tell libcurl to follow redirection
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)

        # add the individual transfers
        lcurl.multi_add_handle(mcurl, curl)

        still_running = ct.c_int(1)  # keep number of running handles
        while still_running.value:
            mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            if still_running.value:
                # wait for activity, timeout or "nothing"
                mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mc:
                break

    return 0


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
