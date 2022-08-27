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
HTTP/2 server push
"""

from dataclasses import dataclass
import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa
from debug import debug_function

here = Path(__file__).resolve().parent


OUT_DIR  = here/"output"
OUT_FILE = OUT_DIR/"dl"


@dataclass
class debug_config:
    trace_ascii: bool = False
    outstream: object = None


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    config = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = config.outstream.write(bwritten)
    return nwritten


count = 0

@lcurl.push_callback
def server_push_callback(parent, easy, num_headers, headers, userp):
    # called when there's an incoming push

    transfersp = ct.cast(userp, ct.POINTER(ct.c_int))

    global OUT_DIR, count

    file_path = OUT_DIR/("push%u" % count)
    count += 1

    # here's a new stream, save it in a new file for each new push
    try:
        #FILE *out;
        out = file_path.open("wb")
    except:
        # if we cannot save it, deny it
        print("Failed to create output file for push", file=sys.stderr)
        return lcurl.CURL_PUSH_DENY

    # write to this file
    #!!!curl_easy_setopt(easy, CURLOPT_WRITEDATA, out)

    print("**** push callback approves stream %u, got %u headers!" %
          (count, num_headers), file=sys.stderr)

    for i in range(num_headers):
        headp = lcurl.pushheader_bynum(headers, i)
        print("**** header %u: %s" % (i, headp.encode("utf-8")),
              file=sys.stderr)

    headp = lcurl.pushheader_byname(headers, b":path")
    if headp:
        print("**** The PATH is %s" % headp.encode("utf-8"),  # skip :path + colon
              file=sys.stderr)

    transfersp.contents += 1  # one more

    return lcurl.CURL_PUSH_OK


def setup(curl: ct.POINTER(lcurl.CURL), config: debug_config, url: str) -> int:

    global OUT_FILE

    try:
        config.outstream = OUT_FILE.open("wb")
    except OSError as exc:
        config.outstream = None
        print("error: could not open file %s for writing: %s" %
              (OUT_FILE, os.strerror(exc.errno)), file=sys.stderr)
        return 1  # failed

    # set the URL
    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    # send all data to this function 
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
    # write to this file
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(config))
    # please be verbose
    lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_function)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, id(config))
    # HTTP/2 please
    lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION,
                            lcurl.CURL_HTTP_VERSION_2_0)
    # we use a self-signed test server, skip verification during debugging
    lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
    if lcurl.CURLPIPE_MULTIPLEX > 0:
        # wait for pipe connection to confirm
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PIPEWAIT, 1)

    return 0  # all is good


#
# Download a file over HTTP/2, take care of server push.
#

def main(argv=sys.argv[1:]):

    url: str = (argv[0] if len(argv) >= 1 else
                "https://localhost:8443/index.html")

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

        still_running = ct.c_int(1)  # keep number of running handles
        while transfers.value:  # as long as we have transfers going
            mcode: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            if still_running.value:
                # wait for activity, timeout or "nothing"
                mcode = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mcode:
                break

            # A little caution when doing server push is that libcurl itself
            # has created and added one or more easy handles but we need to
            # clean them up when we are done.
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

    return 0


sys.exit(main())
