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

import sys
import ctypes as ct
import time

import libcurl as lcurl
from curl_test import *  # noqa


PAUSE_TIME = 5

testname = b"field"


class ReadThis(ct.Structure):
    _fields_ = [
    ("easy",   ct.POINTER(lcurl.CURL)),
    ("origin", lcurl.time_t),
    ("count",  ct.c_int),
]


@lcurl.read_callback
def read_callback(buffer, size, nitems, userp):
    pooh = ct.cast(userp, ct.POINTER(ReadThis)).contents
    buffer_size = nitems * size

    if buffer_size < 1:
        return 0

    count = pooh.count
    pooh.count += 1

    if count == 0:
        buffer[0] = ord(b'A')  # ASCII A.
        return 1

    if count == 1:
        pooh.origin = int(time.time())
        return lcurl.CURL_READFUNC_PAUSE

    if count == 2:
        delta = int(time.time()) - pooh.origin
        buffer[0] = ord(b'A' if delta < PAUSE_TIME else b'B')  # ASCII A or B.
        return 1

    if count == 3:
        return 0

    print("Read callback called after EOF", file=sys.stderr)
    sys.exit(1)


@lcurl.xferinfo_callback
def xferinfo_callback(clientp, dltotal, dlnow, ultotal, ulnow):
    pooh = ct.cast(clientp, ct.POINTER(ReadThis)).contents

    if pooh.origin:
        delta: lcurl.time_t = int(time.time()) - pooh.origin

        if delta >= 4 * PAUSE_TIME:
            print("unpausing failed: drain problem?", file=sys.stderr)
            return lcurl.CURLE_ABORTED_BY_CALLBACK

        if delta >= PAUSE_TIME:
            lcurl.easy_pause(pooh.easy, lcurl.CURLPAUSE_CONT)

    return 0


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = TEST_ERR_FAILURE

    #
    # Check proper pausing/unpausing from a mime or form read callback.
    #

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    pooh = ReadThis()
    pooh.origin = 0
    pooh.count  = 0
    pooh.easy   = curl

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # First set the URL that is about to receive our POST.
        test_setopt(pooh.easy, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # get verbose debug output please
        test_setopt(pooh.easy, lcurl.CURLOPT_VERBOSE, 1)
        # include headers in the output
        test_setopt(pooh.easy, lcurl.CURLOPT_HEADER, 1)

        if defined("LIB670") or defined("LIB671"):
            # Build the mime tree.
            mime: ct.POINTER(lcurl.mime)     = lcurl.mime_init(pooh.easy)
            part: ct.POINTER(lcurl.mimepart) = lcurl.mime_addpart(mime)

            res = lcurl.mime_name(part, testname)
            if res != lcurl.CURLE_OK:
                print("Something went wrong when building the mime structure: %d" %
                      res, file=sys.stderr)
                goto(test_cleanup)

            res = lcurl.mime_data_cb(part, 2, read_callback,
                                    lcurl.seek_callback(0), lcurl.free_callback(0),
                                    ct.byref(pooh))

            # Bind mime data to its easy handle.
            if res == lcurl.CURLE_OK:
                test_setopt(pooh.easy, lcurl.CURLOPT_MIMEPOST, mime)
        else:
            # Build the form.
            formrc: lcurl.CURLFORMcode
            formpost: ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()
            lastptr:  ct.POINTER(lcurl.httppost) = ct.POINTER(lcurl.httppost)()

            # CURL_IGNORE_DEPRECATION(
            fields = (lcurl.forms * 4)()
            fields[0].option = lcurl.CURLFORM_COPYNAME
            fields[0].value  = testname
            fields[1].option = lcurl.CURLFORM_STREAM
            fields[1].value  = ct.cast(ct.pointer(pooh), ct.c_char_p)
            fields[2].option = lcurl.CURLFORM_CONTENTLEN
            fields[2].value  = 2
            fields[3].option = lcurl.CURLFORM_END
            formrc = lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields)
            # )
            if formrc:
                print("libcurl.formadd() = %d" % formrc, file=sys.stderr)
                goto(test_cleanup)

            # We want to use our own read function.
            test_setopt(pooh.easy, lcurl.CURLOPT_READFUNCTION, read_callback)
            # Send a multi-part formpost.
            # CURL_IGNORE_DEPRECATION(
            test_setopt(pooh.easy, lcurl.CURLOPT_HTTPPOST, formpost)
            # )
        # endif

        if defined("LIB670") or defined("LIB672"):
            # Use the multi interface.
            multi: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

            mres: lcurl.CURLMcode = lcurl.multi_add_handle(multi, pooh.easy)
            still_running = ct.c_int(0)
            while not mres:

                mres = lcurl.multi_perform(multi, ct.byref(still_running))
                if not still_running.value or mres != lcurl.CURLM_OK:
                    break

                if pooh.origin:
                    delta: lcurl.time_t = int(time.time()) - pooh.origin

                    if delta >= 4 * PAUSE_TIME:
                        print("unpausing failed: drain problem?", file=sys.stderr)
                        res = lcurl.CURLE_OPERATION_TIMEDOUT
                        break

                    if delta >= PAUSE_TIME:
                        lcurl.easy_pause(pooh.easy, lcurl.CURLPAUSE_CONT)

                fd_read  = lcurl.fd_set()
                fd_write = lcurl.fd_set()
                fd_excep = lcurl.fd_set()

                max_fd = ct.c_int(-1)
                mres = lcurl.multi_fdset(multi,
                                         ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                         ct.byref(max_fd))
                max_fd = max_fd.value
                if mres: break

                timeout = lcurl.timeval(tv_sec=0, tv_usec=1_000_000 * PAUSE_TIME // 10)
                rc: int = lcurl.select(max_fd + 1,
                                       ct.byref(fd_read), ct.byref(fd_write), ct.byref(fd_excep),
                                       ct.byref(timeout))

                if rc == -1:
                    print("Select error", file=sys.stderr)
                    break

            if mres != lcurl.CURLM_OK:
                while True:
                    msgs_left = ct.c_int()
                    msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(multi,
                                                                            ct.byref(msgs_left))
                    if not msgp: break
                    msg = msgp.contents

                    if msg.msg == lcurl.CURLMSG_DONE:
                        res = msg.data.result

            lcurl.multi_remove_handle(multi, pooh.easy)
            lcurl.multi_cleanup(multi)
        else:
            # Use the easy interface.
            test_setopt(pooh.easy, lcurl.CURLOPT_XFERINFODATA, ct.byref(pooh))
            test_setopt(pooh.easy, lcurl.CURLOPT_XFERINFOFUNCTION, xferinfo_callback)
            test_setopt(pooh.easy, lcurl.CURLOPT_NOPROGRESS, 0)

            res = lcurl.easy_perform(pooh.easy)
        # endif

        # test_cleanup:

        if defined("LIB670") or defined("LIB671"):
            lcurl.mime_free(mime)
        else:
            # CURL_IGNORE_DEPRECATION(
            lcurl.formfree(formpost)
            # )

    return res
