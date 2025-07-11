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

"""
HTTP PUT with easy interface and read callback
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


# This example shows an HTTP PUT operation. PUTs a file given as a
# command line argument to the URL also given on the command line.
#
# This example also uses its own read callback.
#
# Here's an article on how to setup a PUT handler for Apache:
# http://www.apacheweek.com/features/put


@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    nread = lcurl.read_from_file(buffer, size, nitems, stream)
    print("*** We read %d bytes from file" % nread, file=sys.stderr)
    return nread


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 2:
        print("Usage: python %s <filename> <URL>" % app_name)
        return 1

    fname: str = argv[0]
    url:   str = argv[1]

    try:
        hd_src = open(fname, "rb")
    except:
        return 2

    # get the file size of the local file
    try:
        fsize: int = file_size(hd_src)
    except:
        hd_src.close()
        return 1  # cannot continue

    # In Windows, this inits the Winsock stuff
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    # get a FILE * of the same file, could also be made with
    # fdopen() from the previous descriptor, but hey this is just
    # an example!
    with hd_src, curl_guard(True, curl) as guard:
        if not curl: return 1

        # we want to use our own read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        # enable uploading (implies PUT over HTTP)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # specify target URL, and note that this URL should include
        # a file name, not only a directory
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # now specify which file to upload
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, id(hd_src))
        # provide the size of the upload, we typecast the value to curl_off_t
        # since we must be sure to use the correct data size
        lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, fsize)

        # Now run off and do what you have been told!
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


if __name__ == "__main__":
    sys.exit(main())
