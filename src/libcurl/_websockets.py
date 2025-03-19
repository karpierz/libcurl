# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

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

import ctypes as ct

from ._platform import CFUNC
from ._dll      import dll
from ._curl     import off_t, CURLcode, CURL

class ws_frame(ct.Structure):
    _fields_ = [
    ("age",       ct.c_int),     # zero
    ("flags",     ct.c_int),     # See the CURLWS_* defines
    ("offset",    off_t),        # the offset of this data into the frame
    ("bytesleft", off_t),        # number of pending bytes left of the payload
    ("len",       ct.c_size_t),  # size of the current data chunk
]

# flag bits
CURLWS_TEXT   = (1 << 0)
CURLWS_BINARY = (1 << 1)
CURLWS_CONT   = (1 << 2)
CURLWS_CLOSE  = (1 << 3)
CURLWS_PING   = (1 << 4)
CURLWS_OFFSET = (1 << 5)

# NAME curl_ws_recv()
#
# DESCRIPTION
#
# Receives data from the websocket connection. Use after successful
# curl_easy_perform() with CURLOPT_CONNECT_ONLY option.
#
try:  # libcurl >= 7.86.0
    ws_recv = CFUNC(CURLcode,
        ct.POINTER(CURL),
        ct.c_void_p,
        ct.c_size_t,
        ct.POINTER(ct.c_size_t),
        ct.POINTER(ct.POINTER(ws_frame)))(
        ("curl_ws_recv", dll), (
        (1, "curl"),
        (1, "buffer"),
        (1, "buflen"),
        (1, "recv"),
        (1, "metap"),))
except: pass  # noqa: E722 # pragma: no cover

# flags for curl_ws_send()
CURLWS_PONG = (1 << 6)

# NAME curl_ws_send()
#
# DESCRIPTION
#
# Sends data over the websocket connection. Use after successful
# curl_easy_perform() with CURLOPT_CONNECT_ONLY option.
#
try:  # libcurl >= 7.86.0
    ws_send = CFUNC(CURLcode,
        ct.POINTER(CURL),
        ct.c_void_p,
        ct.c_size_t,
        ct.POINTER(ct.c_size_t),
        off_t,
        ct.c_uint)(
        ("curl_ws_send", dll), (
        (1, "curl"),
        (1, "buffer"),
        (1, "buflen"),
        (1, "sent"),
        (1, "fragsize"),
        (1, "flags"),))
except: pass  # noqa: E722 # pragma: no cover

# bits for the CURLOPT_WS_OPTIONS bitmask:
CURLWS_RAW_MODE = (1 << 0)

try:  # libcurl >= 7.86.0
    ws_meta = CFUNC(ct.POINTER(ws_frame),
        ct.POINTER(CURL))(
        ("curl_ws_meta", dll), (
        (1, "curl"),))
except: pass  # noqa: E722 # pragma: no cover

# eof
