# **************************************************************************
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
# **************************************************************************

from dataclasses import dataclass
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

try:
    import resource
except ImportError:
    resource = None

    @curl_test_decorator
    def test(URL: str) -> lcurl.CURLcode:
        print("system lacks necessary system function(s)")
        return lcurl.CURLcode(1).value

else:

    if not defined("FD_SETSIZE"):
        print("this test requires FD_SETSIZE")
        sys.exit(-1)

    SAFETY_MARGIN = 16
    NUM_OPEN      = FD_SETSIZE + 10
    NUM_NEEDED    = NUM_OPEN + SAFETY_MARGIN

    @dataclass
    class struct_rlimit:
        rlim_cur: int
        rlim_max: int

    testfd: ct.POINTER(ct.c_int) = ct.POINTER(ct.c_int)()
    num_open: struct_rlimit  = struct_rlimit()

    errmsg: str = ""

    def store_errmsg(msg: str, err: int):
        global errmsg
        if not err:
            errmsg = "%s" % msg
        else:
            errmsg = "%s, errno %d, %s" % (msg, err, strerror(err))


    def clean_errmsg():
        global errmsg
        errmsg = ""


    def close_file_descriptors():
        num_open.rlim_cur = 0
        while num_open.rlim_cur < num_open.rlim_max:
            if testfd[num_open.rlim_cur] > 0:
                close(testfd[num_open.rlim_cur])
            num_open.rlim_cur += 1

        libc.free(testfd)
        testfd = NULL;


    def fopen_works() -> bool:
        ret = True

        fpa = [None] * 3
        for i in range(len(fpa)):
            try:
                fpa[i] = open(os.devnull, "rt" if is_windows else "r")
            except OSError as exc:
                store_errmsg("fopen failed", errno)
                print("%s" % errmsg, file=sys.stderr)
                ret = False
                break

        for fp in fpa:
            if fp: fp.close()

        return ret


    def rlim2str(val) -> str:
         # val: rlim_t
         return ("INFINITY" if (hasattr(resource, "RLIM_INFINITY") and
                                val == resource.RLIM_INFINITY) else "%lu" % val)


    def test_rlimit(keep_open: bool) -> int:

        memchunk: ct.POINTER(ct.c_int) = ct.POINTER(ct.c_int)()
        rl: struct_rlimit  = struct_rlimit()

        # get initial open file limits

        try:
            (rlim_cur, rlim_max) = resource.getrlimit(resource.RLIMIT_NOFILE)
        except Exception as exc:
            store_errmsg("resource.getrlimit() failed", errno)
            print("%s" % errmsg, file=sys.stderr)
            return -1

        # show initial open file limits

        msg = rlim2str(rl.rlim_cur)
        print("initial soft limit: %s" % msg, file=sys.stderr)

        rlim2str(rl.rlim_max)
        print("initial hard limit: %s" % msg, file=sys.stderr)

        # show our constants

        print("test518 FD_SETSIZE: %d" % FD_SETSIZE, file=sys.stderr)
        print("test518 NUM_OPEN  : %d" % NUM_OPEN,   file=sys.stderr)
        print("test518 NUM_NEEDED: %d" % NUM_NEEDED, file=sys.stderr)

        # if soft limit and hard limit are different we ask the
        # system to raise soft limit all the way up to the hard
        # limit. Due to some other system limit the soft limit
        # might not be raised up to the hard limit. So from this
        # point the resulting soft limit is our limit. Trying to
        # open more than soft limit file descriptors will fail.

        if rl.rlim_cur != rl.rlim_max:

            if "SC_OPEN_MAX" in os.sysconf_names:
                OPEN_MAX = os.sysconf("SC_OPEN_MAX")
                if OPEN_MAX != -1 and rl.rlim_cur > 0 and rl.rlim_cur < OPEN_MAX:
                    print("raising soft limit up to OPEN_MAX", file=sys.stderr)
                    rl.rlim_cur = OPEN_MAX
                    try:
                        resource.setrlimit(resource.RLIMIT_NOFILE, ((rlim_cur, rlim_max)))
                    except Exception as exc:
                        # on failure don't abort just issue a warning
                        store_errmsg("resource.setrlimit() failed", errno)
                        print("%s" % errmsg, file=sys.stderr)
                        clean_errmsg()

            print("raising soft limit up to hard limit", file=sys.stderr)
            rl.rlim_cur = rl.rlim_max;
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, ((rlim_cur, rlim_max)))
            except Exception as exc:
                # on failure don't abort just issue a warning
                store_errmsg("resource.setrlimit() failed", errno)
                print("%s" % errmsg, file=sys.stderr)
                clean_errmsg()

            # get current open file limits

            try:
                (rlim_cur, rlim_max) = resource.getrlimit(resource.RLIMIT_NOFILE)
            except Exception as exc:
                store_errmsg("resource.getrlimit() failed", errno)
                print("%s" % errmsg, file=sys.stderr)
                return -3

            # show current open file limits

            msg = rlim2str(rl.rlim_cur)
            print("current soft limit: %s" % msg, file=sys.stderr)

            rlim2str(rl.rlim_max)
            print("current hard limit: %s" % msg, file=sys.stderr)

        # test 518 is all about testing libcurl functionality
        # when more than FD_SETSIZE file descriptors are open.
        # This means that if for any reason we are not able to
        # open more than FD_SETSIZE file descriptors then test
        # 518 should not be run.

        # verify that soft limit is higher than NUM_NEEDED,
        # which is the number of file descriptors we would
        # try to open plus SAFETY_MARGIN to not exhaust the
        # file descriptor pool

        num_open.rlim_cur = NUM_NEEDED

        if (0 < rl.rlim_cur <= num_open.rlim_cur and (not hasattr(resource, "RLIM_INFINITY") or
                                                      rl.rlim_cur != resource.RLIM_INFINITY)):
            msg = "fds needed %s > system limit %s" % ((rlim2str(num_open.rlim_cur)),
                                                       (rlim2str(rl.rlim_cur)))
            store_errmsg(msg, 0)
            print("%s" % errmsg, file=sys.stderr)
            return -4

        # reserve a chunk of memory before opening file descriptors to
        # avoid a low memory condition once the file descriptors are
        # open. System conditions that could make the test fail should
        # be addressed in the precheck phase. This chunk of memory shall
        # be always free()ed before exiting the test_rlimit() function so
        # that it becomes available to the test.

        nitems = i = 1
        while nitems <= i:
            nitems = i
            i *= 2
        if nitems > 0x7fff:
            nitems = 0x40000
        while True:
            num_open.rlim_max = sizeof(*memchunk) * nitems
            msg = rlim2str(num_open.rlim_max)
            print("allocating memchunk %s byte array" % msg, file=sys.stderr)
            memchunk = libc.malloc(sizeof(*memchunk) * nitems)
            if memchunk: break
            print("memchunk, malloc() failed", file=sys.stderr)
            nitems //= 2
            if not nitems: break
        if not memchunk:
            store_errmsg("memchunk, malloc() failed", errno)
            print("%s" % errmsg, file=sys.stderr)
            return -5

        # initialize it to fight lazy allocation

        print("initializing memchunk array", file=sys.stderr)
        for i in range(nitems): memchunk[i] = -1

        # set the number of file descriptors we will try to open

        num_open.rlim_max = NUM_OPEN

        # verify that we won't overflow size_t in malloc()

        if ct.c_size_t(num_open.rlim_max).value > (ct.c_size_t(-1).value) / ct.sizeof(testfd[0]):
            msg = ("unable to allocate an array for %s file descriptors, "
                   "would overflow size_t") % (rlim2str(num_open.rlim_max))
            store_errmsg(msg, 0)
            print("%s" % errmsg, file=sys.stderr)
            libc.free(memchunk)
            return -6

        # allocate array for file descriptors

        msg = rlim2str(num_open.rlim_max)
        print("allocating array for %s file descriptors" % msg, file=sys.stderr)
        testfd = libc.malloc(ct.c_size_t(num_open.rlim_max).value * ct.sizeof(testfd[0]))
        if not testfd:
            store_errmsg("testfd, malloc() failed", errno)
            print("%s" % errmsg, file=sys.stderr)
            libc.free(memchunk)
            return -7

        # initialize it to fight lazy allocation

        print("initializing testfd array", file=sys.stderr)
        num_open.rlim_cur = 0
        while num_open.rlim_cur < num_open.rlim_max:
            testfd[num_open.rlim_cur] = -1
            num_open.rlim_cur += 1

        msg = rlim2str(num_open.rlim_max)
        print("trying to open %s file descriptors" % msg, file=sys.stderr)

        # open a dummy descriptor

        testfd[0] = open(os.devnull, os.O_RDONLY)
        if testfd[0] < 0:
            msg = "opening of %s failed" % os.devnull
            store_errmsg(msg, errno)
            print("%s" % errmsg, file=sys.stderr)
            libc.free(testfd)
            testfd = NULL;
            libc.free(memchunk)
            return -8

        # create a bunch of file descriptors

        num_open.rlim_cur = 1
        while num_open.rlim_cur < num_open.rlim_max:

            testfd[num_open.rlim_cur] = dup(testfd[0])

            if testfd[num_open.rlim_cur] < 0:

                testfd[num_open.rlim_cur] = -1

                msg = "dup() attempt %s failed" % (rlim2str(num_open.rlim_cur))
                print("%s" % msg, file=sys.stderr)

                msg = "fds system limit seems close to %s" % (rlim2str(num_open.rlim_cur))
                print("%s" % msg, file=sys.stderr)

                num_open.rlim_max = NUM_NEEDED

                msg = "fds needed %s > system limit %s" % ((rlim2str(num_open.rlim_max)),
                                                           (rlim2str(num_open.rlim_cur)))
                store_errmsg(msg, 0)
                print("%s" % errmsg, file=sys.stderr)

                num_open.rlim_cur = 0
                while testfd[num_open.rlim_cur] >= 0:
                    close(testfd[num_open.rlim_cur])
                    num_open.rlim_cur += 1

                libc.free(testfd)
                testfd = NULL;
                libc.free(memchunk)
                return -9

            num_open.rlim_cur += 1

        msg = rlim2str(num_open.rlim_max)
        print("%s file descriptors open" % msg, file=sys.stderr)

        if not defined("HAVE_POLL") and not defined("USE_WINSOCK"):

            # when using select() instead of poll() we cannot test
            # libcurl functionality with a socket number equal or
            # greater than FD_SETSIZE. In any case, macro VERIFY_SOCK
            # in lib/select.c enforces this check and protects libcurl
            # from a possible crash. The effect of this protection
            # is that test 518 will always fail, since the actual
            # call to select() never takes place. We skip test 518
            # with an indication that select limit would be exceeded.

            num_open.rlim_cur = FD_SETSIZE - SAFETY_MARGIN
            if num_open.rlim_max > num_open.rlim_cur:
                msg = "select limit is FD_SETSIZE %d" % FD_SETSIZE
                store_errmsg(msg, 0)
                print("%s" % errmsg, file=sys.stderr)
                close_file_descriptors()
                libc.free(memchunk)
                return -10

            num_open.rlim_cur = FD_SETSIZE - SAFETY_MARGIN
            rl.rlim_cur = 0
            while rl.rlim_cur < num_open.rlim_max:
                if testfd[rl.rlim_cur] > 0 and ct.c_uit(testfd[rl.rlim_cur]).value > num_open.rlim_cur:
                    msg = "select limit is FD_SETSIZE %d" % FD_SETSIZE
                    store_errmsg(msg, 0)
                    print("%s" % errmsg, file=sys.stderr)
                    close_file_descriptors()
                    libc.free(memchunk)
                    return -11

                rl.rlim_cur += 1

        #endif  # using a FD_SETSIZE bound select()

        # Old or 'backwards compatible' implementations of stdio do not allow
        # handling of streams with an underlying file descriptor number greater
        # than 255, even when allowing high numbered file descriptors for sockets.
        # At this point we have a big number of file descriptors which have been
        # opened using dup(), so lets test the stdio implementation and discover
        # if it is capable of open()ing some additional files.

        if not fopen_works():
            msg = "fopen fails with %s fds open" % (rlim2str(num_open.rlim_max))
            print("%s" % msg, file=sys.stderr)
            msg = "fopen fails with lots of fds open"
            store_errmsg(msg, 0)
            close_file_descriptors()
            libc.free(memchunk)
            return -12

        # free the chunk of memory we were reserving so that it
        # becomes available to the test

        libc.free(memchunk)

        # close file descriptors unless instructed to keep them

        if not keep_open:
            close_file_descriptors()

        return 0


    @curl_test_decorator
    def test(URL: str) -> lcurl.CURLcode:

        global errmsg

        if URL == "check":

            # used by the test script to ask if we can run this test or not
            if test_rlimit(keep_open=False):
                print("test_rlimit problem: %s" % errmsg, file=sys.stdout)
                return lcurl.CURLcode(1).value

            return lcurl.CURLE_OK  # sure, run this!

        else:

            res: lcurl.CURLcode

            if test_rlimit(keep_open=True):
                # failure
                return TEST_ERR_MAJOR_BAD

            # run the test with the bunch of open file descriptors
            # and close them all once the test is over

            if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
                close_file_descriptors()
                return TEST_ERR_MAJOR_BAD

            curl: ct.POINTER(lcurl.CURL) = easy_init()

            with curl_guard(True, curl) as guard:
                if not curl:
                    close_file_descriptors()
                    return TEST_ERR_EASY_INIT

                test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
                test_setopt(curl, lcurl.CURLOPT_HEADER, 1)

                res = lcurl.easy_perform(curl)

                # test_cleanup:

                close_file_descriptors()

            return res
