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
def test(URL: str, filename: str = None) -> lcurl.CURLcode:
    if filename: filename = str(filename)

    res: lcurl.CURLcode = lcurl.CURLE_OK

    start_test_timing()

    if not filename:
        if defined("LIB529"):
            # test 529
            print("Usage: lib529 [url] [uploadfile]", file=sys.stderr)
        else:
            # test 525
            print("Usage: lib525 [url] [uploadfile]", file=sys.stderr)
        return TEST_ERR_USAGE

    try:
        hd_src = open(filename, "rb")
    except OSError as exc:
        print("fopen failed with error: %d (%s)" %
              (exc.errno, exc.strerror), file=sys.stderr)
        print("Error opening file: (%s)" % filename,
              file=sys.stderr)
        return TEST_ERR_FOPEN

    with hd_src:

        try:
            file_len: int = file_size(hd_src)
        except OSError as exc:
            # can't open file, bail out
            print("fstat() failed with error: %d (%s)" %
                  (exc.errno, exc.strerror), file=sys.stderr)
            print("ERROR: cannot open file (%s)" % filename,
                  file=sys.stderr)
            return TEST_ERR_FSTAT

        res = res_global_init(lcurl.CURL_GLOBAL_ALL)
        if res: return res
        curl:  ct.POINTER(lcurl.CURL)  = easy_init()
        multi: ct.POINTER(lcurl.CURLM) = multi_init()

        # specify target
        easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # enable uploading
        easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # go verbose
        easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # use active FTP
        easy_setopt(curl, lcurl.CURLOPT_FTPPORT, b"-")
        # we want to use our own read function
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, lcurl.read_from_file)
        # now specify which file to upload
        easy_setopt(curl, lcurl.CURLOPT_READDATA, id(hd_src))
        # NOTE: if you want this code to work on Windows with libcurl as a DLL, you
        # MUST also provide a read callback with libcurl.CURLOPT_READFUNCTION. Failing to
        # do so will give you a crash since a DLL may not use the variable's memory
        # when passed in to it from an app like this.

        # Set the size of the file to upload (optional).  If you give a *_LARGE
        # option you MUST make sure that the type of the passed-in argument is a
        # lcurl.off_t. If you use libcurl.CURLOPT_INFILESIZE (without _LARGE)
        # you must make sure that to pass in a type 'long' argument.
        easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, file_len)

        multi_add_handle(multi, curl)

        still_running = ct.c_int()
        while True:
            multi_perform(multi, ct.byref(still_running))

            abort_on_test_timeout()

            if not still_running.value:
                break  # done

            fd_read  = lcurl.fd_set()
            fd_write = lcurl.fd_set()
            fd_excep = lcurl.fd_set()

            max_fd = ct.c_int(-99)
            multi_fdset(multi,
                        ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                        ct.byref(max_fd))
            max_fd = max_fd.value

            # At this point, max_fd is guaranteed to be greater or equal than -1.

            timeout = lcurl.timeval(tv_sec=1, tv_usec=0)  # 1 sec
            res = select_test(max_fd + 1,
                              ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                              ct.byref(timeout))

            abort_on_test_timeout()

    return res
