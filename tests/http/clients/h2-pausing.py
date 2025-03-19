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

import argparse
import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa
from utils import debug_cb

HANDLECOUNT = 2


class shandle(ct.Structure):
    _fields_ = [
    ("idx",        ct.c_int),
    ("paused",     ct.c_int),
    ("resumed",    ct.c_bool),
    ("errored",    ct.c_int),
    ("fail_write", ct.c_bool),
    ("h",          ct.POINTER(lcurl.CURL)),
]


@lcurl.write_callback
def wtite_cb(buffer, size, nitems, outstream):
    handle: ct.POINTER(shandle) = ct.cast(outstream, ct.POINTER(shandle)).contents
    realsize = size * nitems

    totalsize = lcurl.off_t()
    if lcurl.easy_getinfo(handle.h, lcurl.CURLINFO_CONTENT_LENGTH_DOWNLOAD_T,
                          ct.byref(totalsize)) == lcurl.CURLE_OK:
        totalsize = totalsize.value
        print(f"INFO: [%d] write, Content-Length %{lcurl.CURL_FORMAT_CURL_OFF_T}" %
              (handle.idx, totalsize), file=sys.stderr)

    if not handle.resumed:
        handle.paused += 1
        print("INFO: [%d] write, PAUSING %d time on %u bytes" %
              (handle.idx, handle.paused, realsize), file=sys.stderr)
        assert handle.paused == 1
        return lcurl.CURL_WRITEFUNC_PAUSE

    if handle.fail_write:
        handle.errored += 1
        print("INFO: [%d] FAIL write of %u bytes, %d time" %
              (handle.idx, realsize, handle.errored), file=sys.stderr)
        return lcurl.CURL_WRITEFUNC_ERROR

    print("INFO: [%d] write, accepting %u bytes" %
          (handle.idx, realsize), file=sys.stderr)

    return realsize


def usage(msg = None):
    if msg is not None: print("%s" % msg, file=sys.stderr)
    print("usage: [options] url\n"
          "  pause downloads with following options:\n"
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

    #while (ch := getopt(argc, argv, "hV:")) != -1:
    #    else:
    #        usage("invalid option")
    #        return 1

    #if argc != 1:
    #    print("ERROR: need URL as argument", file=sys.stderr)
    #    return 2

    http_version: int = lcurl.CURL_HTTP_VERSION_2_0
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

    rc: int = 0

    all_paused: bool  = False
    resume_round: int = -1

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    lcurl.global_trace(b"ids,time,http/2,http/3")

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

    handles = (shandle * HANDLECOUNT)()
    for i, handle in enumerate(handles):

        handle.idx        = i
        handle.paused     = 0
        handle.resumed    = False
        handle.errored    = 0
        handle.fail_write = True
        handle.h          = lcurl.easy_init()

        if (not handle.h or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_WRITEFUNCTION, wtite_cb)     != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_WRITEDATA, ct.byref(handle)) != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_FOLLOWLOCATION, 1)           != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_VERBOSE, 1)                  != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_DEBUGFUNCTION, debug_cb)     != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_SSL_VERIFYPEER, 0)           != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_RESOLVE, resolve)            != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_PIPEWAIT, 1)                 != lcurl.CURLE_OK or
            lcurl.easy_setopt(handle.h, lcurl.CURLOPT_URL, url.encode("utf-8"))    != lcurl.CURLE_OK):
            err()

        lcurl.easy_setopt(handle.h, lcurl.CURLOPT_HTTP_VERSION, http_version)

    multi_handle: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    if not multi_handle:
        err()

    for handle in handles:
        if lcurl.multi_add_handle(multi_handle, handle.h) != lcurl.CURLM_OK:
            err()

    rounds: int = -1
    while True:
        rounds += 1
        print("INFO: multi_perform round %d" % rounds, file=sys.stderr)
        still_running = ct.c_int(1)
        if lcurl.multi_perform(multi_handle, ct.byref(still_running)) != lcurl.CURLM_OK:
            err()
        still_running = still_running.value

        if not still_running:
            as_expected: bool = True
            print("INFO: no more handles running", file=sys.stderr)
            for handle in handles:
                if handle.paused == 0:
                    print("ERROR: [%d] NOT PAUSED" % handle.idx, file=sys.stderr)
                    as_expected = False
                elif handle.paused != 1:
                    print("ERROR: [%d] PAUSED %d times!" %
                          (handle.idx, handle.paused), file=sys.stderr)
                    as_expected = False
                elif not handle.resumed:
                    print("ERROR: [%d] NOT resumed!" % handle.idx, file=sys.stderr)
                    as_expected = False
                elif handle.errored != 1:
                    print("ERROR: [%d] NOT errored once, %d instead!" %
                          (handle.idx, handle.errored), file=sys.stderr)
                    as_expected = False
            if not as_expected:
                print("ERROR: handles not in expected state after %d rounds" %
                      rounds, file=sys.stderr)
                rc = 1
            break

        numfds = ct.c_int()
        if lcurl.multi_poll(multi_handle,
                            None, 0, 100, ct.byref(numfds)) != lcurl.CURLM_OK:
            err()

        # !checksrc! disable EQUALSNULL 1
        msg: ct.POINTER(lcurl.CURLMsg)
        msgs_left = ct.c_int()
        while (msg := lcurl.multi_info_read(multi_handle, ct.byref(msgs_left))):
            msg = msg.contents
            if msg.msg == lcurl.CURLMSG_DONE:
                for handle in handles:
                    if msg.easy_handle == handle.h:
                        if handle.paused != 1 or not handle.resumed:
                            print("ERROR: [%d] done, pauses=%d, resumed=%d, "
                                  "result %d - wtf?" % (handle.idx, handle.paused,
                                  handle.resumed, msg.data.result),
                                  file=sys.stderr)
                            rc = 1
                            break

        if rc: break

        # Successfully paused?
        if not all_paused:
            all_paused = all((handle.paused != 0) for handle in handles)
            if all_paused:
                print("INFO: all transfers paused", file=sys.stderr)
                # give transfer some rounds to mess things up
                resume_round = rounds + 2

        if resume_round > 0 and rounds == resume_round:
            # time to resume
            for handle in handles:
                print("INFO: [%d] resumed" % handle.idx, file=sys.stderr)
                handle.resumed = True
                lcurl.easy_pause(handle.h, lcurl.CURLPAUSE_CONT)

    for handle in handles:
        lcurl.multi_remove_handle(multi_handle, handle.h)
        lcurl.easy_cleanup(handle.h)

    lcurl.slist_free_all(resolve)
    lcurl.url_cleanup(cu)
    lcurl.multi_cleanup(multi_handle)
    lcurl.global_cleanup()

    return rc


if __name__ == "__main__":
    sys.exit(main())
