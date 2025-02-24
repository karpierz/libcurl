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
HTTP PUT upload with authentication using "any" method. libcurl picks the
one the server supports/wants.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 12, 3):
    print("This example requires curl 7.12.3 or later", file=sys.stderr)
    sys.exit(-1)

# This example shows an HTTP PUT operation with authentication using "any"
# type. It PUTs a file given as a command line argument to the URL also given
# on the command line.
#
# Since libcurl 7.12.3, using "any" auth and POST/PUT requires a set seek
# function.
#
# This example also uses its own read callback.


@lcurl.seek_callback
def seek_function(instream, offset, origin):
    # seek callback function
    file = lcurl.from_oid(instream)
    try:
        file.seek(offset, origin)
    except:
        # could not seek
        return lcurl.CURL_SEEKFUNC_CANTSEEK
    return lcurl.CURL_SEEKFUNC_OK  # success!


@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    # read callback function
    nread = lcurl.read_from_file(buffer, size, nitems, stream)
    if nread > 0:
        print("*** We read %d bytes from file" % nread, file=sys.stderr)
    return nread


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 2:
        print("Usage: python %s <filename> <URL> [user_login]" % app_name)
        return 1

    fname: str      = argv[0]
    url: str        = argv[1]
    user_login: str = argv[2] if len(argv) >= 3 else "user:password"

    # open the local file
    try:
        local_file = fname.open("rb")
    except OSError as exc:
        print("Couldn't open '%s': %s" % (fname, exc.strerror))
        return 2  # cannot continue

    # get the file size of the local file
    try:
        fsize: int = file_size(local_file)
    except:
        local_file.close()
        return 1  # cannot continue

    # In Windows, this inits the Winsock stuff
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with local_file, curl_guard(True, curl) as guard:
        if not curl: return 1

        # we want to use our own read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        # which file to upload
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, id(local_file))
        # set the seek function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SEEKFUNCTION, seek_function)
        # pass the file descriptor to the seek callback as well
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SEEKDATA, id(local_file))
        # enable "uploading" (which means PUT when doing HTTP)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # specify target URL, and note that this URL should also include a file
        # name, not only a directory (as you can do with GTP uploads)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # and give the size of the upload, this supports large file sizes
        # on systems that have general support for it
        lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, fsize)
        # tell libcurl we can use "any" auth, which lets the lib pick one, but it
        # also costs one extra round-trip and possibly sending of all the PUT
        # data twice!!!
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPAUTH, lcurl.CURLAUTH_ANY)
        # set user name and password for the authentication
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERPWD,
                                user_login.encode("utf-8") if user_login else None)

        # Now run off and do what you have been told!
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        handle_easy_perform_error(res)

    return int(res)


sys.exit(main())
