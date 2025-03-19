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
Upload pausing
"""

#
# This is based on the PoC client of issue #11769
#

import argparse
import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa
from utils import debug_cb

PAUSE_READ_AFTER = 1


total_read = 0

@lcurl.read_callback
def read_callback(buffer, size, nitems, instream):
    global total_read
    if total_read >= PAUSE_READ_AFTER:
        print("read_callback, return PAUSE", file=sys.stderr)
        return lcurl.CURL_READFUNC_PAUSE
    buffer[0] = b'\n'
    total_read += 1
    print("read_callback, return 1 byte", file=sys.stderr)
    return 1


@lcurl.progress_callback
def progress_callback(clientp, dltotal, dlnow, ultotal, ulnow):
    if 0:
        # Used to unpause on progress, but keeping for now.
        curl: ct.POINTER(lcurl.CURL) = ct.cast(clientp, ct.POINTER(lcurl.CURL))
        lcurl.easy_pause(curl, lcurl.CURLPAUSE_CONT)
        # lcurl.easy_pause(curl, lcurl.CURLPAUSE_RECV_CONT)
    # endif
    return 0


def usage(msg = None):
    if msg is not None: print("%s" % msg, file=sys.stderr)
    print("usage: [options] url\n"
          "  upload and pause, options:\n"
          "  -V http_version (http/1.1, h2, h3) http version to use",
          file=sys.stderr)


def err() -> int:
    print("something unexpected went wrong - bailing out!", file=sys.stderr)
    sys.exit(2)


def main(argv=sys.argv[1:]) -> int:
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if is_windows:
        print("Not supported with this compiler.", file=sys.stderr)
        return 1
    # endif

    parser = argparse.ArgumentParser(prog=f"python {app_name}", add_help=False)
    parser.add_argument("-h", action=usage)  # return 2
    parser.add_argument("-V", dest="http_proto")
    parser.add_argument("url")
    args = parser.parse_args(argv)

    #while (ch := getopt(argc, argv, "V:")) != -1:
    #    else:
    #        usage("invalid option")
    #        return 1

    #if argc != 1:
    #    usage("not enough arguments")
    #    return 2

    http_version: int = lcurl.CURL_HTTP_VERSION_1_1
    if args.http_proto is not None:
        if args.http_proto == "http/1.1":
            http_version = lcurl.CURL_HTTP_VERSION_1_1
        elif args.http_proto == "h2":
            http_version = lcurl.CURL_HTTP_VERSION_2_0
        elif args.http_proto == "h3":
            http_version = lcurl.CURL_HTTP_VERSION_3ONLY
        else:
            usage("invalid http version")
            return 1
    url: str = args.url

    res: lcurl.CURLcode = lcurl.CURLE_OK

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    lcurl.global_trace(b"ids,time")

    cu: ct.POINTER(lcurl.CURLU) = lcurl.url()
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

    resolve = ct.POINTER(lcurl.slist)()
    resolve = lcurl.slist_append(resolve,
                                 b"%s:%s:127.0.0.1" % (host.value, port.value))

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
    if not curl:
        print("out of memory", file=sys.stderr)
        return 1

    # We want to use our own read function.
    lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)

    # It will help us to continue the read function.
    lcurl.easy_setopt(curl, lcurl.CURLOPT_XFERINFOFUNCTION, progress_callback)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_XFERINFODATA, curl)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)

    # It will help us to ensure that keepalive does not help.
    lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPALIVE, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPIDLE, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPINTVL, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_TCP_KEEPCNT, 1)

    # Enable uploading.
    lcurl.easy_setopt(curl, lcurl.CURLOPT_CUSTOMREQUEST, b"POST")
    lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)

    lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

    if (lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)              != lcurl.CURLE_OK or
        lcurl.easy_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_cb) != lcurl.CURLE_OK or
        lcurl.easy_setopt(curl, lcurl.CURLOPT_RESOLVE, resolve)        != lcurl.CURLE_OK):
        err()

    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
    lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION, http_version)

    res = lcurl.easy_perform(curl)

    lcurl.easy_cleanup(curl)
    lcurl.slist_free_all(resolve)
    lcurl.url_cleanup(cu)
    lcurl.global_cleanup()

    return int(res)


if __name__ == "__main__":
    sys.exit(main())
