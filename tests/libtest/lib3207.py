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
except ImportError:
    threading = None

import libcurl as lcurl
from curl_test import *  # noqa

THREAD_SIZE     = 16
PER_THREAD_SIZE = 8

CA_INFO: str = None


class Ctx(ct.Structure):
    _fields_ = [
    ("URL",       ct.c_char_p),
    ("share",     ct.POINTER(lcurl.CURLSH)),
    ("result",    ct.c_int),
    ("thread_id", ct.c_int),
    ("contents",  ct.POINTER(lcurl.slist)),
]


@lcurl.write_callback
def write_memory_callback(buffer, size, nitems, userp):
      mem = ct.cast(userp, ct.POINTER(Ctx)).contents

      # append the data to buffer
      realsize = size * nitems
      data = (ct.c_char * (realsize + 1))()
      if not data:
          print("not enough memory (malloc returned NULL)")
          return 0

      ct.memmove(data, buffer, realsize)
      data[realsize] = b'\0'
      item_append: ct.POINTER(lcurl.slist) = lcurl.slist_append(mem.contents, data)

      del data

      if item_append:
          mem.contents = item_append
      else:
          print("not enough memory (lcurl.slist_append returned NULL)")
          return 0

      return realsize


def test_thread(ctxp: ct.POINTER(Ctx)):

    global CA_INFO

    ctx: Ctx = ct.cast(ctxp, ct.POINTER(Ctx)).contents

    res: lcurl.CURLcode = lcurl.CURLE_OK

    # Loop the transfer and cleanup the handle properly every lap. This will
    # still reuse ssl session since the pool is in the shared object!
    for i in range(PER_THREAD_SIZE):
        curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
        if curl:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, ctx.URL)

            # use the share object
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SHARE, ctx.share)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_CAINFO, CA_INFO)

            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_memory_callback)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.cast(ctxp, ct.c_void_p))
            lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

            # Perform the request, res will get the return code
            res = lcurl.easy_perform(curl)

            # always cleanup
            lcurl.easy_cleanup(curl)
            # Check for errors
            if res != lcurl.CURLE_OK:
                print("libcurl.easy_perform() failed: %s" %
                      lcurl.easy_strerror(res).decode("utf-8"), file=sys.stderr)
                break

    ctx.result = int(res)

    return 0


@lcurl.lock_function
def test_lock(handle, data, locktype, useptr):
    mutexes = ct.cast(useptr, ct.POINTER(ct.py_object))
    mutexes[data].acquire()


@lcurl.unlock_function
def test_unlock(handle, data, useptr):
    mutexes = ct.cast(useptr, ct.POINTER(ct.py_object))
    mutexes[data].release()


def execute(share: ct.POINTER(lcurl.CURLSH), thread_ctx: ct.POINTER(Ctx)):

    if threading is None:
        # without pthread, run serially
        for ctx in thread_ctx:
            test_thread(ct.byref(ctx))
        return

    mutexes = (ct.py_object * (lcurl.CURL_LOCK_DATA_LAST - 1))()
    for i in range(len(mutexes)):
        mutexes[i] = threading.RLock()

    lcurl.share_setopt(share, lcurl.CURLSHOPT_LOCKFUNC, test_lock)
    lcurl.share_setopt(share, lcurl.CURLSHOPT_UNLOCKFUNC, test_unlock)
    lcurl.share_setopt(share, lcurl.CURLSHOPT_USERDATA, ct.cast(mutexes, ct.c_void_p))
    lcurl.share_setopt(share, lcurl.CURLSHOPT_SHARE, lcurl.CURL_LOCK_DATA_SSL_SESSION)

    threads: List[threading.Thread] = []

    if is_windows:
        # On Windows libcurl global init/cleanup calls LoadLibrary/FreeLibrary for
        # secur32.dll and iphlpapi.dll. Here we load them beforehand so that when
        # libcurl calls LoadLibrary/FreeLibrary it only increases/decreases the
        # library's refcount rather than actually loading/unloading the library,
        # which would affect the test runtime.
        tutil.win32_load_system_library("secur32.dll")
        tutil.win32_load_system_library("iphlpapi.dll")

    for i, ctx in enumerate(thread_ctx):
        try:
            thread = threading.Thread(target=test_thread, args=(ct.pointer(ctx),))
            thread.start()
        except Exception as exc:
            print("%s:%d Couldn't create thread, errno %d" %
                  (current_file(), current_line(), exc.errno), file=sys.stderr)
            raise exc  # break
        threads.append(thread)

    for i, thread in enumerate(threads):
        if thread:
            thread.join()
            threads[i] = None

    del thread, threads

    lcurl.share_setopt(share, lcurl.CURLSHOPT_LOCKFUNC, None)
    lcurl.share_setopt(share, lcurl.CURLSHOPT_UNLOCKFUNC, None)

    for i in range(len(mutexes)):
        mutexes[i] = None


@curl_test_decorator
def test(URL: str, CA_info: str) -> lcurl.CURLcode:

    global CA_INFO
    CA_INFO = CA_info

    res: lcurl.CURLcode = lcurl.CURLE_OK

    thread_ctx = (Ctx * THREAD_SIZE)()

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    share: ct.POINTER(lcurl.CURLSH) = lcurl.share_init()

    with curl_guard(True, share=share):
        if not share:
            print("libcurl.share_init() failed", file=sys.stderr)
            return res # !!! raczej fail !!!

        for i, ctx in enumerate(thread_ctx):
            ctx.URL       = URL.encode("utf-8")
            ctx.share     = share
            ctx.result    = 0
            ctx.thread_id = i
            ctx.contents  = None

        execute(share, thread_ctx)

        for ctx in thread_ctx:
            if ctx.result:
                res = lcurl.CURLcode(ctx.result).value
            else:
                item: ct.POINTER(lcurl.slist) = ctx.contents
                while item:
                    item = item.contents
                    print("%s" % item.data, end="")
                    item = item.next
            lcurl.slist_free_all(ctx.contents)

    return res
