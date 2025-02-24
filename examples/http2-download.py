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
Multiplexed HTTP/2 downloads over a single connection
"""

import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curl_utils import *  # noqa
from debug import debug_output

here = Path(__file__).resolve().parent

NUM_HANDLES = 1000
OUT_DIR = here/"output"


class transfer_data(ct.Structure):
    _fields_ = [
    ("curl", ct.POINTER(lcurl.CURL)),
    ("num",  ct.c_uint),
    ("outstream", ct.py_object),
]


@lcurl.write_callback
def write_function(buffer, size, nitems, userp):
    transfer = ct.cast(userp, ct.POINTER(transfer_data)).contents
    buffer_size = nitems * size
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = transfer.outstream.write(bwritten)
    return nwritten


@lcurl.debug_callback
def debug_function(curl, info_type, data, size, userptr):
    transfer = ct.cast(userptr, ct.POINTER(transfer_data)).contents
    debug_output(info_type, transfer.num, data, size, True, sys.stderr)
    return 0


def setup(transfer: transfer_data, num: int, url: str) -> int:

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    transfer.curl = curl
    transfer.num  = num

    file_path = OUT_DIR/("dl-%d" % num)

    try:
        transfer.outstream = file_path.open("wb")
    except OSError as exc:
        print("error: could not open file %s for writing: %s" %
              (file_path, exc.strerror), file=sys.stderr)
        return 1

    # send all data to this function
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
    # write to this file
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(transfer))
    # set the URL
    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    # please be verbose
    lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_function)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(transfer))
    # enlarge the receive buffer for potentially higher transfer speeds
    lcurl.easy_setopt(curl, lcurl.CURLOPT_BUFFERSIZE, 100000)
    # HTTP/2 please
    lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION,
                            lcurl.CURL_HTTP_VERSION_2_0)
    if lcurl.CURLPIPE_MULTIPLEX > 0:
        # wait for pipe connection to confirm
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PIPEWAIT, 1)

    return 0  # all is good


#
# Download many transfers over HTTP/2, using the same connection!
#

def main(argv=sys.argv[1:]):

    global NUM_HANDLES

    num_transfers = 3  # suitable default
    url = "https://localhost:8443/index.html"
    if len(argv) >= 1:
        # if given a number, do that many transfers
        num_transfers = int(argv[0])
        if not (1 <= num_transfers <= NUM_HANDLES):
            num_transfers = 3  # a suitable low default
    if len(argv) >= 2:
        url = argv[1]

    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    with curl_guard(False, None, mcurl) as guard:
        if not mcurl: return 2

        transfers = []
        for num in range(num_transfers):
            transfer = transfer_data()
            res = setup(transfer, num, url)
            if res:
                return res
            # add the individual transfer
            lcurl.multi_add_handle(mcurl, transfer.curl)
            transfers.append(transfer)

        lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_PIPELINING,
                                  lcurl.CURLPIPE_MULTIPLEX)

        still_running = ct.c_int(1)  # keep number of running handles
        while still_running.value:

            mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            # wait for activity, timeout or "nothing"
            if still_running.value: mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mc:
                break

        for transfer in transfers:
            lcurl.multi_remove_handle(mcurl, transfer.curl)
            lcurl.easy_cleanup(transfer.curl)

    return 0


sys.exit(main())
