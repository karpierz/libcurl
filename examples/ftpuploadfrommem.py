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
FTP upload a file from memory
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


# Silly test data to upload
text: str = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Nam rhoncus odio id venenatis volutpat. Vestibulum dapibus "
    "bibendum ullamcorper. Maecenas finibus elit augue, vel "
    "condimentum odio maximus nec. In hac habitasse platea dictumst. "
    "Vestibulum vel dolor et turpis rutrum finibus ac at nulla. "
    "Vivamus nec neque ac elit blandit pretium vitae maximus ipsum. "
    "Quisque sodales magna vel erat auctor, sed pellentesque nisi "
    "rhoncus. Donec vehicula maximus pretium. Aliquam eu tincidunt "
    "lorem."
)

data: bytes = text.encode("utf-8")


class WriteThis(ct.Structure):
    _fields_ = [
    ("readptr",  ct.c_char_p),
    ("sizeleft", ct.c_size_t),
]


@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    upload = ct.cast(stream, ct.POINTER(WriteThis)).contents
    buffer_size = size * nitems
    if upload.sizeleft == 0 or buffer_size == 0:
        return 0  # no more data left to deliver
    # copy as much as possible from the source to the destination
    copy_this_much = min(upload.sizeleft, buffer_size)
    ct.memmove(buffer, upload.readptr, copy_this_much)
    upload.readptr = c_ptr_add(ct.c_char_p(upload.readptr), copy_this_much)
    #upload.readptr = upload.readptr[copy_this_much:]
    upload.sizeleft -= copy_this_much
    return copy_this_much  # we copied this many bytes


def main(argv=sys.argv[1:]):

    url: str = (argv[0] if len(argv) >= 1 else
                "ftp://example.com/path/to/upload/file")

    upload = WriteThis(data, len(data))

    # In windows, this will init the winsock stuff
    res: lcurl.CURLcode = lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        # Check for errors
        if res != lcurl.CURLE_OK: return 1
        if not curl: return 1

        # First set the URL, the target file
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # User and password for the FTP login
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERPWD, b"login:secret")
        # Now specify we want to UPLOAD data
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        # we want to use our own read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        # pointer to pass to our read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(upload))
        # get verbose debug output please
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # Set the expected upload size.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE,
                          lcurl.off_t(upload.sizeleft).value)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
