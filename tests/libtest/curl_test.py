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

# Now include the curl_setup.h file from libcurl's private libdir (the source
# version, but that might include "curl_config.h" from the build dir so we
# need both of them in the include path), so that we get good in-depth
# knowledge about the system we're building this on

from typing import Optional, List, Tuple
import sys
import ctypes as ct
import functools
import locale
import time

import libcurl as lcurl
import _tutil as tutil
from curl_utils import *  # noqa

TEST_HANG_TIMEOUT = 60 * 1000


@lcurl.CFUNC(lcurl.CURLcode,
             ct.POINTER(lcurl.CURL), lcurl.CURLoption, ct.c_void_p)
def test_setopt(curl, option, value):
    res = lcurl.easy_setopt(curl, option, value)
    if res != lcurl.CURLE_OK:
        goto(test_cleanup)
    return res

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM), lcurl.CURLMoption, ct.c_void_p)
def test_multi_setopt(multi_handle, option, value):
    res = lcurl.multi_setopt(multi_handle, option, value)
    if res != lcurl.CURLE_OK:
        goto(test_cleanup)
    return res

tv_test_start = lcurl.timeval()  # for test timing

#include "curl_setup.h"

test_func_t = lcurl.CFUNC(lcurl.CURLcode, ct.c_char_p)

if defined("CURLTESTS_BUNDLED"):
    class onetest(ct.Structure):
        _fields_ = [
        ("name", ct.c_char_p),
        ("ptr",  test_func_t),
    ]
# endif

def hexdump(buf: bytes, size: Optional[int] = None) -> bytes:
    # returns a hexdump in a static memory area
    if size is None: size = len(buf)
    dump = b""
    for i in range(min(size, len(buf))):
        dump += "%02x " % buf[i]
    return dump

# TEST_ERR_* values must be greater than CURL_LAST CURLcode in order
# to avoid confusion with any CURLcode or CURLMcode. These TEST_ERR_*
# codes are returned to signal test specific situations and should
# not get mixed with CURLcode or CURLMcode values.
#
# For portability reasons TEST_ERR_* values should be less than 127.

TEST_ERR_MAJOR_BAD    = lcurl.CURLcode(126).value
TEST_ERR_RUNS_FOREVER = lcurl.CURLcode(125).value
TEST_ERR_EASY_INIT    = lcurl.CURLcode(124).value
TEST_ERR_MULTI        = lcurl.CURLcode(123).value
TEST_ERR_NUM_HANDLES  = lcurl.CURLcode(122).value
TEST_ERR_SELECT       = lcurl.CURLcode(121).value
TEST_ERR_SUCCESS      = lcurl.CURLcode(120).value
TEST_ERR_FAILURE      = lcurl.CURLcode(119).value
TEST_ERR_USAGE        = lcurl.CURLcode(118).value
TEST_ERR_FOPEN        = lcurl.CURLcode(117).value
TEST_ERR_FSTAT        = lcurl.CURLcode(116).value
TEST_ERR_BAD_TIMEOUT  = lcurl.CURLcode(115).value

# Macros for test source code readability/maintainability.
#
# All of the following macros require that an int data type 'res' variable
# exists in scope where macro is used, and that it has been initialized to
# zero before the macro is used.
#
# exe_* and chk_* macros are helper macros not intended to be used from
# outside of this header file. Arguments 'Y' and 'Z' of these represent
# source code file and line number, while Arguments 'A', 'B', etc, are
# the arguments used to actually call a libcurl function.
#
# All easy_* and multi_* macros call a libcurl function and evaluate if
# the function has succeeded or failed. When the function succeeds 'res'
# variable is not set nor cleared and program continues normal flow. On
# the other hand if function fails 'res' variable is set and a jump to
# label 'test_cleanup' is performed.
#
# Every easy_* and multi_* macros have a res_easy_* and res_multi_* macro
# counterpart that operates in the same way with the exception that no
# jump takes place in case of failure. res_easy_* and res_multi_* macros
# should be immediately followed by checking if 'res' variable has been
# set.
#
# 'res' variable when set will hold a CURLcode, CURLMcode, or any of the
# TEST_ERR_* values defined above. It is advisable to return this value
# as test result.

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLcode,
             ct.c_long,
             ct.py_object, ct.py_object)
