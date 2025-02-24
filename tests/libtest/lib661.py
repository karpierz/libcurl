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
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # test: libcurl.CURLFTPMETHOD_SINGLECWD with absolute path should
        #       skip CWD to entry path
        test_setopt(curl, lcurl.CURLOPT_URL, b"%s/folderA/661" % URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_IGNORE_CONTENT_LENGTH, 1)
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_SINGLECWD)
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_REMOTE_FILE_NOT_FOUND: raise guard.Break

        test_setopt(curl, lcurl.CURLOPT_URL, b"%s/folderB/661" % URL.encode("utf-8"))
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_REMOTE_FILE_NOT_FOUND: raise guard.Break

        # test: libcurl.CURLFTPMETHOD_NOCWD with absolute path should
        #       never emit CWD (for both new and reused easy handle)
        lcurl.easy_cleanup(curl)
        curl = lcurl.easy_init()
        if not curl:
            print("libcurl.easy_init() failed", file=sys.stderr)
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break

        test_setopt(curl, lcurl.CURLOPT_URL, b"%s/folderA/661" % URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_IGNORE_CONTENT_LENGTH, 1)
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_NOCWD)
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_REMOTE_FILE_NOT_FOUND: raise guard.Break

        # curve ball: CWD /folderB before reusing connection with _NOCWD

        test_setopt(curl, lcurl.CURLOPT_URL, b"%s/folderB/661" % URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_SINGLECWD)
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_REMOTE_FILE_NOT_FOUND: raise guard.Break

        test_setopt(curl, lcurl.CURLOPT_URL, b"%s/folderA/661" % URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_NOCWD)
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_REMOTE_FILE_NOT_FOUND: raise guard.Break

        # test: libcurl.CURLFTPMETHOD_NOCWD with home-relative path should
        #       not emit CWD for first FTP access after login
        lcurl.easy_cleanup(curl)
        curl = lcurl.easy_init()
        if not curl:
            print("libcurl.easy_init() failed", file=sys.stderr)
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break

        slist: ct.POINTER(lcurl.slist) = lcurl.slist_append(None, b"SYST")
        if not slist:
            print("libcurl.slist_append() failed", file=sys.stderr)
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break
        guard.add_slist(slist)

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_NOBODY, 1)
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_NOCWD)
        test_setopt(curl, lcurl.CURLOPT_QUOTE, slist)
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        # test: libcurl.CURLFTPMETHOD_SINGLECWD with home-relative path should
        #       not emit CWD for first FTP access after login
        lcurl.easy_cleanup(curl)
        curl = lcurl.easy_init()
        if not curl:
            print("libcurl.easy_init() failed", file=sys.stderr)
            res = TEST_ERR_MAJOR_BAD
            raise guard.Break

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_NOBODY, 1)
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_SINGLECWD)
        test_setopt(curl, lcurl.CURLOPT_QUOTE, slist)
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

        # test: libcurl.CURLFTPMETHOD_NOCWD with home-relative path should
        #       not emit CWD for second FTP access when not needed +
        #       bonus: see if path buffering survives curl_easy_reset()
        lcurl.easy_reset(curl)
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        test_setopt(curl, lcurl.CURLOPT_NOBODY, 1)
        test_setopt(curl, lcurl.CURLOPT_FTP_FILEMETHOD, lcurl.CURLFTPMETHOD_NOCWD)
        test_setopt(curl, lcurl.CURLOPT_QUOTE, slist)
        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    if res:
        print("test encountered error %d" % res, file=sys.stderr)

    return res
