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
HTTP/2 server push. Receive all data in memory.
"""

from dataclasses import dataclass
import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa
from debug import debug_function


MAX_FILES = 10


@dataclass
class debug_config:
    trace_ascii: bool = False


class MemoryStruct(ct.Structure):
    _fields_ = [
    ("memory", ct.c_void_p),
    ("size",   ct.c_size_t),
]

def init_memory(chunk: MemoryStruct):
    chunk.memory = libc.malloc(1)  # grown as needed with realloc
    chunk.size   = 0               # no data at this point


files = (MemoryStruct * MAX_FILES)()
push_index = 1


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


@lcurl.push_callback
def server_push_callback(parent, easy, num_headers, headers, userp):
    # called when there's an incoming push
    global MAX_FILES, files, push_index

    transfersp = ct.cast(userp, ct.POINTER(ct.c_int))

    if push_index == MAX_FILES:
        # cannot fit anymore
        return lcurl.CURL_PUSH_DENY

    # write to this buffer
    init_memory(files[push_index])
    lcurl.easy_setopt(easy, lcurl.CURLOPT_WRITEDATA, ct.byref(files[push_index]))
    push_index += 1

    headp = lcurl.pushheader_byname(headers, b":path")
    if headp:
        print("* Pushed :path '%s'", headp.encode("utf-8"),  # skip :path + colon
              file=sys.stderr)

    transfersp.contents += 1  # one more

    return lcurl.CURL_PUSH_OK


def setup(curl: ct.POINTER(lcurl.CURL), config: debug_config, url: str) -> int:
    global files

    # set the URL
    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    # HTTP/2 please
    lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION,
                            lcurl.CURL_HTTP_VERSION_2_0)
    # we use a self-signed test server, skip verification during debugging
    lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
    # write data to a struct
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
    init_memory(files[0])
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(files[0]))
    # please be verbose
    lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_function)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, id(config))
    # wait for pipe connection to confirm
    lcurl.easy_setopt(curl, lcurl.CURLOPT_PIPEWAIT, 1)

    return 0  # all is good


#
# Download a file over HTTP/2, take care of server push.
#

def main(argv=sys.argv[1:]):

    url: str = (argv[0] if len(argv) >= 1 else
                "https://localhost:8443/index.html")

    global files, push_index

    config = debug_config(True)  # enable ascii tracing

    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    curl:  ct.POINTER(lcurl.CURL)  = lcurl.easy_init()

    with curl_guard(False, None, mcurl):
        if not curl: return 1

        # set options
        res = setup(curl, config, url)
        if res:
            print("failed", file=sys.stderr)
            return res

        # add the easy transfer
        lcurl.multi_add_handle(mcurl, curl)

        transfers = ct.c_int(1)  # we start with one
        lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_PIPELINING,
                                  lcurl.CURLPIPE_MULTIPLEX)
        lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_PUSHFUNCTION,
                                  server_push_callback)
        lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_PUSHDATA,
                                  ct.byref(transfers))

        while transfers.value:  # as long as we have transfers going
            still_running = ct.c_int(0)  # keep number of running handles
            mcode: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            if mcode:
                break

            rc = ct.c_int(0)
            mcode = lcurl.multi_wait(mcurl, None, 0, 1000, ct.byref(rc))
            if mcode:
                break

            # When doing server push, libcurl itself created and added one or
            # more easy handles but *we* need to clean them up when they are
            # done.
            while True:
                queued = ct.c_int(0)
                msg: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(mcurl,
                                                                       ct.byref(queued))
                if not msg: break
                msg = msg.contents

                if msg.msg == lcurl.CURLMSG_DONE:
                    transfers.value -= 1
                    lcurl.multi_remove_handle(mcurl, msg.easy_handle)
                    lcurl.easy_cleanup(msg.easy_handle)

        # 'push_index' is now the number of received transfers
        for i in range(push_index):
            # do something fun with the data, and then free it when done
            libc.free(files[i].memory)

    return 0


sys.exit(main())
