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

import os
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# This example shows an FTP upload, with a rename of the file just after
# a successful upload.
#
# Example based on source code provided by Erick Nuwendam. Thanks!


@curl_test_decorator
def test(URL: str, filename: str = None) -> lcurl.CURLcode:
    if filename: filename = str(filename)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    buf_1 = b"RNFR 505"
    buf_2 = b"RNTO 505-forreal"

    if not filename:
        print("Usage: <url> <file-to-upload>", file=sys.stderr)
        return TEST_ERR_USAGE

    try:
        hd_src = open(filename, "rb")
    except OSError as exc:
        print("fopen failed with error: %d %s" %
              (exc.errno, exc.strerror), file=sys.stderr)
        print("Error opening file: %s" % filename, file=sys.stderr)
        return TEST_ERR_MAJOR_BAD  # if this happens things are major weird

    with hd_src:

        # get the file size of the local file
        try:
            file_len: int = file_size(hd_src)
        except OSError as exc:
            # can't open file, bail out
            print("fstat() failed with error: %d %s" %
                  (exc.errno, exc.strerror), file=sys.stderr)
            print("ERROR: cannot open file %s" % filename, file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        if file_len == 0:
            print("ERROR: file %s has zero size!" % filename, file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
            return TEST_ERR_MAJOR_BAD

        # get a curl handle
        curl: ct.POINTER(lcurl.CURL) = easy_init()

        with curl_guard(True, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            # build a list of commands to pass to libcurl

            hl: ct.POINTER(lcurl.slist) = lcurl.slist_append(None, buf_1)
            if not hl:
                print("libcurl.slist_append() failed", file=sys.stderr)
                return TEST_ERR_MAJOR_BAD
            headerlist: ct.POINTER(lcurl.slist) = lcurl.slist_append(hl, buf_2)
            if not headerlist:
                print("libcurl.slist_append() failed", file=sys.stderr)
                lcurl.slist_free_all(hl)
                return TEST_ERR_MAJOR_BAD
            headerlist = hl

            # specify target
            test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            # enable uploading
            test_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
            # enable verbose
            test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            # pass in that last of FTP commands to run after the transfer
            test_setopt(curl, lcurl.CURLOPT_POSTQUOTE, headerlist)
            # we want to use our own read function
            test_setopt(curl, lcurl.CURLOPT_READFUNCTION, lcurl.read_from_file)
            # now specify which file to upload
            test_setopt(curl, lcurl.CURLOPT_READDATA, id(hd_src))
            # and give the size of the upload (optional)
            test_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, file_len)

            # Now run off and do what you've been told!
            res = lcurl.easy_perform(curl)

            # test_cleanup:

            # clean up the FTP commands list
            lcurl.slist_free_all(headerlist)

    return res
