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


class chunk_data(ct.Structure):
    _fields_ = [
    ("remains",       ct.c_int),
    ("print_content", ct.c_bool),
]


@lcurl.chunk_bgn_callback
def chunk_bgn(transfer_info, ptr, remains):
    finfo = ct.cast(transfer_info, ct.POINTER(lcurl.fileinfo)).contents
    ch_d  = ct.cast(ptr, ct.POINTER(chunk_data)).contents

    ch_d.remains = remains

    print("=============================================================")
    print("Remains:      %d" % remains)
    print("Filename:     %s" % finfo.filename.decode("utf-8"))
    if finfo.strings.perm:
        print("Permissions:  %s" % finfo.strings.perm.decode("utf-8"), end="")
        if finfo.flags & lcurl.CURLFINFOFLAG_KNOWN_PERM:
            print(" (parsed => %o)" % finfo.perm, end="")
        print()
    print("Size:         %ldB" % finfo.size)
    if finfo.strings.user:
        print("User:         %s" % finfo.strings.user.decode("utf-8"))
    if finfo.strings.group:
        print("Group:        %s" % finfo.strings.group.decode("utf-8"))
    if finfo.strings.time:
        print("Time:         %s" % finfo.strings.time.decode("utf-8"))
    print("Filetype:     ", end="")
    if finfo.filetype == lcurl.CURLFILETYPE_FILE:
        print("regular file")
    elif finfo.filetype == lcurl.CURLFILETYPE_DIRECTORY:
        print("directory")
    elif finfo.filetype == lcurl.CURLFILETYPE_SYMLINK:
        print("symlink")
        print("Target:       %s" % finfo.strings.target.decode("utf-8"))
    else:
        print("other type")
    if finfo.filetype == lcurl.CURLFILETYPE_FILE:
        ch_d.print_content = True
        print("Content:\n"
              "-------------------------------------------------------------")
    if finfo.filename and finfo.filename.decode("utf-8") == "someothertext.txt":
        print("# THIS CONTENT WAS SKIPPED IN CHUNK_BGN CALLBACK #")
        return lcurl.CURL_CHUNK_BGN_FUNC_SKIP

    return lcurl.CURL_CHUNK_BGN_FUNC_OK


@lcurl.chunk_end_callback
def chunk_end(ptr):
    ch_d = ct.cast(ptr, ct.POINTER(chunk_data)).contents

    if ch_d.print_content:
        ch_d.print_content = False
        print("-------------------------------------------------------------")
    if ch_d.remains == 1:
        print("=============================================================")

    return lcurl.CURL_CHUNK_END_FUNC_OK


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    ch_d = chunk_data(0, 0)

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return int(lcurl.CURLE_OUT_OF_MEMORY)

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_WILDCARDMATCH, 1)
        test_setopt(curl, lcurl.CURLOPT_CHUNK_BGN_FUNCTION, chunk_bgn)
        test_setopt(curl, lcurl.CURLOPT_CHUNK_END_FUNCTION, chunk_end)
        test_setopt(curl, lcurl.CURLOPT_CHUNK_DATA, ct.byref(ch_d))

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
