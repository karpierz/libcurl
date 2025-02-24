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
HTTP/2 Upgrade test
"""

import argparse
import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa
from utils import debug_cb


@lcurl.write_callback
def write_cb(buffer, size, nitems, userp):
    return size * nitems


def main(argv=sys.argv[1:]) -> int:
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) != 1:
        print(f"python {app_name} URL", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(prog=f"python {app_name}")
    parser.add_argument("url")
    args = parser.parse_args(argv)

    url: str = args.url

    multi: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    if not multi:
        print("curl_multi_init failed", file=sys.stderr)
        return 1

    start_count: int = 200
    while True:
        mc: lcurl.CURLMcode
        if start_count:
            easy: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
            if not easy:
                print("curl_easy_init failed", file=sys.stderr)
                return 1

            lcurl.easy_setopt(easy, lcurl.CURLOPT_VERBOSE, 1)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_DEBUGFUNCTION, debug_cb)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_URL, url.encode("utf-8"))
            lcurl.easy_setopt(easy, lcurl.CURLOPT_NOSIGNAL, 1)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_AUTOREFERER, 1)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_FAILONERROR, 1)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_HTTP_VERSION,
                                    lcurl.CURL_HTTP_VERSION_2_0)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_WRITEFUNCTION, write_cb)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_WRITEDATA, None)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_HTTPGET, 1)
            lcurl.easy_setopt(easy, lcurl.CURLOPT_RANGE, b"0-16384")

            mc = lcurl.multi_add_handle(multi, easy)
            if mc != lcurl.CURLM_OK:
                print("curl_multi_add_handle: %s" %
                      lcurl.multi_strerror(mc).decode("utf-8"), file=sys.stderr)
                return 1
            start_count -= 1

        running_handles = ct.c_int(0)
        mc = lcurl.multi_perform(multi, ct.byref(running_handles))
        if mc != lcurl.CURLM_OK:
            print("curl_multi_perform: %s" %
                  lcurl.multi_strerror(mc).decode("utf-8"), file=sys.stderr)
            return 1
        running_handles = running_handles.value

        if running_handles:
            numfds = ct.c_int()
            mc = lcurl.multi_poll(multi, None, 0, 1000000, ct.byref(numfds))
            if mc != lcurl.CURLM_OK:
                print("curl_multi_poll: %s" %
                      lcurl.multi_strerror(mc).decode("utf-8"), file=sys.stderr)
                return 1

        # Check for finished handles and remove.
        # !checksrc! disable EQUALSNULL 1
        msg: ct.POINTER(lcurl.CURLMsg)
        msgs_in_queue = ct.c_int()
        while (msg := lcurl.multi_info_read(multi, ct.byref(msgs_in_queue))):
            msg = msg.contents
            if msg.msg == lcurl.CURLMSG_DONE:
                xfer_id = lcurl.off_t()
                status  = ct.c_long(0)
                lcurl.easy_getinfo(msg.easy_handle, lcurl.CURLINFO_XFER_ID,       ct.byref(xfer_id))
                lcurl.easy_getinfo(msg.easy_handle, lcurl.CURLINFO_RESPONSE_CODE, ct.byref(status))
                xfer_id = xfer_id.value
                status  = status.value
                if (msg.data.result == lcurl.CURLE_SEND_ERROR or
                    msg.data.result == lcurl.CURLE_RECV_ERROR):
                    # We get these if the server had a GOAWAY in transit on
                    # re-using a connection
                    pass
                elif msg.data.result:
                    print(f"transfer #%{lcurl.CURL_FORMAT_CURL_OFF_T}: failed "
                          "with %d" % (xfer_id, msg.data.result), file=sys.stderr)
                    return 1
                elif status != 206:
                    print(f"transfer #%{lcurl.CURL_FORMAT_CURL_OFF_T}: wrong http status "
                          "%ld (expected 206)" % (xfer_id, status), file=sys.stderr)
                    return 1

                lcurl.multi_remove_handle(multi, msg.easy_handle)
                lcurl.easy_cleanup(msg.easy_handle)
                print(f"transfer #%{lcurl.CURL_FORMAT_CURL_OFF_T} retiring (%d now "
                      "running)" % (xfer_id, running_handles), file=sys.stderr)

        print("running_handles=%d, yet_to_start=%d" %
              (running_handles, start_count), file=sys.stderr)

        if not (running_handles > 0 or start_count):
            break

    print("exiting", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
