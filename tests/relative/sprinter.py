# **************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 2021, Daniel Stenberg, <daniel@haxx.se>, et al.
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
# **************************************************************************

from typing import List
import sys
import ctypes as ct
from datetime import datetime, timedelta

import libcurl as lcurl
from libcurl._platform import defined

if not lcurl.CURL_AT_LEAST_VERSION(7, 28, 0):
    print("This code needs libcurl 7.28.0 or later", file=sys.stderr)
    sys.exit(-1)

SPRINTER_VERSION = "0.1"

MAXPARALLEL = 500    # max parallelism
NPARALLEL   = 100    # Default number of concurrent transfers
NTOTAL      = 10000  #  # Default number of transfers in total
RESPCODE    = 200    # Default expected response code from server


downloaded = 0

@lcurl.write_callback
def write_callback(buffer, size, nitems, stream):
    # ignore the data here
    global downloaded
    buffer_size = nitems * size
    downloaded += buffer_size
    return buffer_size


def main(argv=sys.argv[1:]):
    """ """
    global downloaded

    if len(argv) < 1:
        print("curl sprinter version %s\n"
              "Usage: sprinter <URL> [total] [parallel] [respcode]\n"
              " <URL> will be downloaded\n"
              " [total] number of times (default %d) using\n"
              " [parallel] simultaneous transfers (default %d)\n"
              " [respcode] expected response code from server (default %d)" %
              (SPRINTER_VERSION, NTOTAL, NPARALLEL, RESPCODE))
        return 1

    URL: str          = argv[0]
    ntotal            = int(argv[1])     if len(argv) > 1 else NTOTAL
    nparallel         = min(int(argv[2]) if len(argv) > 2 else NPARALLEL, ntotal, MAXPARALLEL)
    expected_respcode = int(argv[3])     if len(argv) > 3 else RESPCODE

    version_info = lcurl.version_info(lcurl.CURLVERSION_NOW).contents

    downloaded = 0
    total = add = ntotal

    # Allocate one libcurl.CURL handle per transfer
    handles: List[ct.POINTER(lcurl.CURL)] = []
    for _ in range(nparallel):
        handle = lcurl.easy_init()
        handles.append(handle)
        lcurl.easy_setopt(handle, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        lcurl.easy_setopt(handle, lcurl.CURLOPT_WRITEFUNCTION,  write_callback)
        lcurl.easy_setopt(handle, lcurl.CURLOPT_HEADERFUNCTION, write_callback)
        lcurl.easy_setopt(handle, lcurl.CURLOPT_BUFFERSIZE, 100000)
        lcurl.easy_setopt(handle, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
        lcurl.easy_setopt(handle, lcurl.CURLOPT_SSL_VERIFYPEER, 0)

    # init a multi stack
    multi_handle: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    lcurl.multi_setopt(multi_handle, lcurl.CURLMOPT_MAXCONNECTS, nparallel + 2)

    # add the first NPARALLEL individual transfers
    for handle in handles:
        lcurl.multi_add_handle(multi_handle, handle)
        add -= 1

    print("curl: %s\n"
          "URL: %s\n"
          "Transfers: %d [%d in parallel]..." %
          (version_info.version.decode("utf-8"), URL, ntotal, nparallel))

    start = datetime.now()

    while total:
        still_running = ct.c_int(1)  # keep number of running handles
        mc: lcurl.CURLMcode = lcurl.multi_perform(multi_handle, ct.byref(still_running))
        still_running = still_running.value

        if still_running:
            # wait for activity, timeout or "nothing"
            if lcurl.CURL_AT_LEAST_VERSION(7, 66, 0) and not defined("FOR_OLDER"):
                mc = lcurl.multi_poll(multi_handle, None, 0, 1000, None)
            else:
                # should be mostly okay
                mc = lcurl.multi_wait(multi_handle, None, 0, 1000, None)
        if mc:
            break

        # See how the transfers went
        while True:
            # for picking up messages with the transfer status
            msgs_left = ct.c_int()   # how many messages are left
            msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi_handle,
                                                                    ct.byref(msgs_left))
            if not msgp: break
            msg = msgp.contents

            if msg.msg == lcurl.CURLMSG_DONE:
                # anything but libcurl.CURLE_OK here disqualifies this entire round
                if msg.data.result:
                    print("Transfer returned %d!" % msg.data.result, file=sys.stderr)
                    return 2
                respcode = ct.c_long()
                if (lcurl.easy_getinfo(msg.easy_handle, lcurl.CURLINFO_RESPONSE_CODE, ct.byref(respcode))
                    or expected_respcode != respcode.value):
                    print("Transfer returned unexpected response code %d!" % respcode.value,
                          file=sys.stderr)
                    return 2
                total -= 1
                lcurl.multi_remove_handle(multi_handle, msg.easy_handle)
                if add:
                    # add it back in to get it restarted
                    lcurl.multi_add_handle(multi_handle, msg.easy_handle)
                    add -= 1

    end = datetime.now()
    diff = (end - start)

    print("Time: %u us, %.2f us/transfer" %
          (diff // timedelta(microseconds=1),
           (diff / timedelta(microseconds=1)) / ntotal))
    print("Freq: %.2f requests/second" %
          (ntotal / diff.total_seconds()))
    print("Downloaded: %u bytes, %.1f GB" %
          (downloaded, downloaded / (1024 * 1024 * 1024)))
    print("Speed: %.1f bytes/sec %.1f MB/s (%u bytes/transfer)" %
          (downloaded / diff.total_seconds(),
           (downloaded / diff.total_seconds()) / (1024 * 1024),
           downloaded // ntotal))

    lcurl.multi_cleanup(multi_handle)

    # Free the libcurl.CURL handles
    for handle in handles:
        lcurl.easy_cleanup(handle)

    return 0


sys.exit(main())
