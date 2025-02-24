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
HTTP/2 download pausing
"""

#
# This is based on the PoC client of issue #11982
#

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa


if not is_windows:

    HANDLECOUNT = 2

    from utils import debug_cb, err

    struct handle
        [
        ("idx",        ct.c_int),
        ("paused",     ct.c_int),
        ("resumed",    ct.c_bool),
        ("errored",    ct.c_int),
        ("fail_write", ct.c_bool),
        ("h",          ct.POINTER(lcurl.CURL),
    ]


    @lcurl.write_callback
    def cb(buffer, size, nitems, outstream):
        struct handle *handle = ((struct handle *) outstream).contents

        realsize = size * nitems

        totalsize = lcurl.off_t()
        if lcurl.easy_getinfo(handle.h, lcurl.CURLINFO_CONTENT_LENGTH_DOWNLOAD_T,
                              ct.byref(totalsize)) == lcurl.CURLE_OK:
            totalsize = totalsize.value
            print(f"INFO: [%d] write, Content-Length %{lcurl.CURL_FORMAT_CURL_OFF_T}" %
                  (handle.idx, totalsize), file=sys.stderr)

        if not handle.resumed:
            handle.paused += 1
            print("INFO: [%d] write, PAUSING %d time on %u bytes",
                  (handle.idx, handle.paused, realsize), file=sys.stderr)
            assert (handle.paused == 1)
            return lcurl.CURL_WRITEFUNC_PAUSE

        if handle.fail_write:
            handle.errored += 1
            print("INFO: [%d] FAIL write of %u bytes, %d time",
                  (handle.idx, realsize, handle.errored), file=sys.stderr)
            return lcurl.CURL_WRITEFUNC_ERROR

        print("INFO: [%d] write, accepting %u bytes",
              (handle.idx, realsize), file=sys.stderr)

        return realsize


    def usage(msg = None):
        if msg is not None:
            print("%s" % msg, file=sys.stderr)
        print("usage: [options] url\n"
              "  pause downloads with following options:\n"
              "  -V http_version (http/1.1, h2, h3) http version to use",
              file=sys.stderr)

# endif


if not is_windows:

    def main(argv=sys.argv[1:]) -> int:

        struct handle handles[HANDLECOUNT];

        int numfds;
        CURLMsg *msg;
        int rc = 0;

        all_paused: bool  = False
        resume_round: int = -1

        http_version: int = lcurl.CURL_HTTP_VERSION_2_0
        while (ch := getopt(argc, argv, "hV:")) != -1:
            if ch == "h":
                usage()
                return 2
            elif ch == "V":
                if optarg == "http/1.1":
                    http_version = lcurl.CURL_HTTP_VERSION_1_1
                elif optarg == "h2":
                    http_version = lcurl.CURL_HTTP_VERSION_2_0
                elif optarg == "h3":
                    http_version = lcurl.CURL_HTTP_VERSION_3ONLY
                else:
                    usage("invalid http version")
                    return 1
            else:
                usage("invalid option")
                return 1
        argc -= optind
        argv += optind

        if argc != 1:
            print("ERROR: need URL as argument", file=sys.stderr)
            return 2

        url = argv[0]

        lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
        lcurl.global_trace(b"ids,time,http/2,http/3")

        cu: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not cu:
            print("out of memory", file=sys.stderr)
            return 1
        if curl_url_set(cu, lcurl.CURLUPART_URL, url.encode("utf-8"), 0):
            print("not a URL: '%s'" % url, file=sys.stderr)
            return 1
        char *host = NULL;
        if curl_url_get(cu, lcurl.CURLUPART_HOST, ct.byref(host), 0):
            print("could not get host of '%s'" % url, file=sys.stderr)
            return 1
        char *port = NULL;
        if curl_url_get(cu, lcurl.CURLUPART_PORT, ct.byref(port), 0):
            print("could not get port of '%s'" % url, file=sys.stderr)
            return 1

        struct curl_slist *resolve = NULL;
        memset(&resolve, 0, sizeof(resolve));
        char resolve_buf[1024];
        curl_msnprintf(resolve_buf, sizeof(resolve_buf)-1, "%s:%s:127.0.0.1", host, port)
        resolve = lcurl.slist_append(resolve, resolve_buf)

        for i in range(HANDLECOUNT):

            handles[i].idx        = i
            handles[i].paused     = 0
            handles[i].resumed    = False
            handles[i].errored    = 0
            handles[i].fail_write = True
            handles[i].h          = lcurl.easy_init()

            if (not handles[i].h or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_WRITEFUNCTION, cb)               != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_WRITEDATA, ct.byref(handles[i])) != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_FOLLOWLOCATION, 1)               != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_VERBOSE, 1)                      != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_DEBUGFUNCTION, debug_cb)         != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_SSL_VERIFYPEER, 0)               != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_RESOLVE, resolve)                != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_PIPEWAIT, 1)                     != lcurl.CURLE_OK or
                lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_URL, url.encode("utf-8"))        != lcurl.CURLE_OK):
                err()

            lcurl.easy_setopt(handles[i].h, lcurl.CURLOPT_HTTP_VERSION, http_version)

        multi_handle: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
        if not multi_handle:
            err()

        for i in range(HANDLECOUNT):
            if lcurl.multi_add_handle(multi_handle, handles[i].h) != lcurl.CURLM_OK:
                err()

        still_running = ct.c_int(1)
        rounds: int = -1
        while True:
            rounds += 1
            print("INFO: multi_perform round %d" % rounds, file=sys.stderr)
            if lcurl.multi_perform(multi_handle, ct.byref(still_running)) != lcurl.CURLM_OK:
                err()
          
            if not still_running.value:
                as_expected: bool = True
                print("INFO: no more handles running", file=sys.stderr)
                for i in range(HANDLECOUNT):
                    if handles[i].paused == 0:
                        print("ERROR: [%d] NOT PAUSED" % i, file=sys.stderr)
                        as_expected = False
                    elif handles[i].paused != 1:
                        print("ERROR: [%d] PAUSED %d times!" %
                              (i, handles[i].paused), file=sys.stderr)
                        as_expected = False
                    elif not handles[i].resumed:
                        print("ERROR: [%d] NOT resumed!" % i, file=sys.stderr)
                        as_expected = False
                    elif handles[i].errored != 1:
                        print("ERROR: [%d] NOT errored once, %d instead!" %
                              (i, handles[i].errored), file=sys.stderr)
                        as_expected = False
                if not as_expected:
                    print("ERROR: handles not in expected state after %d rounds" %
                          rounds, file=sys.stderr)
                    rc = 1
                break;
          
            if curl_multi_poll(multi_handle, NULL, 0, 100, &numfds) != lcurl.CURLM_OK:
                err()
          
            # !checksrc! disable EQUALSNULL 1
            int msgs_left,
            while (msg := curl_multi_info_read(multi_handle, &msgs_left)) != NULL:
                if msg->msg == CURLMSG_DONE:
                    for i in range(HANDLECOUNT):
                        if msg->easy_handle == handles[i].h:
                            if handles[i].paused != 1 or not handles[i].resumed:
                                print("ERROR: [%d] done, pauses=%d, resumed=%d, "
                                      "result %d - wtf?" % (i, handles[i].paused,
                                      handles[i].resumed, msg->data.result),
                                      file=sys.stderr)
                                rc = 1
                                goto out;
          
            # Successfully paused?
            if not all_paused:
                all_paused = all((handles[i].paused != 0)
                                 for i in range(HANDLECOUNT))
                if all_paused:
                    print("INFO: all transfers paused", file=sys.stderr)
                    # give transfer some rounds to mess things up
                    resume_round = rounds + 2
          
            if resume_round > 0 and rounds == resume_round:
                # time to resume
                for i in range(HANDLECOUNT):
                    print("INFO: [%d] resumed" % i, file=sys.stderr)
                    handles[i].resumed = True
                    lcurl.easy_pause(handles[i].h, lcurl.CURLPAUSE_CONT)

        out:

        for i in range(HANDLECOUNT):
            lcurl.multi_remove_handle(multi_handle, handles[i].h)
            lcurl.easy_cleanup(handles[i].h)

        lcurl.slist_free_all(resolve)
        curl_free(host);
        curl_free(port);
        lcurl.url_cleanup(cu)
        lcurl.multi_cleanup(multi_handle)
        lcurl.global_cleanup()

        return rc

else:  # if is_windows:

    def main(argv=sys.argv[1:]) -> int:
        print("Not supported with this compiler.", file=sys.stderr)
        return 1

# endif