def _exe_global_init(flags, curr_file, curr_line):
    res: lcurl.CURLcode = lcurl.CURLE_OK
    ec:  lcurl.CURLcode = lcurl.global_init(flags)
    if ec != lcurl.CURLE_OK:
        print("%s:%d libcurl.global_init() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.easy_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = ec
    return res

def _chk_global_init(flags, curr_file, curr_line):
    res = _exe_global_init(flags, curr_file, curr_line)
    if res:
        return res
    return res

def res_global_init(flags):
    return _exe_global_init(flags, current_file(2), current_line(2))

def global_init(flags):
    # global_init() is different than other macros. In case of
    # failure it 'return's instead of going to 'test_cleanup'.
    return _chk_global_init(flags, current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(ct.POINTER(lcurl.CURL),
             ct.py_object, ct.py_object)
def _exe_easy_init(curr_file, curr_line):
    curl = lcurl.easy_init()
    if not curl :
        print("%s:%d lcurl.easy_init() failed" %
              (curr_file, curr_line), file=sys.stderr)
        res = TEST_ERR_EASY_INIT
    return curl

def _chk_easy_init(curr_file, curr_line):
    curl = _exe_easy_init(curr_file, curr_line)
    res = None
    if res:
        goto(test_cleanup)
    return curl

def res_easy_init():
    return _exe_easy_init(current_file(2), current_line(2))

def easy_init():
    return _chk_easy_init(current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(ct.POINTER(lcurl.CURLM),
             ct.py_object, ct.py_object)
def _exe_multi_init(curr_file, curr_line):
    multi = lcurl.multi_init()
    if not multi:
        print("%s:%d lcurl.multi_init() failed" %
              (curr_file, curr_line), file=sys.stderr)
        res = TEST_ERR_MULTI
    return multi

def _chk_multi_init(curr_file, curr_line):
    multi = _exe_multi_init(curr_file, curr_line)
    res = None
    if res:
        goto(test_cleanup)
    return multi

def res_multi_init():
    return _exe_multi_init(current_file(2), current_line(2))

def multi_init():
    return _chk_multi_init(current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLcode,
             ct.POINTER(lcurl.CURL), lcurl.CURLoption, ct.c_void_p,
             ct.py_object, ct.py_object)
def _exe_easy_setopt(curl, option, value, curr_file, curr_line):
    res: lcurl.CURLcode = lcurl.CURLE_OK
    ec:  lcurl.CURLcode = lcurl.easy_setopt(curl, option, value)
    if ec != lcurl.CURLE_OK:
        print("%s:%d lcurl.easy_setopt() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.easy_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = ec
    return res

def _chk_easy_setopt(curl, option, value, curr_file, curr_line):
    res = _exe_easy_setopt(curl, option, value, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_easy_setopt(curl, option, value):
    return _exe_easy_setopt(curl, option, value,
                            current_file(2), current_line(2))

def easy_setopt(curl, option, value):
    return _chk_easy_setopt(curl, option, value,
                            current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM), lcurl.CURLMoption, ct.c_void_p,
             ct.py_object, ct.py_object)
def _exe_multi_setopt(multi_handle, option, value, curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_setopt(multi_handle, option, value)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_setopt() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_MULTI
    return res

def _chk_multi_setopt(multi_handle, option, value, curr_file, curr_line):
    res = _exe_multi_setopt(multi_handle, option, value, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_setopt(multi_handle, option, value):
    return _exe_multi_setopt(multi_handle, option, value,
                             current_file(2), current_line(2))

def multi_setopt(multi_handle, option, value):
    return _chk_multi_setopt(multi_handle, option, value,
                             current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM), ct.POINTER(lcurl.CURL),
             ct.py_object, ct.py_object)
def _exe_multi_add_handle(multi_handle, curl_handle, curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_add_handle(multi_handle, curl_handle)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_add_handle() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_MULTI
    return res

def _chk_multi_add_handle(multi_handle, curl_handle, curr_file, curr_line):
    res = _exe_multi_add_handle(multi_handle, curl_handle, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_add_handle(multi_handle, curl_handle):
    return _exe_multi_add_handle(multi_handle, curl_handle,
                                 current_file(2), current_line(2))

def multi_add_handle(multi_handle, curl_handle):
    return _chk_multi_add_handle(multi_handle, curl_handle,
                                 current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM), ct.POINTER(lcurl.CURL),
             ct.py_object, ct.py_object)
def _exe_multi_remove_handle(multi_handle, curl_handle, curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_remove_handle(multi_handle, curl_handle)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_remove_handle() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_MULTI
    return res

def _chk_multi_remove_handle(multi_handle, curl_handle, curr_file, curr_line):
    res = _exe_multi_remove_handle(multi_handle, curl_handle, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_remove_handle(multi_handle, curl_handle):
    return _exe_multi_remove_handle(multi_handle, curl_handle,
                                    current_file(2), current_line(2))

def multi_remove_handle(multi_handle, curl_handle):
    return _chk_multi_remove_handle(multi_handle, curl_handle,
                                    current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM), ct.POINTER(ct.c_int),
             ct.py_object, ct.py_object)
def _exe_multi_perform(multi_handle, running_handles, curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_perform(multi_handle, running_handles)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_perform() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_MULTI
    elif running_handles.contents.value < 0:
        print("%s:%d lcurl.multi_perform() succeeded, but returned "
              "invalid running_handles value (%d)" %
              (curr_file, curr_line, running_handles.contents.value), file=sys.stderr)
        res = TEST_ERR_NUM_HANDLES
    return res

def _chk_multi_perform(multi_handle, running_handles, curr_file, curr_line):
    res = _exe_multi_perform(multi_handle, running_handles, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_perform(multi_handle, running_handles):
    return _exe_multi_perform(multi_handle, running_handles,
                              current_file(2), current_line(2))

def multi_perform(multi_handle, running_handles):
    return _chk_multi_perform(multi_handle, running_handles,
                              current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM),
             ct.POINTER(lcurl.fd_set), ct.POINTER(lcurl.fd_set), ct.POINTER(lcurl.fd_set),
             ct.POINTER(ct.c_int),
             ct.py_object, ct.py_object)
def _exe_multi_fdset(multi_handle, read_fd_set, write_fd_set, exc_fd_set, max_fd,
                     curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_fdset(multi_handle,
                                             read_fd_set, write_fd_set, exc_fd_set,
                                             max_fd)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_fdset() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_MULTI
    elif max_fd.contents.value < -1:
        print("%s:%d lcurl.multi_fdset() succeeded, but returned "
              "invalid max_fd value (%d)" %
              (curr_file, curr_line, max_fd.contents.value), file=sys.stderr)
        res = TEST_ERR_NUM_HANDLES
    return res

def _chk_multi_fdset(multi_handle, read_fd_set, write_fd_set, exc_fd_set, max_fd,
                     curr_file, curr_line):
    res = _exe_multi_fdset(multi_handle, read_fd_set, write_fd_set, exc_fd_set, max_fd,
                           curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_fdset(multi_handle, read_fd_set, write_fd_set, exc_fd_set, max_fd):
    return _exe_multi_fdset(multi_handle, read_fd_set, write_fd_set, exc_fd_set, max_fd,
                            current_file(2), current_line(2))

def multi_fdset(multi_handle, read_fd_set, write_fd_set, exc_fd_set, max_fd):
    return _chk_multi_fdset(multi_handle, read_fd_set, write_fd_set, exc_fd_set, max_fd,
                            current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM), ct.POINTER(ct.c_long),
             ct.py_object, ct.py_object)
def _exe_multi_timeout(multi_handle, milliseconds, curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_timeout(multi_handle, milliseconds)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_timeout() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_BAD_TIMEOUT
    elif milliseconds.contents.value < -1:
        print("%s:%d lcurl.multi_timeout() succeeded, but returned "
              "invalid timeout value (%ld)" %
              (curr_file, curr_line, milliseconds.contents.value), file=sys.stderr)
        res = TEST_ERR_BAD_TIMEOUT
    return res

def _chk_multi_timeout(multi_handle, milliseconds, curr_file, curr_line):
    res = _exe_multi_timeout(multi_handle, milliseconds, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_timeout(multi_handle, milliseconds):
    return _exe_multi_timeout(multi_handle, milliseconds,
                              current_file(2), current_line(2))

def multi_timeout(multi_handle, milliseconds):
    return _chk_multi_timeout(multi_handle, milliseconds,
                              current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM), ct.POINTER(lcurl.waitfd), ct.c_uint, ct.c_int,
             ct.POINTER(ct.c_int),
             ct.py_object, ct.py_object)
def _exe_multi_poll(multi_handle, extra_fds, extra_nfds, timeout_ms, ret,
                    curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_poll(multi_handle, extra_fds, extra_nfds,
                                            timeout_ms, ret)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_poll() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_MULTI
    elif ret.contents.value < 0:
        print("%s:%d lcurl.multi_poll() succeeded, but returned "
              "invalid numfds value (%d)" %
              (curr_file, curr_line, ret.contents.value), file=sys.stderr)
        res = TEST_ERR_NUM_HANDLES
    return res

def _chk_multi_poll(multi_handle, extra_fds, extra_nfds, timeout_ms, ret,
                    curr_file, curr_line):
    res = _exe_multi_poll(multi_handle, extra_fds, extra_nfds, timeout_ms, ret,
                          curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_poll(multi_handle, extra_fds, extra_nfds, timeout_ms, ret):
    return _exe_multi_poll(multi_handle, extra_fds, extra_nfds, timeout_ms, ret,
                           current_file(2), current_line(2))

def multi_poll(multi_handle, extra_fds, extra_nfds, timeout_ms, ret):
    return _chk_multi_poll(multi_handle, extra_fds, extra_nfds, timeout_ms, ret,
                           current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(lcurl.CURLMcode,
             ct.POINTER(lcurl.CURLM),
             ct.py_object, ct.py_object)
def _exe_multi_wakeup(multi_handle, curr_file, curr_line):
    res: lcurl.CURLMcode = lcurl.CURLM_OK
    ec:  lcurl.CURLMcode = lcurl.multi_wakeup(multi_handle)
    if ec != lcurl.CURLM_OK:
        print("%s:%d lcurl.multi_wakeup() failed, with code %d (%s)" %
              (curr_file, curr_line, ec, lcurl.multi_strerror(ec).decode("utf-8")),
              file=sys.stderr)
        res = TEST_ERR_MULTI
    return res

def _chk_multi_wakeup(multi_handle, curr_file, curr_line):
    res = _exe_multi_wakeup(multi_handle, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_multi_wakeup(multi_handle):
    return _exe_multi_wakeup(multi_handle, current_file(2), current_line(2))

def multi_wakeup(multi_handle):
    return _chk_multi_wakeup(multi_handle, current_file(2), current_line(2))

# ------------------------------------------------------------------ #

@lcurl.CFUNC(ct.c_int, ct.c_int,
             ct.POINTER(lcurl.fd_set), ct.POINTER(lcurl.fd_set), ct.POINTER(lcurl.fd_set),
             ct.POINTER(lcurl.timeval),
             ct.py_object, ct.py_object)
def _exe_select_test(nfds, rd, wr, exc, timeout, curr_file, curr_line):
    res: lcurl.CURLcode = lcurl.CURLE_OK
    ec: int
    if lcurl.select(nfds, rd, wr, exc, timeout) == -1:
        ec = SOCKERRNO
        print("%s:%d select() failed, with errno %d (%s)" %
              (curr_file, curr_line, ec, strerror(ec)),
              file=sys.stderr)
        res = TEST_ERR_SELECT
    return res

def _chk_select_test(nfds, rd, wr, exc, timeout, curr_file, curr_line):
    res = _exe_select_test(nfds, rd, wr, exc, timeout, curr_file, curr_line)
    if res:
        goto(test_cleanup)
    return res

def res_select_test(nfds, rd, wr, exc, timeout):
    return _exe_select_test(nfds, rd, wr, exc, timeout,
                            current_file(2), current_line(2))

def select_test(nfds, rd, wr, exc, timeout):
    return _chk_select_test(nfds, rd, wr, exc, timeout,
                            current_file(2), current_line(2))

# ------------------------------------------------------------------ #

def start_test_timing():
    global tv_test_start
    tv_test_start = tutil.tvnow()

def _exe_test_timedout(curr_file, curr_line, *, test_hang_timeout):
    res: lcurl.CURLcode = lcurl.CURLE_OK
    timediff = tutil.tvdiff(tutil.tvnow(), tv_test_start)
    if timediff > test_hang_timeout:
        print("%s:%d ABORTING TEST, since it seems that it "
              "would have run forever (%ld ms > %ld ms)" %
              (curr_file, curr_line, timediff, test_hang_timeout),
              file=sys.stderr)
        res = TEST_ERR_RUNS_FOREVER
    return res

def _chk_test_timedout(curr_file, curr_line, *, test_hang_timeout):
    res = _exe_test_timedout(curr_file, curr_line,
                             test_hang_timeout=test_hang_timeout)
    if res:
        goto(test_cleanup)
    return res

def res_test_timedout(test_hang_timeout=TEST_HANG_TIMEOUT):
    return _exe_test_timedout(current_file(2), current_line(2),
                              test_hang_timeout=test_hang_timeout)

def abort_on_test_timeout(test_hang_timeout=TEST_HANG_TIMEOUT):
    return _chk_test_timedout(current_file(2), current_line(2),
                              test_hang_timeout=TEST_HANG_TIMEOUT)

# ------------------------------------------------------------------ #

def curl_test_decorator(test_func):
    """ """
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs) -> int:

        # # ifdef O_BINARY
        #     setmode(fileno(sys.stdout), O_BINARY);
        # # endif
        # # switch to binary mode
        # sys.stdout = sys.stdout.buffer

        memory_tracking_init()

        # Setup proper locale from environment. This is needed to enable locale-
        # specific behavior by the C library in order to test for undesired side
        # effects that could cause in libcurl.
        if True or defined("HAVE_SETLOCALE"): # !!!
            locale.setlocale(locale.LC_ALL, "")
        # endif

        if len(args) == 0:
            print("Pass URL as argument please", file=sys.stderr)
            return 1

        URL: str = args[0]
        print("URL: %s" % URL, file=sys.stderr)

        # getting the returned value
        result: int = int(test_func(URL, *args[1:], **kwargs))

        if defined("USE_NSS"):
            if PR_Initialized():
                # prevent valgrind from reporting possibly lost memory (fd cache, ...)
                PR_Cleanup()
        # endif

        # ifdef WIN32
            # flush buffers of all streams regardless of mode
            #!!! _flushall()
        # endif

        # switch back
        sys.stdout = sys.__stdout__

        return result

    return wrapper

# ifdef USE_NSS
# include <nspr.h>
# endif
if defined("CURLDEBUG"):
    MEMDEBUG_NODEFINES = 1
    #include "memdebug.h"
# endif
# include "timediff.h"

if defined("CURLDEBUG"):

    # CURL_EXTERN void curl_dbg_memdebug(const char *logname);
    CFUNC(None, ct.c_char_p)
    def curl_dbg_memdebug(logname):
        pass

    # CURL_EXTERN void curl_dbg_memlimit(long limit);
    CFUNC(None, ct.c_long)
    def curl_dbg_memlimit(limit):
        pass

    if (not hasattr(lcurl, "dbg_memdebug") or
        not hasattr(lcurl, "dbg_memlimit")):
        lcurl.dbg_memdebug = curl_dbg_memdebug
        lcurl.dbg_memlimit = curl_dbg_memlimit

    def memory_tracking_init():

        # if CURL_MEMDEBUG is set, this starts memory tracking message logging
        env = lcurl.getenv("CURL_MEMDEBUG")
        if env:
            logfname = env
            lcurl.dbg_memdebug(logfname)

        # if CURL_MEMLIMIT is set, this enables fail-on-alloc-number-N feature
        env = lcurl.getenv("CURL_MEMLIMIT")
        if env:
            try:
                num = int(env)
            except: pass
            else:
                if num > 0:
                    lcurl.dbg_memlimit(num)

else:

    def memory_tracking_init():
        pass

# endif

# ------------------------------------------------------------------ #

@curl_test_decorator
def test_missing_support(URL: str, *args, **kwargs) -> lcurl.CURLcode:
    print("Missing support", file=sys.stderr)
    return lcurl.CURLcode(1).value


@curl_test_decorator
def test_lacks_necessary_function(URL: str, *args, **kwargs) -> lcurl.CURLcode:
    print("system lacks necessary system function(s)")
    return lcurl.CURLcode(1).value

# ------------------------------------------------------------------ #
