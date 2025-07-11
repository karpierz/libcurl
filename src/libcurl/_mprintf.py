# flake8-in-file-ignores: noqa: E305

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

class FILE(ct.Structure): pass
va_list = ct.c_void_p

if 0:  # deprecated
    mprintf = CFUNC(ct.c_int,
        ct.c_char_p,)(
        # ...)(
        ("curl_mprintf", dll), (
        (1, "format"),
        ))  # (1, "???"),))

    mfprintf = CFUNC(ct.c_int,
        ct.POINTER(FILE),
        ct.c_char_p,)(
        # ...)(
        ("curl_mfprintf", dll), (
        (1, "fd"),
        (1, "format"),
        ))  # (1, "???"),))

    msprintf = CFUNC(ct.c_int,
        ct.c_char_p,
        ct.c_char_p,)(
        # ...)(
        ("curl_msprintf", dll), (
        (1, "buffer"),
        (1, "format"),
        ))  # (1, "???"),))

    msnprintf = CFUNC(ct.c_int,
        ct.c_char_p,
        ct.c_size_t,
        ct.c_char_p,)(
        # ...)(
        ("curl_msnprintf", dll), (
        (1, "buffer"),
        (1, "maxlength"),
        (1, "format"),
        ))  # (1, "???"),))

    mvprintf = CFUNC(ct.c_int,
        ct.c_char_p,
        va_list)(
        ("curl_mvprintf", dll), (
        (1, "format"),
        (1, "args"),))

    mvfprintf = CFUNC(ct.c_int,
        ct.POINTER(FILE),
        ct.c_char_p,
        va_list)(
        ("curl_mvfprintf", dll), (
        (1, "fd"),
        (1, "format"),
        (1, "args"),))

    mvsprintf = CFUNC(ct.c_int,
        ct.c_char_p,
        ct.c_char_p,
        va_list)(
        ("curl_mvsprintf", dll), (
        (1, "buffer"),
        (1, "format"),
        (1, "args"),))

    mvsnprintf = CFUNC(ct.c_int,
        ct.c_char_p,
        ct.c_size_t,
        ct.c_char_p,
        va_list)(
        ("curl_mvsnprintf", dll), (
        (1, "buffer"),
        (1, "maxlength"),
        (1, "format"),
        (1, "args"),))

    maprintf = CFUNC(ct.c_char_p,
        ct.c_char_p,)(
        # ...)(
        ("curl_maprintf", dll), (
        (1, "format"),
        ))  # (1, "???"),))

    mvaprintf = CFUNC(ct.c_char_p,
        ct.c_char_p,
        va_list)(
        ("curl_mvaprintf", dll), (
        (1, "format"),
        (1, "args"),))

# eof
