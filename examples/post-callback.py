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
Issue an HTTP POST and provide the data through the read callback.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa

# USE_CHUNKED    = 1
# DISABLE_EXPECT = 1


# Silly test data to POST
text: str = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vel "
    "urna neque. Ut quis leo metus. Quisque eleifend, ex at laoreet "
    "rhoncus, odio ipsum semper metus, at tempus ante urna in mauris. "
    "Suspendisse ornare tempor venenatis. Ut dui neque, pellentesque "
    "a varius eget, mattis vitae ligula. Fusce ut pharetra est. Ut "
    "ullamcorper mi ac sollicitudin semper. Praesent sit amet tellus "
    "varius, posuere nulla non, rhoncus ipsum."
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

    url: str = argv[0] if len(argv) >= 1 else "https://example.com/index.cgi"

    upload = WriteThis(data, len(data))

    res: lcurl.CURLcode = lcurl.CURLE_OK

    # In windows, this will init the winsock stuff
    res = lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    # Check for errors
    if res != lcurl.CURLE_OK:
        handle_global_init_error(res)
        return 1
    # get a curl handle
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        # First set the URL that is about to receive our POST.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # Now specify we want to POST data
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POST, 1)
        # we want to use our own read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        # pointer to pass to our read function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(upload))
        # get verbose debug output please
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # If you use POST to a HTTP 1.1 server, you can send data without knowing
        # the size before starting the POST if you use chunked encoding. You
        # enable this by adding a header like "Transfer-Encoding: chunked" with
        # CURLOPT_HTTPHEADER. With HTTP 1.0 or without chunked transfer, you must
        # specify the size in the request.
        if defined("USE_CHUNKED"):
            chunk = ct.POINTER(lcurl.slist)()
            chunk = lcurl.slist_append(chunk, b"Transfer-Encoding: chunked")
            res = lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, chunk)
            # use curl_slist_free_all() after the *perform() call to free this
            # list again
        else:
            # Set the expected POST size. If you want to POST large amounts of data,
            # consider CURLOPT_POSTFIELDSIZE_LARGE
            lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, upload.sizeleft)
        if defined("DISABLE_EXPECT"):
            # Using POST with HTTP 1.1 implies the use of a "Expect: 100-continue"
            # header.  You can disable this header with CURLOPT_HTTPHEADER as usual.
            # NOTE: if you want chunked transfer too, you need to combine these two
            # since you can only set one list of headers with CURLOPT_HTTPHEADER.
            #
            # A less good option would be to enforce HTTP 1.0, but that might also
            # have other implications.
            chunk = ct.POINTER(lcurl.slist)()
            chunk = lcurl.slist_append(chunk, b"Expect:")
            res = lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, chunk)
            # use curl_slist_free_all() after the *perform() call to free
            # this list again

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
