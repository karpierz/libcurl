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


@curl_test_decorator
def test(URL: str, new_URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # Begin with curl set to use a single CWD to the URL's directory.

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_SINGLECWD)

        res = lcurl.easy_perform(curl)

        # Change the FTP_FILEMETHOD option to use full paths rather than a CWD
        # command. Use an innocuous QUOTE command, after which curl will CWD to
        # ftp_conn->entrypath and then (on the next call to ftp_statemach_act)
        # find a non-zero ftpconn->dirdepth even though no directories are stored
        # in the ftpconn->dirs array (after a call to freedirs).

        slist: ct.POINTER(lcurl.slist) = lcurl.slist_append(None, b"SYST")
        if not slist: return TEST_ERR_MAJOR_BAD
        guard.add_slist(slist)

        test_setopt(curl, lcurl.CURLOPT_URL, new_URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_NOCWD)
        test_setopt(curl, lcurl.CURLOPT_QUOTE, slist)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
