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

import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# This test uses these funny custom memory callbacks for the only purpose
# of verifying that libcurl.global_init_mem() functionality is present in
# libcurl and that it works unconditionally no matter how libcurl is built,
# nothing more.
#
# Do not include memdebug.h in this source file, and do not use directly
# memory related functions in this file except those used inside custom
# memory callbacks which should be calling 'the real thing'.

seen: int = 0


@lcurl.malloc_callback
def custom_malloc(size: ct.c_size_t) -> ct.c_void_p:
    global seen
    seen += 1
    return libc.malloc(size)


@lcurl.calloc_callback
def custom_calloc(nmemb: ct.c_size_t, size: ct.c_size_t) -> ct.c_void_p:
    global seen
    seen += 1
    return libc.calloc(nmemb, size)


@lcurl.realloc_callback
def custom_realloc(ptr: ct.c_void_p, size: ct.c_size_t) -> ct.c_void_p:
    global seen
    seen += 1
    return libc.realloc(ptr, size)


@lcurl.free_callback
def custom_free(ptr: ct.c_void_p) -> None:
    global seen
    seen += 1
    return libc.free(ptr)


@lcurl.strdup_callback
def custom_strdup(str: ct.c_char_p) -> ct.c_void_p:
    global seen
    seen += 1
    return libc.strdup(str)


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    global seen ; seen = 0

    res: lcurl.CURLcode

    a = (ct.c_ubyte * 14)(0x2f, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f,
                          0x91, 0xa2, 0xb3, 0xc4, 0xd5, 0xe6, 0xf7)

    res = lcurl.global_init_mem(lcurl.CURL_GLOBAL_ALL,
                                custom_malloc,
                                custom_free,
                                custom_realloc,
                                custom_strdup,
                                custom_calloc)
    if res != lcurl.CURLE_OK:
        print("libcurl.global_init_mem() failed", file=sys.stderr)
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_USERAGENT, b"test509")  # uses strdup()

        asize: int = ct.sizeof(a)
        estr: bytes = lcurl.easy_escape(curl, ct.cast(a, ct.c_char_p), asize)  # uses realloc()

        if seen:
            print("Callbacks were invoked %d times!" % seen)
            sys.stdout.flush()

        del estr

    return res
