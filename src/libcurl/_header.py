# Copyright (c) 2021-2022 Adam Karpierz
# Licensed under the MIT License
# https://opensource.org/licenses/MIT

# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 2018 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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

import ctypes as ct

from ._platform import CFUNC
from ._dll      import dll
from ._curl     import CURL

class header(ct.Structure):
    _fields_ = [
    ("name",   ct.c_char_p),  # this might not use the same case
    ("value",  ct.c_char_p),
    ("amount", ct.c_size_t),  # number of headers using this name
    ("index",  ct.c_size_t),  # ... of this instance, 0 or higher
    ("origin", ct.c_uint),    # see bits below
    ("anchor", ct.c_void_p),  # handle privately used by libcurl
]

# 'origin' bits
CURLH_HEADER  = (1 << 0)  # plain server header
CURLH_TRAILER = (1 << 1)  # trailers
CURLH_CONNECT = (1 << 2)  # CONNECT headers
CURLH_1XX     = (1 << 3)  # 1xx headers
CURLH_PSEUDO  = (1 << 4)  # pseudo headers

CURLHcode = ct.c_int
(
    CURLHE_OK,
    CURLHE_BADINDEX,       # header exists but not with this index
    CURLHE_MISSING,        # no such header exists
    CURLHE_NOHEADERS,      # no headers at all exist (yet)
    CURLHE_NOREQUEST,      # no request with this number was used
    CURLHE_OUT_OF_MEMORY,  # out of memory while processing
    CURLHE_BAD_ARGUMENT,   # a function argument was not okay
    CURLHE_NOT_BUILT_IN    # if API was disabled in the build
) = range(8)

easy_header = CFUNC(CURLHcode,
                    ct.POINTER(CURL),
                    ct.c_char_p,
                    ct.c_size_t,
                    ct.c_uint,
                    ct.c_int,
                    ct.POINTER(ct.POINTER(header)))(
                    ("curl_easy_header", dll), (
                    (1, "easy"),
                    (1, "name"),
                    (1, "index"),
                    (1, "origin"),
                    (1, "request"),
                    (1, "hout"),))

easy_nextheader = CFUNC(ct.POINTER(header),
                        ct.POINTER(CURL),
                        ct.c_uint,
                        ct.c_int,
                        ct.POINTER(header))(
                        ("curl_easy_nextheader", dll), (
                        (1, "easy"),
                        (1, "origin"),
                        (1, "request"),
                        (1, "prev"),))

# eof
