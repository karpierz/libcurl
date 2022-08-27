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
Make a HTTP POST with data from memory and receive response in memory.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


class MemoryStruct(ct.Structure):
    _fields_ = [
    ("memory", ct.c_void_p),
    ("size",   ct.c_size_t),
]

def init_memory(chunk: MemoryStruct):
    chunk.memory = libc.malloc(1)  # grown as needed with realloc
    chunk.size   = 0               # no data at this point


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    chunk = ct.cast(stream, ct.POINTER(MemoryStruct)).contents
    buffer_size = size * nitems

    memory = libc.realloc(chunk.memory, chunk.size + buffer_size + 1)
    if not memory:
        # out of memory!
        print("not enough memory (realloc returned NULL)")
        return 0

    chunk.memory = memory
    ct.memmove(chunk.memory + chunk.size, buffer, buffer_size)
    chunk.size += buffer_size
    ct.memset(chunk.memory + chunk.size, 0, 1)
    return buffer_size


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.org/"

    chunk = MemoryStruct()
    init_memory(chunk)

    post_this = b"Field=1&Field=2&Field=3"

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # init the curl session
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl:
            libc.free(chunk.memory)
            return 1

        # specify URL
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # send all data to this function 
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        # we pass our 'chunk' struct to the callback function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(chunk))
        # some servers do not like requests that are made without a user-agent
        # field, so we provide one
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"libcurl-agent/1.0")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDS, post_this)
        # if we do not provide POSTFIELDSIZE, libcurl will len() by itself
        lcurl.easy_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, len(post_this))

        # Perform the request, res will get the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)
        else:
            # Now, our chunk.memory points to a memory block that is chunk.size
            # bytes big and contains the remote file.
            #
            # Do something nice with it!
            print("%s" % ct.cast(chunk.memory, ct.c_char_p).value.decode("utf-8"))

    # Cleanup
    libc.free(chunk.memory)

    return 0


sys.exit(main())
