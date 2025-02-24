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

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


if not is_windows:

    from utils import debug_cb, err

    PAUSE_READ_AFTER = 1
    total_read       = 0


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


    int progress_callback(void *clientp,
                          lcurl.off_t dltotal,
                          lcurl.off_t dlnow,
                          lcurl.off_t ultotal,
                          lcurl.off_t ulnow):
        if 0:
            # Used to unpause on progress, but keeping for now.
            CURL *curl = (CURL *)clientp;
            lcurl.easy_pause(curl, lcurl.CURLPAUSE_CONT)
            # lcurl.easy_pause(curl, lcurl.CURLPAUSE_RECV_CONT)
        # endif

        return 0

    def usage(msg = None):
        if msg is not None:
            print("%s" % msg, file=sys.stderr)
        print("usage: [options] url\n"
              "  upload and pause, options:\n"
              "  -V http_version (http/1.1, h2, h3) http version to use",
              file=sys.stderr)

# endif


if not is_windows:

    def main(argv=sys.argv[1:]) -> int:

        res:  lcurl.CURLcode = lcurl.CURLE_OK

        CURLU *cu;
        char *host = NULL, *port = NULL;

        http_version = lcurl.CURL_HTTP_VERSION_1_1
        while (ch := getopt(argc, argv, "V:")) != -1:
            if ch == 'V':
                if optarg == "http/1.1":
                    http_version = lcurl.CURL_HTTP_VERSION_1_1
                elif optarg == "h2":
                    http_version = lcurl.CURL_HTTP_VERSION_2_0
                elif optarg == "h3":
                    http_version = lcurl.CURL_HTTP_VERSION_3ONLY
                else:
                    usage("invalid http version")
                    return 1
                break;
            else:
                usage("invalid option")
                return 1
        argc -= optind
        argv += optind

        if argc != 1:
            usage("not enough arguments")
            return 2

        url = argv[0]

        lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
        lcurl.global_trace(b"ids,time")

        cu = lcurl.url()
        if not cu:
            print("out of memory", file=sys.stderr)
            return 1
        if curl_url_set(cu, lcurl.CURLUPART_URL, url.encode("utf-8"), 0):
            print("not a URL: '%s'" % url, file=sys.stderr)
            return 1
        if curl_url_get(cu, lcurl.CURLUPART_HOST, &host, 0):
            print("could not get host of '%s'" % url, file=sys.stderr)
            return 1
        if curl_url_get(cu, lcurl.CURLUPART_PORT, &port, 0):
            print("could not get port of '%s'" % url, file=sys.stderr)
            return 1

        struct curl_slist *resolve = NULL;
        memset(&resolve, 0, sizeof(resolve));
        char resolve_buf[1024];
        curl_msnprintf(resolve_buf, sizeof(resolve_buf)-1, "%s:%s:127.0.0.1", host, port)
        resolve = lcurl.slist_append(resolve, resolve_buf)

        curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
        if not curl:
            print("out of memory", file=sys.stderr)
            return 1

        # We want to use our own read function.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)

        # It will help us to continue the read function.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_XFERINFOFUNCTION, progress_callback)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_XFERINFODATA, curl);
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
        curl_free(host);
        curl_free(port);
        lcurl.url_cleanup(cu)
        lcurl.global_cleanup()

        return int(res)

else:  # if is_windows:

    def main(argv=sys.argv[1:]) -> int:
        print("Not supported with this compiler.", file=sys.stderr)
        return 1

# endif
