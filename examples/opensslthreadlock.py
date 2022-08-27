#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 1998 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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
#***************************************************************************

"""
One way to set the necessary OpenSSL locking callbacks if you want to do
multi-threaded transfers with HTTPS/FTPS with libcurl built to use OpenSSL.
"""

import sys
import ctypes as ct
#include <openssl/err.h>

import libcurl as lcurl
from curltestutils import *  # noqa


# This is not a complete stand-alone example.
#
# Author: Jeremy Brown

#define MUTEX_TYPE       pthread_mutex_t
#define MUTEX_SETUP(x)   pthread_mutex_init(&(x), NULL)
#define MUTEX_CLEANUP(x) pthread_mutex_destroy(&(x))
#define MUTEX_LOCK(x)    pthread_mutex_lock(&(x))
#define MUTEX_UNLOCK(x)  pthread_mutex_unlock(&(x))
#define THREAD_ID        (unsigned long)pthread_self()


def handle_error(file: ct.c_char_p, lineno: int, msg: ct.c_char_p):
    print("** %s:%d %s" % (file, lineno, msg), file=sys.stderr)
    ERR_print_errors_fp(stderr)
    # exit(-1);


# This array will store all of the mutexes available to OpenSSL.
mutex_buf = None


def locking_function(mode: int, n: int, file: ct.c_char_p, line: int):
    global mutex_buf
    if mode & CRYPTO_LOCK:
        MUTEX_LOCK(mutex_buf[n])
    else:
        MUTEX_UNLOCK(mutex_buf[n])


def id_function() -> int: # -> unsigned long
    return THREAD_ID


def thread_setup() -> int:
    global mutex_buf
    mutex_buf = ct.cast(libc.malloc(CRYPTO_num_locks() * sizeof(MUTEX_TYPE)),
                        ct.POINTER(MUTEX_TYPE))
    if not mutex_buf:
        return 0
    for i in range(CRYPTO_num_locks()):
        MUTEX_SETUP(mutex_buf[i])
    CRYPTO_set_id_callback(id_function)
    CRYPTO_set_locking_callback(locking_function)
    return 1


def thread_cleanup() -> int:
    global mutex_buf
    if not mutex_buf:
        return 0
    CRYPTO_set_id_callback(NULL);
    CRYPTO_set_locking_callback(NULL);
    for i in range(CRYPTO_num_locks()):
        MUTEX_CLEANUP(mutex_buf[i])
    libc.free(mutex_buf)
    mutex_buf = None
    return 1
