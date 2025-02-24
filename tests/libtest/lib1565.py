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
try:
    import threading
except ImportError:
    threading = None

import libcurl as lcurl
from curl_test import *  # noqa

TIME_BETWEEN_START_SECS = 2
CONN_NUM = 3

lock = threading.Lock()
pending_handles = (ct.POINTER(lcurl.CURL) * CONN_NUM)()
pending_num:  int = 0

test_failure: lcurl.CURLcode = lcurl.CURLE_OK
testmulti: ct.POINTER(lcurl.CURLM) = ct.POINTER(lcurl.CURLM)()
url: str = None

def run_thread():

    global lock
    global pending_handles
    global pending_num
    global test_failure
    global testmulti
    global url

    res: lcurl.CURLcode = lcurl.CURLE_OK
    easy: ct.POINTER(lcurl.CURL) = ct.POINTER(lcurl.CURL)()

    for i in range(CONN_NUM):

        time.sleep(TIME_BETWEEN_START_SECS)

        easy = easy_init()

        easy_setopt(easy, lcurl.CURLOPT_URL, url.encode("utf-8"))
        easy_setopt(easy, lcurl.CURLOPT_VERBOSE, 0)

        with lock:
            # critical section: begin
            if test_failure:
                break
            pending_handles[pending_num] = easy
            pending_num += 1
            easy = ct.POINTER(lcurl.CURL)()  # NULL
            # critical section: end

        err = res_multi_wakeup(testmulti)
        if err: res = err

    # test_cleanup:

    lcurl.easy_cleanup(easy)

    with lock:
        # critical section: begin
        if not test_failure:
            test_failure = res
        # critical section: end


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    # <Added by AK (Adam Karpierz)> as in lib3026.py
    ver = lcurl.version_info(lcurl.CURLVERSION_NOW).contents

    if threading is not None:

        if (ver.features & lcurl.CURL_VERSION_THREADSAFE) == 0:
            print("%s:%d %s but the libcurl.CURL_VERSION_THREADSAFE"
                  " feature flag is not set" %
                  (current_file(), current_line(),
                   "On Windows" if is_windows else "Have threads"),
                  file=sys.stderr)
            return lcurl.CURLcode(-1).value

    else:  # without pthread or Windows, this test doesn't work

        if (ver.features & lcurl.CURL_VERSION_THREADSAFE) != 0:
            print("%s:%d No threads but the "
                  "libcurl.CURL_VERSION_THREADSAFE feature flag is set" %
                  (current_file(), current_line()), file=sys.stderr)
            return lcurl.CURLcode(-1).value

        return lcurl.CURLE_OK
    # </Added by AK (Adam Karpierz)>

    global lock
    global pending_handles
    global pending_num
    global test_failure
    global testmulti
    global url

    # <Added by AK (Adam Karpierz)> as in lib3026.py
    if is_windows:
        # On Windows libcurl global init/cleanup calls LoadLibrary/FreeLibrary for
        # secur32.dll and iphlpapi.dll. Here we load them beforehand so that when
        # libcurl calls LoadLibrary/FreeLibrary it only increases/decreases the
        # library's refcount rather than actually loading/unloading the library,
        # which would affect the test runtime.
        tutil.win32_load_system_library("secur32.dll")
        tutil.win32_load_system_library("iphlpapi.dll")
    # </Added by AK (Adam Karpierz)>

    start_test_timing()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    testmulti = multi_init()
    url       = URL

    res: lcurl.CURLcode = lcurl.CURLE_OK

    thread_valid = False
    try:
        thread = threading.Thread(target=run_thread, args=())
        thread.start()
        thread_valid = True
    except Exception as exc:
        print("%s:%d Couldn't create thread, errno %d" %
              (current_file(), current_line(), exc.errno), file=sys.stderr)
        res = TEST_ERR_MAJOR_BAD
        goto(test_cleanup)

    started_handles = (ct.POINTER(lcurl.CURL) * CONN_NUM)()
    started_num:  int = 0
    finished_num: int = 0
    while True:

        still_running = ct.c_int()
        multi_perform(testmulti, ct.byref(still_running))
        still_running = still_running.value

        abort_on_test_timeout()

        while True:
            msgs_left = ct.c_int()  # how many messages are left
            msgp: ct.POINTER(lcurl.CURLMsg) = lcurl.multi_info_read(testmulti,
                                                                    ct.byref(msgs_left))
            if not msgp: break
            message = msgp.contents

            if message.msg == lcurl.CURLMSG_DONE:
                res = message.data.result
                if res: goto(test_cleanup)
                multi_remove_handle(testmulti, message.easy_handle)
                finished_num += 1
            else:
                print("%s:%d Got an unexpected message from curl: %i" %
                      (current_file(), current_line(), message.msg),
                      file=sys.stderr)
                res = TEST_ERR_MAJOR_BAD
                goto(test_cleanup)

            abort_on_test_timeout()

        if finished_num == CONN_NUM:
            break

        num = ct.c_int()
        multi_poll(testmulti, None, 0, TEST_HANG_TIMEOUT, ct.byref(num))

        abort_on_test_timeout()

        with lock:
            # critical section: begin
            while pending_num > 0:
                res = res_multi_add_handle(testmulti, pending_handles[pending_num - 1])
                if res: goto(test_cleanup)
                started_handles[started_num] = pending_handles[pending_num - 1]
                started_num += 1
                pending_num -= 1
            # critical section: end

        abort_on_test_timeout()

    if started_num != CONN_NUM:
        print("%s:%d Not all connections started: %d of %d" %
              (current_file(), current_line(),
               started_num, CONN_NUM), file=sys.stderr)
        goto(test_cleanup)

    if finished_num != CONN_NUM:
        print("%s:%d Not all connections finished: %d of %d" %
              (current_file(), current_line(),
               started_num, CONN_NUM), file=sys.stderr)
        goto(test_cleanup)

    # test_cleanup:

    with lock:
        # critical section: begin
        if not test_failure:
            test_failure = res
        # critical section: end

    if thread_valid:
        thread.join()

    lcurl.multi_cleanup(testmulti)
    for i in range(pending_num):
        lcurl.easy_cleanup(pending_handles[i])
    for i in range(started_num):
        lcurl.easy_cleanup(started_handles[i])
    lcurl.global_cleanup()

    return test_failure
