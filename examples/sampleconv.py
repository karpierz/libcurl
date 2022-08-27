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
This is a simple example showing how a program on a non-ASCII platform
would invoke callbacks to do its own codeset conversions instead of
using the built-in iconv functions in libcurl.
"""

import sys
import ctypes as ct

import ebcdic
import libcurl as lcurl
from curltestutils import *  # noqa


# The IBM-1047 EBCDIC codeset is used for this example but the code
# would be similar for other non-ASCII codesets.
#
# Three callback functions are created below:
#      my_conv_from_ascii_to_ebcdic,
#      my_conv_from_ebcdic_to_ascii, and
#      my_conv_from_utf8_to_ebcdic
#
# The "platform_xxx" calls represent platform-specific conversion routines.


def ascii_to_ebcdic(source: bytes) -> bytes:
    return source.decode("ascii").encode("cp1148")


def ebcdic_to_ascii(source: bytes) -> bytes:
    return source.decode("cp1148").encode("ascii")


def utf8_to_ebcdic(source: bytes) -> bytes:
    return source.decode("utf-8").encode("cp1148")


@lcurl.conv_callback
def my_conv_from_ascii_to_ebcdic(buffer, length):
    try:
        original  = bytes(buffer[:length])
        converted = ascii_to_ebcdic(bytes(buffer[:length]))
        ct.memmove(buffer, converted, len(converted))
    except:
        return lcurl.CURLE_CONV_FAILED
    else:
        return lcurl.CURLE_OK


@lcurl.conv_callback
def my_conv_from_ebcdic_to_ascii(buffer, length):
    try:
        original  = bytes(buffer[:length])
        converted = ebcdic_to_ascii(bytes(buffer[:length]))
        ct.memmove(buffer, converted, len(converted))
    except:
        return lcurl.CURLE_CONV_FAILED
    else:
        return lcurl.CURLE_OK


@lcurl.conv_callback
def my_conv_from_utf8_to_ebcdic(buffer, length):
    try:
        original  = bytes(buffer[:length])
        converted = utf8_to_ebcdic(bytes(buffer[:length]))
        ct.memmove(buffer, converted, len(converted))
    except:
        return lcurl.CURLE_CONV_FAILED
    else:
        return lcurl.CURLE_OK


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://example.com"

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # use platform-specific functions for codeset conversions
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CONV_FROM_NETWORK_FUNCTION,
                          my_conv_from_ascii_to_ebcdic)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CONV_TO_NETWORK_FUNCTION,
                          my_conv_from_ebcdic_to_ascii)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CONV_FROM_UTF8_FUNCTION,
                          my_conv_from_utf8_to_ebcdic)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
