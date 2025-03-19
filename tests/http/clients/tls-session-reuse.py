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
TLS session reuse
"""

import argparse
import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa
from utils import debug_cb


@lcurl.write_callback
def write_callback(buffer, size, nitems, userp):
    return size * nitems


def add_transfer(multi: lcurl.POINTER(lcurl.CURLM),
                 share: lcurl.POINTER(lcurl.CURLSH),
                 resolve: ct.POINTER(lcurl.slist),
                 url: str, http_version: int):

    easy: lcurl.POINTER(lcurl.CURL) = lcurl.easy_init()
    if not easy:
        print("curl_easy_init failed", file=sys.stderr)
        exit(1);

    lcurl.easy_setopt(easy, lcurl.CURLOPT_VERBOSE, 1)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_DEBUGFUNCTION, debug_cb)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_URL, url.encode("utf-8"))
    lcurl.easy_setopt(easy, lcurl.CURLOPT_SHARE, share)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_NOSIGNAL, 1)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_AUTOREFERER, 1)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_FAILONERROR, 1)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_HTTP_VERSION, http_version)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_WRITEFUNCTION, write_cb)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_WRITEDATA, None)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_HTTPGET, 1)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    if resolve:
        lcurl.easy_setopt(easy, lcurl.CURLOPT_RESOLVE, resolve)

    mc: lcurl.CURLMcode = lcurl.multi_add_handle(multi, easy)
    if mc != lcurl.CURLM_OK:
        print("curl_multi_add_handle: %s" % lcurl.multi_strerror(mc).decode("utf-8"),
              file=sys.stderr)
        exit(1);


def main(argv=sys.argv[1:]) -> int:
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) != 2:
        print(f"python {app_name} proto URL", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(prog=f"python {app_name}")
    parser.add_argument("proto")
    parser.add_argument("url")
    args = parser.parse_args(argv)

    if args.proto == "h2":
        http_version: int = lcurl.CURL_HTTP_VERSION_2
    elif args.proto == "h3":
        http_version: int = lcurl.CURL_HTTP_VERSION_3ONLY
    else:
        http_version: int = lcurl.CURL_HTTP_VERSION_1_1
    url: str = args.url

    mc: lcurl.CURLMcode
    msg: ct.POINTER(lcurl.CURLMsg)

    cu: lcurl.POINTER(CURLU) = lcurl.url()
    if not cu:
        print("out of memory", file=sys.stderr)
        return 1
    if lcurl.url_set(cu, lcurl.CURLUPART_URL, url.encode("utf-8"), 0):
        print("not a URL: '%s'" % url, file=sys.stderr)
        return 1
    host = ct.c_char_p()
    if lcurl.url_get(cu, lcurl.CURLUPART_HOST, ct.byref(host), 0):
        print("could not get host of '%s'" % url, file=sys.stderr)
        return 1
    port = ct.c_char_p()
    if lcurl.url_get(cu, lcurl.CURLUPART_PORT, ct.byref(port), 0):
        print("could not get port of '%s'" % url, file=sys.stderr)
        return 1

    resolve = lcurl.slist()
    ct.memset(ct.byref(resolve), 0, ct.sizeof(resolve))
    lcurl.slist_append(ct.byref(resolve), b"%s:%s:127.0.0.1" % (host.value, port.value))

    multi: lcurl.POINTER(CURLM) = lcurl.multi_init()
    if not multi:
        print("curl_multi_init failed", file=sys.stderr)
        return 1

    share: lcurl.POINTER(CURLSH) = lcurl.share_init()
    if not share:
        print("curl_share_init failed", file=sys.stderr)
        return 1

    lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE, lcurl.CURL_LOCK_DATA_SSL_SESSION)

    add_transfer(multi, share, ct.byref(resolve), url, http_version)
    ongoing:  int = 1
    add_more: int = 6
    waits:    int = 3
    while ongoing or add_more:
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

        if waits:
            waits -= 1
        else:
            while add_more:
                add_transfer(multi, share, ct.byref(resolve), url, http_version)
                ongoing  += 1
                add_more -= 1

        # Check for finished handles and remove.
        # !checksrc! disable EQUALSNULL 1
        msgs_in_queue = ct.c_int()
        while (msg := lcurl.multi_info_read(multi, ct.byref(msgs_in_queue))) != NULL:
            msg = msg.contents
            if msg.msg == lcurl.CURLMSG_DONE:
                xfer_id = lcurl.off_t()
                status  = ct.c_long(0)
                lcurl.easy_getinfo(msg.easy_handle, lcurl.CURLINFO_XFER_ID, ct.byref(xfer_id))
                lcurl.easy_getinfo(msg.easy_handle, lcurl.CURLINFO_RESPONSE_CODE, ct.byref(status))
                if (msg.data.result == lcurl.CURLE_SEND_ERROR or
                    msg.data.result == lcurl.CURLE_RECV_ERROR):
                    # We get these if the server had a GOAWAY in transit on
                    # re-using a connection
                    pass
                elif msg.data.result:
                    print(f"transfer #%{lcurl.CURL_FORMAT_CURL_OFF_T}: failed "
                          "with %d" % (xfer_id, msg.data.result), file=sys.stderr)
                    return 1
                elif status != 200:
                    print(f"transfer #%{lcurl.CURL_FORMAT_CURL_OFF_T}: wrong http status "
                          "%ld (expected 200)" % (xfer_id, status), file=sys.stderr)
                    return 1
                lcurl.multi_remove_handle(multi, msg.easy_handle)
                lcurl.easy_cleanup(msg.easy_handle)
                ongoing += 1
                print(f"transfer #%{lcurl.CURL_FORMAT_CURL_OFF_T} retiring (%d now "
                      "running)" % (xfer_id, running_handles), file=sys.stderr)

        print("running_handles=%d, yet_to_start=%d" %
              (running_handles, add_more), file=sys.stderr)

    print("exiting", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
