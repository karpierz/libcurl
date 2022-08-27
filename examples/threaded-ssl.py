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
Show the required mutex callback setups for GnuTLS and OpenSSL when using
libcurl multi-threaded.
"""

import sys
import ctypes as ct
import threading

import libcurl as lcurl
from curltestutils import *  # noqa


# A multi-threaded example that uses pthreads and fetches 4 remote files at
# once over HTTPS. The lock callbacks and stuff assume OpenSSL <1.1 or GnuTLS
# (libgcrypt) so far.
#
# OpenSSL docs for this:
#   https://www.openssl.org/docs/man1.0.2/man3/CRYPTO_num_locks.html
# gcrypt docs for this:
#   https://gnupg.org/documentation/manuals/gcrypt/Multi_002dThreading.html

# USE_OPENSSL = 1  # or USE_GNUTLS = 1 accordingly

if defined("USE_OPENSSL"):
    #include <openssl/crypto.h>

    """!!!
    # we have this global to let the callback get easy access to it
    pthread_mutex_t* lockarray;


    def init_locks():
        global lockarray

        lockarray = (pthread_mutex_t *)OPENSSL_malloc(CRYPTO_num_locks() *
                                                      sizeof(pthread_mutex_t))
        for i in range(CRYPTO_num_locks()):
            pthread_mutex_init(&(lockarray[i]), NULL)

        CRYPTO_set_id_callback((unsigned long (*)())thread_id)
        CRYPTO_set_locking_callback((void (*)())lock_callback)


    def kill_locks():
        global lockarray

        CRYPTO_set_locking_callback(NULL)

        for i in range(CRYPTO_num_locks()):
            pthread_mutex_destroy(&(lockarray[i]))

        OPENSSL_free(lockarray)


    def lock_callback(int mode, int type, char *file, int line)
        global lockarray

        if mode & CRYPTO_LOCK:
            pthread_mutex_lock(&(lockarray[type]))
        else:
            pthread_mutex_unlock(&(lockarray[type]))


    def thread_id() -> int: # -> unsigned long
        return (unsigned long)pthread_self()
    """


elif defined("USE_GNUTLS"):
    #include <gcrypt.h>
    #GCRY_THREAD_OPTION_PTHREAD_IMPL;

    init_locks = lambda: gcry_control(GCRYCTL_SET_THREAD_CBS)
    kill_locks = lambda: None

else:

    init_locks = lambda: None
    kill_locks = lambda: None


# List of URLs to fetch.
urls = [
    "https://www.example.com/",
    "https://www2.example.com/",
    "https://www3.example.com/",
    "https://www4.example.com/",
]


def pull_one_url(url: str):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        # this example does not verify the server's certificate,
        # which means we might be downloading stuff from an impostor
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

        # Perform the custom request
        lcurl.easy_perform(curl)  # ignores error


def main(argv=sys.argv[1:]):

    # Must initialize libcurl before any threads are started
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    with curl_guard(True):

        init_locks()
        try:
            threads = []
            for i, url in enumerate(urls):
                try:
                    thread = threading.Thread(target=pull_one_url, args=(url,))
                    thread.start()
                except Exception as exc:
                    print("Couldn't run thread number %d, error %s" % (i, exc),
                          file=sys.stderr)
                else:
                    threads.append(thread)
                    print("Thread %d, gets %s" % (i, url), file=sys.stderr)

            # now wait for all threads to terminate
            for i, thread in enumerate(threads):
                thread.join()
                print("Thread %d terminated" % i, file=sys.stderr)
        finally:
            kill_locks()

    return 0


sys.exit(main())
