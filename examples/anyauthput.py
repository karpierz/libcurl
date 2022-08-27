#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 1998 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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
#***************************************************************************

"""
HTTP PUT upload with authentication using "any" method. libcurl picks the
one the server supports/wants.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 12, 3):
    print("This example requires curl 7.12.3 or later", file=sys.stderr)
    sys.exit(-1)


# This example shows a HTTP PUT operation with authentication using "any"
# type. It PUTs a file given as a command line argument to the URL also
# given on the command line.
#
# Since libcurl 7.12.3, using "any" auth and POST/PUT requires a set ioctl
# function.
#
# This example also uses its own read callback.

@lcurl.ioctl_callback
def ioctl_function(handle, cmd, clientp):
    # ioctl callback function
    fd: int = int(clientp)
    if cmd != lcurl.CURLIOCMD_RESTARTREAD:
        # ignore unknown commands
        return lcurl.CURLIOE_UNKNOWNCMD
    # libcurl kindly asks as to rewind the read data stream to start
    try:
        pos = os.lseek(fd, 0, os.SEEK_SET)
    except:
        # couldn't rewind
        return lcurl.CURLIOE_FAILRESTART
    if pos != 0:
        # improper rewind
        return lcurl.CURLIOE_FAILRESTART
    return lcurl.CURLIOE_OK  # success!


@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    # read callback function
    fd: int = int(stream)
    bread = os.read(fd, size * nitems)
    if not bread: return 0
    nread = len(bread)
    print("*** We read %u bytes from file" % nread, file=sys.stderr)
    ct.memmove(buffer, bread, nread)
    return nread


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 2:
        print("Usage: %s <filename> <URL>" % app_name)
        return 1

    fname: str = argv[0]
    url:   str = argv[1]

    # get the file size of the local file
    fd: int = os.open(fname, os.O_RDONLY)

    # get the file size
    try:
        fsize: int = os.fstat(fd).st_size
    except:
        os.close(fd)
        return 1  # cannot continue

    # In windows, this will init the winsock stuff
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl:
            # Close the local file
            os.close(fd)
            return 1

        # we want to use our own read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        # which file to upload
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, fd)
        # set the ioctl function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_IOCTLFUNCTION, ioctl_function)
        # pass the file descriptor to the ioctl callback as well
        lcurl.easy_setopt(curl, lcurl.CURLOPT_IOCTLDATA, fd)
        # enable "uploading" (which means PUT when doing HTTP)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # specify target URL, and note that this URL should also include a file
        # name, not only a directory (as you can do with GTP uploads)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # and give the size of the upload, this supports large file sizes
        # on systems that have general support for it
        lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, fsize)
        # tell libcurl we can use "any" auth, which lets the lib pick one, but
        # it also costs one extra round-trip and possibly sending of all the PUT
        # data twice!!!
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPAUTH, lcurl.CURLAUTH_ANY)
        # set user name and password for the authentication
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERPWD, b"user:password")

        # Now run off and do what you have been told!
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    # Close the local file
    os.close(fd)

    return 0


sys.exit(main())
