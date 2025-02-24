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
Multiplexed HTTP/2 uploads over a single connection
"""

from typing import Optional
import sys
import ctypes as ct
from pathlib import Path
import time

import libcurl as lcurl
from curl_utils import *  # noqa
from debug import dump

here = Path(__file__).resolve().parent

NUM_HANDLES = 1000
OUT_DIR = here/"output"


class transfer_data(ct.Structure):
    _fields_ = [
    ("curl", ct.POINTER(lcurl.CURL)),
    ("num",  ct.c_uint),
    ("instream",   ct.py_object),
    ("bytes_read", ct.c_size_t),  # count up
    ("outstream",  ct.py_object),
]


@lcurl.write_callback
def write_function(buffer, size, nitems, userp):
    transfer = ct.cast(userp, ct.POINTER(transfer_data)).contents
    buffer_size = nitems * size
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = transfer.outstream.write(bwritten)
    return nwritten


@lcurl.read_callback
def read_function(buffer, size, nitems, userp):
    transfer = ct.cast(userp, ct.POINTER(transfer_data)).contents
    buffer_size = nitems * size
    bread = transfer.instream.read(buffer_size)
    if not bread: return 0
    nread = len(bread)
    ct.memmove(buffer, bread, nread)
    transfer.bytes_read += nread
    return nread


@lcurl.debug_callback
def debug_function(curl, info_type, data, size, userptr):
    transfer = ct.cast(userptr, ct.POINTER(transfer_data)).contents
    debug_output(info_type, transfer.num, data, size, True, sys.stderr)
    return 0


_known_offset = False
_epoch_offset = 0

def debug_output(info_type, num: Optional[int],
                 data: ct.POINTER(ct.c_ubyte), size: int, no_hex: bool, stream):
    global _known_offset, _epoch_offset

    if info_type == lcurl.CURLINFO_TEXT:
        nanosecs = time.monotonic_ns()
        tv = lcurl.timeval(tv_sec =(nanosecs // 1_000_000_000),
                           tv_usec=(nanosecs %  1_000_000_000) // 1000)
        if not _known_offset:
            _epoch_offset = int(time.time()) - tv.tv_sec
            _known_offset = True
        secs: time_t = _epoch_offset + tv.tv_sec
        now: time.struct_time = time.localtime(secs)
        curr_time = "%02d:%02d:%02d.%06ld" % (
                    now.tm_hour, now.tm_min, now.tm_sec, tv.tv_usec)

        if num is None:
            print("%s Info: %s" %
                  (curr_time, bytes(data[:size]).decode("utf-8")),
                  end="", file=stream)
        else:
            print("%s [%d] Info: %s" %
                  (curr_time, num, bytes(data[:size]).decode("utf-8")),
                  end="", file=stream)
    else:
        if   info_type == lcurl.CURLINFO_HEADER_OUT:   text = "=> Send header"
        elif info_type == lcurl.CURLINFO_DATA_OUT:     text = "=> Send data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_OUT: text = "=> Send SSL data"
        elif info_type == lcurl.CURLINFO_HEADER_IN:    text = "<= Recv header"
        elif info_type == lcurl.CURLINFO_DATA_IN:      text = "<= Recv data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_IN:  text = "<= Recv SSL data"
        else: return 0  # in case a new one is introduced to shock us
        dump(num, text, data, size, no_hex, stream)

    return 0


def setup(transfer: transfer_data, num: int, upload_fpath: Path, url: str) -> int:

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    transfer.curl = curl
    transfer.num  = num

    try:
        transfer.instream = upload_fpath.open("rb")
    except OSError as exc:
        print("error: could not open file %s for reading: %s" %
              (upload_fpath, exc.strerror), file=sys.stderr)
        return 1

    # get the file size of the local file
    try:
        upload_size = file_size(transfer.instream)
    except OSError as exc:
        print("error: could not stat file %s: %s" %
              (upload_fpath, exc.strerror), file=sys.stderr)
        return 1

    file_path = OUT_DIR/("dl-%d" % num)

    try:
        transfer.outstream = file_path.open("wb")
    except OSError as exc:
        print("error: could not open file %s for writing: %s" %
              (file_path, exc.strerror), file=sys.stderr)
        return 1

    url += "/upload-%d" % num

    # send all data to this function
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
    # write to this file
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(transfer))
    # we want to use our own read function
    lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
    # read from this file
    lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, ct.byref(transfer))
    # provide the size of the upload
    lcurl.easy_setopt(curl, lcurl.CURLOPT_INFILESIZE_LARGE, upload_size)
    # send in the URL to store the upload as
    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    # upload please
    lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
    # please be verbose
    lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_function)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGDATA, ct.byref(transfer))
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
# Upload all files over HTTP/2, using the same physical connection!
#

def main(argv=sys.argv[1:]):

    global NUM_HANDLES

    num_transfers = 3  # suitable default
    fpath = here/"input/index.html"
    url = "https://localhost:8443"
    if len(argv) >= 1:
        # if given a number, do that many transfers
        num_transfers = int(argv[0])
        if not (1 <= num_transfers <= NUM_HANDLES):
            num_transfers = 3  # a suitable low default
    if len(argv) >= 2:
        # if given a file name, upload this!
        fpath = Path(argv[1])
    if len(argv) >= 3:
        url = argv[2]

    # init a multi stack
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    with curl_guard(False, None, mcurl) as guard:
        if not mcurl: return 2

        transfers = []
        for num in range(num_transfers):
            transfer = transfer_data()
            res = setup(transfer, num, fpath, url)
            if res:
                return res
            # add the individual transfer
            lcurl.multi_add_handle(mcurl, transfer.curl)
            transfers.append(transfer)

        lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_PIPELINING,
                                  lcurl.CURLPIPE_MULTIPLEX)
        # We do HTTP/2 so let's stick to one connection per host
        lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_MAX_HOST_CONNECTIONS, 1)

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
