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
try:
    import threading
except ImportError:  # pragma: no cover
    threading = None

import libcurl as lcurl
from curl_test import *  # noqa

NUM_THREADS = 100


def run_thread(result_p: ct.POINTER(lcurl.CURLcode)):
    # result_p = ct.cast(ptr, ct.POINTER(lcurl.CURLcode))
    res: lcurl.CURLcode = lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    result_p.contents.value = res
    if res == lcurl.CURLE_OK:  # pragma: no branch
        lcurl.global_cleanup()


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    ver = lcurl.version_info(lcurl.CURLVERSION_NOW).contents

    if threading is not None:

        if (ver.features & lcurl.CURL_VERSION_THREADSAFE) == 0:  # pragma: no cover
            print("%s:%d %s but the libcurl.CURL_VERSION_THREADSAFE"
                  " feature flag is not set" %
                  (current_file(), current_line(),
                   "On Windows" if is_windows else "Have threads"),
                  file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

    else:  # without pthread or Windows, this test doesn't work

        if (ver.features & lcurl.CURL_VERSION_THREADSAFE) != 0:
            print("%s:%d No threads but the "
                  "libcurl.CURL_VERSION_THREADSAFE feature flag is set" %
                  (current_file(), current_line()), file=sys.stderr)
            return TEST_ERR_MAJOR_BAD

        return lcurl.CURLE_OK

    test_failure: lcurl.CURLcode = lcurl.CURLE_OK

    threads: List[threading.Thread] = []
    results: List[lcurl.CURLcode]   = []

    for i in range(NUM_THREADS):
        result = lcurl.CURLcode()  #lcurl.CURL_LAST  # initialize with invalid value
        try:
            thread = threading.Thread(target=run_thread, args=(ct.pointer(result),))
            thread.start()
        except Exception as exc:
            print("%s:%d Couldn't create thread, errno %d" %
                  (current_file(), current_line(), exc.errno), file=sys.stderr)
            test_failure = TEST_ERR_MAJOR_BAD
            break
        threads.append(thread)
        results.append(result)

    for thread in threads:
        thread.join()

    del thread, threads

    for i, result in enumerate(results):
        result = result.value
        if result != lcurl.CURLE_OK:  # pragma: no cover
            print("%s:%d thread[%u]: libcurl.global_init() failed, with code %d (%s)" %
                  (current_file(), current_line(),
                   i, result, lcurl.easy_strerror(result).decode("utf-8")),
                  file=sys.stderr)
            test_failure = TEST_ERR_MAJOR_BAD

    return test_failure
