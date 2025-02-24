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
Show how CURLOPT_DEBUGFUNCTION can be used.
"""

from typing import Optional
import sys
import ctypes as ct
from dataclasses import dataclass

import libcurl as lcurl
from curl_utils import *  # noqa


@dataclass
class debug_config:
    trace_ascii: bool = False


@lcurl.debug_callback
def debug_function(curl, info_type, data, size, userptr):
    config = lcurl.from_oid(userptr)
    debug_output(info_type, None, data, size, config.trace_ascii, sys.stderr)
    return 0


def debug_output(info_type, num: Optional[int],
                 data: ct.POINTER(ct.c_ubyte), size: int, no_hex: bool, stream):

    if info_type == lcurl.CURLINFO_TEXT:
        if num is None:
            print("== Info: %s" % bytes(data[:size]).decode("utf-8"),
                  end="", file=stream)
        else:
            print("== [%d] Info: %s" % (num, bytes(data[:size]).decode("utf-8")),
                  end="", file=stream)
    else:
        if   info_type == lcurl.CURLINFO_HEADER_OUT:   text = "=> Send header"
        elif info_type == lcurl.CURLINFO_DATA_OUT:     text = "=> Send data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_OUT: text = "=> Send SSL data"
        elif info_type == lcurl.CURLINFO_HEADER_IN:    text = "<= Recv header"
        elif info_type == lcurl.CURLINFO_DATA_IN:      text = "<= Recv data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_IN:  text = "<= Recv SSL data"
        else: return 0  # in case a new one is introduced to shock us
        dump(num, text, data, size, no_hex, stream)

    return 0


def dump(num: Optional[int], text: str,
         data: ct.POINTER(ct.c_ubyte), size: int, no_hex: bool, stream):

    CR = 0x0D
    LF = 0x0A

    # without the hex output, we can fit more on screen
    width = 0x40 if no_hex else 0x10

    if num is None:
        print("%s, %d bytes (0x%x)" % (text, size, size), file=stream)
    else:
        print("%d %s, %d bytes (0x%x)" % (num, text, size, size), file=stream)

    for i in range(0, size, width):

        print("%04x: " % i, end="", file=stream)

        if not no_hex:
            # hex not disabled, show it
            for c in range(width):
                idx = i + c
                if idx < size:
                    print("%02x " % data[idx], end="", file=stream)
                else:
                    print("   ", end="", file=stream)

        for c in range(width):
            idx = i + c
            if idx >= size:
                break
            # check for CR/LF; if found, skip past and start a new line of output
            if (no_hex and (idx + 1) < size and
                data[idx] == CR and data[idx + 1] == LF):
                i += c + 2 - width
                break
            idx = i + c
            print("%c" % (data[idx] if 0x20 <= data[idx] < 0x80 else "."),
                  end="", file=stream)
            # check again for CR/LF, to avoid an extra \n if it's at width
            idx += 1
            if (no_hex and (idx + 1) < size and
                data[idx] == CR and data[idx + 1] == LF):
                i += c + 3 - width
                break

        print(file=stream)  # newline

    stream.flush()


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    config = debug_config(trace_ascii=True)  # enable ASCII tracing

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return 1

        # set the options (I left out a few, you will get the point anyway)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, id(config))
        # the DEBUGFUNCTION has no effect until we enable VERBOSE
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # example.com is redirected, so we tell libcurl to follow redirection
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


if __name__.rpartition(".")[-1] == "__main__":
    sys.exit(main())
