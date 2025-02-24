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

import sys
import locale
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# The purpose of this test is to minimally exercise libcurl's internal
# curl_m*printf formatting capabilities and handling of some data types.

BUFSZ              = 256
USHORT_TESTS_ARRSZ = 1 + 100
SSHORT_TESTS_ARRSZ = 1 + 100
UINT_TESTS_ARRSZ   = 1 + 100
SINT_TESTS_ARRSZ   = 1 + 100
ULONG_TESTS_ARRSZ  = 1 + 100
SLONG_TESTS_ARRSZ  = 1 + 100
COFFT_TESTS_ARRSZ  = 1 + 100


class unsshort_st(ct.Structure):
    _fields_ = [
    ("num",      ct.c_ushort),          # unsigned short
    ("expected", ct.c_char_p),          # expected string
    ("result",   (ct.c_byte * BUFSZ)),  # result string
]

class sigshort_st(ct.Structure):
    _fields_ = [
    ("num",      ct.c_short),           # signed short
    ("expected", ct.c_char_p),          # expected string
    ("result",   (ct.c_byte * BUFSZ)),  # result string
]

class unsint_st(ct.Structure):
    _fields_ = [
    ("num",      ct.c_uint),            # unsigned int
    ("expected", ct.c_char_p),          # expected string
    ("result",   (ct.c_byte * BUFSZ)),  # result string
]

class sigint_st(ct.Structure):
    _fields_ = [
    ("num",      ct.c_int),             # signed int
    ("expected", ct.c_char_p),          # expected string
    ("result",   (ct.c_byte * BUFSZ)),  # result string
]

class unslong_st(ct.Structure):
    _fields_ = [
    ("num",      ct.c_ulong),           # unsigned long
    ("expected", ct.c_char_p),          # expected string
    ("result",   (ct.c_byte * BUFSZ)),  # result string
]

class siglong_st(ct.Structure):
    _fields_ = [
    ("num",      ct.c_long),            # signed long
    ("expected", ct.c_char_p),          # expected string
    ("result",   (ct.c_byte * BUFSZ)),  # result string
]

class curloff_st(ct.Structure):
    _fields_ = [
    ("num",      lcurl.off_t),          # libcurl.off_t
    ("expected", ct.c_char_p),          # expected string
    ("result",   (ct.c_byte * BUFSZ)),  # result string
]


us_test = (unsshort_st * USHORT_TESTS_ARRSZ)()
ss_test = (sigshort_st * SSHORT_TESTS_ARRSZ)()
ui_test = (unsint_st   * UINT_TESTS_ARRSZ)()
si_test = (sigint_st   * SINT_TESTS_ARRSZ)()
ul_test = (unslong_st  * ULONG_TESTS_ARRSZ)()
sl_test = (siglong_st  * SLONG_TESTS_ARRSZ)()
co_test = (curloff_st  * COFFT_TESTS_ARRSZ)()


def test_unsigned_short_formatting() -> int:

    num_ushort_tests: int = 0
    failed: int = 0

    i  = 1 ; us_test[i].num = 0xFFFF ; us_test[i].expected = b"65535"
    i += 1 ; us_test[i].num = 0xFF00 ; us_test[i].expected = b"65280"
    i += 1 ; us_test[i].num = 0x00FF ; us_test[i].expected = b"255"

    i += 1 ; us_test[i].num = 0xF000 ; us_test[i].expected = b"61440"
    i += 1 ; us_test[i].num = 0x0F00 ; us_test[i].expected = b"3840"
    i += 1 ; us_test[i].num = 0x00F0 ; us_test[i].expected = b"240"
    i += 1 ; us_test[i].num = 0x000F ; us_test[i].expected = b"15"

    i += 1 ; us_test[i].num = 0xC000 ; us_test[i].expected = b"49152"
    i += 1 ; us_test[i].num = 0x0C00 ; us_test[i].expected = b"3072"
    i += 1 ; us_test[i].num = 0x00C0 ; us_test[i].expected = b"192"
    i += 1 ; us_test[i].num = 0x000C ; us_test[i].expected = b"12"

    i += 1 ; us_test[i].num = 0x0001 ; us_test[i].expected = b"1"
    i += 1 ; us_test[i].num = 0x0000 ; us_test[i].expected = b"0"

    num_ushort_tests = i

    for i in range(1, num_ushort_tests + 1):

        ct.memset(us_test[i].result, ord(b'X'), BUFSZ)
        us_test[i].result[BUFSZ - 1] = ord(b'\0')

        for j, ch in enumerate(b"%hu" % us_test[i].num):
            us_test[i].result[j] = ch

        if bytes(us_test[i].result[:len(us_test[i].expected)]) != us_test[i].expected:
            print("unsigned short test #%.2d: Failed (Expected: %s Got: %s)" %
                  (i, us_test[i].expected, us_test[i].result))
            failed += 1

    if not failed:
        print("All libcurl.mprintf() unsigned short tests OK!")
    else:
        print("Some libcurl.mprintf() unsigned short tests Failed!")

    return failed


def test_signed_short_formatting() -> int:

    num_sshort_tests: int = 0
    failed: int = 0

    i  = 1 ; ss_test[i].num = 0x7FFF ; ss_test[i].expected = b"32767"
    i += 1 ; ss_test[i].num = 0x7FFE ; ss_test[i].expected = b"32766"
    i += 1 ; ss_test[i].num = 0x7FFD ; ss_test[i].expected = b"32765"
    i += 1 ; ss_test[i].num = 0x7F00 ; ss_test[i].expected = b"32512"
    i += 1 ; ss_test[i].num = 0x07F0 ; ss_test[i].expected = b"2032"
    i += 1 ; ss_test[i].num = 0x007F ; ss_test[i].expected = b"127"

    i += 1 ; ss_test[i].num = 0x7000 ; ss_test[i].expected = b"28672"
    i += 1 ; ss_test[i].num = 0x0700 ; ss_test[i].expected = b"1792"
    i += 1 ; ss_test[i].num = 0x0070 ; ss_test[i].expected = b"112"
    i += 1 ; ss_test[i].num = 0x0007 ; ss_test[i].expected = b"7"

    i += 1 ; ss_test[i].num = 0x5000 ; ss_test[i].expected = b"20480"
    i += 1 ; ss_test[i].num = 0x0500 ; ss_test[i].expected = b"1280"
    i += 1 ; ss_test[i].num = 0x0050 ; ss_test[i].expected = b"80"
    i += 1 ; ss_test[i].num = 0x0005 ; ss_test[i].expected = b"5"

    i += 1 ; ss_test[i].num = 0x0001 ; ss_test[i].expected = b"1"
    i += 1 ; ss_test[i].num = 0x0000 ; ss_test[i].expected = b"0"

    i += 1 ; ss_test[i].num = -0x7FFF - 1 ; ss_test[i].expected = b"-32768"
    i += 1 ; ss_test[i].num = -0x7FFE - 1 ; ss_test[i].expected = b"-32767"
    i += 1 ; ss_test[i].num = -0x7FFD - 1 ; ss_test[i].expected = b"-32766"
    i += 1 ; ss_test[i].num = -0x7F00 - 1 ; ss_test[i].expected = b"-32513"
    i += 1 ; ss_test[i].num = -0x07F0 - 1 ; ss_test[i].expected = b"-2033"
    i += 1 ; ss_test[i].num = -0x007F - 1 ; ss_test[i].expected = b"-128"

    i += 1 ; ss_test[i].num = -0x7000 - 1 ; ss_test[i].expected = b"-28673"
    i += 1 ; ss_test[i].num = -0x0700 - 1 ; ss_test[i].expected = b"-1793"
    i += 1 ; ss_test[i].num = -0x0070 - 1 ; ss_test[i].expected = b"-113"
    i += 1 ; ss_test[i].num = -0x0007 - 1 ; ss_test[i].expected = b"-8"

    i += 1 ; ss_test[i].num = -0x5000 - 1 ; ss_test[i].expected = b"-20481"
    i += 1 ; ss_test[i].num = -0x0500 - 1 ; ss_test[i].expected = b"-1281"
    i += 1 ; ss_test[i].num = -0x0050 - 1 ; ss_test[i].expected = b"-81"
    i += 1 ; ss_test[i].num = -0x0005 - 1 ; ss_test[i].expected = b"-6"

    i += 1 ; ss_test[i].num =  0x0000 - 1 ; ss_test[i].expected = b"-1"

    num_sshort_tests = i

    for i in range(1, num_sshort_tests + 1):

        ct.memset(ss_test[i].result, ord(b'X'), BUFSZ)
        ss_test[i].result[BUFSZ - 1] = ord(b'\0')

        for j, ch in enumerate(b"%hd" % ss_test[i].num):
            ss_test[i].result[j] = ch

        if bytes(ss_test[i].result[:len(ss_test[i].expected)]) != ss_test[i].expected:
            print("signed short test #%.2d: Failed (Expected: %s Got: %s)" %
                  (i, ss_test[i].expected, ss_test[i].result))
            failed += 1

    if not failed:
        print("All libcurl.mprintf() signed short tests OK!")
    else:
        print("Some libcurl.mprintf() signed short tests Failed!")

    return failed


def test_unsigned_int_formatting() -> int:

    num_uint_tests: int = 0
    failed: int = 0

    if ct.sizeof(ct.c_int) == 2:

        i  = 1 ; ui_test[i].num = 0xFFFF ; ui_test[i].expected = b"65535"
        i += 1 ; ui_test[i].num = 0xFF00 ; ui_test[i].expected = b"65280"
        i += 1 ; ui_test[i].num = 0x00FF ; ui_test[i].expected = b"255"

        i += 1 ; ui_test[i].num = 0xF000 ; ui_test[i].expected = b"61440"
        i += 1 ; ui_test[i].num = 0x0F00 ; ui_test[i].expected = b"3840"
        i += 1 ; ui_test[i].num = 0x00F0 ; ui_test[i].expected = b"240"
        i += 1 ; ui_test[i].num = 0x000F ; ui_test[i].expected = b"15"

        i += 1 ; ui_test[i].num = 0xC000 ; ui_test[i].expected = b"49152"
        i += 1 ; ui_test[i].num = 0x0C00 ; ui_test[i].expected = b"3072"
        i += 1 ; ui_test[i].num = 0x00C0 ; ui_test[i].expected = b"192"
        i += 1 ; ui_test[i].num = 0x000C ; ui_test[i].expected = b"12"

        i += 1 ; ui_test[i].num = 0x0001 ; ui_test[i].expected = b"1"
        i += 1 ; ui_test[i].num = 0x0000 ; ui_test[i].expected = b"0"

        num_uint_tests = i

    elif ct.sizeof(ct.c_int) == 4:

        i  = 1 ; ui_test[i].num = 0xFFFFFFFF ; ui_test[i].expected = b"4294967295"
        i += 1 ; ui_test[i].num = 0xFFFF0000 ; ui_test[i].expected = b"4294901760"
        i += 1 ; ui_test[i].num = 0x0000FFFF ; ui_test[i].expected = b"65535"

        i += 1 ; ui_test[i].num = 0xFF000000 ; ui_test[i].expected = b"4278190080"
        i += 1 ; ui_test[i].num = 0x00FF0000 ; ui_test[i].expected = b"16711680"
        i += 1 ; ui_test[i].num = 0x0000FF00 ; ui_test[i].expected = b"65280"
        i += 1 ; ui_test[i].num = 0x000000FF ; ui_test[i].expected = b"255"

        i += 1 ; ui_test[i].num = 0xF0000000 ; ui_test[i].expected = b"4026531840"
        i += 1 ; ui_test[i].num = 0x0F000000 ; ui_test[i].expected = b"251658240"
        i += 1 ; ui_test[i].num = 0x00F00000 ; ui_test[i].expected = b"15728640"
        i += 1 ; ui_test[i].num = 0x000F0000 ; ui_test[i].expected = b"983040"
        i += 1 ; ui_test[i].num = 0x0000F000 ; ui_test[i].expected = b"61440"
        i += 1 ; ui_test[i].num = 0x00000F00 ; ui_test[i].expected = b"3840"
        i += 1 ; ui_test[i].num = 0x000000F0 ; ui_test[i].expected = b"240"
        i += 1 ; ui_test[i].num = 0x0000000F ; ui_test[i].expected = b"15"

        i += 1 ; ui_test[i].num = 0xC0000000 ; ui_test[i].expected = b"3221225472"
        i += 1 ; ui_test[i].num = 0x0C000000 ; ui_test[i].expected = b"201326592"
        i += 1 ; ui_test[i].num = 0x00C00000 ; ui_test[i].expected = b"12582912"
        i += 1 ; ui_test[i].num = 0x000C0000 ; ui_test[i].expected = b"786432"
        i += 1 ; ui_test[i].num = 0x0000C000 ; ui_test[i].expected = b"49152"
        i += 1 ; ui_test[i].num = 0x00000C00 ; ui_test[i].expected = b"3072"
        i += 1 ; ui_test[i].num = 0x000000C0 ; ui_test[i].expected = b"192"
        i += 1 ; ui_test[i].num = 0x0000000C ; ui_test[i].expected = b"12"

        i += 1 ; ui_test[i].num = 0x00000001 ; ui_test[i].expected = b"1"
        i += 1 ; ui_test[i].num = 0x00000000 ; ui_test[i].expected = b"0"

        num_uint_tests = i

    elif ct.sizeof(ct.c_int) == 8:

        # !checksrc! disable LONGLINE all
        i  = 1 ; ui_test[i].num = 0xFFFFFFFFFFFFFFFF ; ui_test[i].expected = b"18446744073709551615"
        i += 1 ; ui_test[i].num = 0xFFFFFFFF00000000 ; ui_test[i].expected = b"18446744069414584320"
        i += 1 ; ui_test[i].num = 0x00000000FFFFFFFF ; ui_test[i].expected = b"4294967295"

        i += 1 ; ui_test[i].num = 0xFFFF000000000000 ; ui_test[i].expected = b"18446462598732840960"
        i += 1 ; ui_test[i].num = 0x0000FFFF00000000 ; ui_test[i].expected = b"281470681743360"
        i += 1 ; ui_test[i].num = 0x00000000FFFF0000 ; ui_test[i].expected = b"4294901760"
        i += 1 ; ui_test[i].num = 0x000000000000FFFF ; ui_test[i].expected = b"65535"

        i += 1 ; ui_test[i].num = 0xFF00000000000000 ; ui_test[i].expected = b"18374686479671623680"
        i += 1 ; ui_test[i].num = 0x00FF000000000000 ; ui_test[i].expected = b"71776119061217280"
        i += 1 ; ui_test[i].num = 0x0000FF0000000000 ; ui_test[i].expected = b"280375465082880"
        i += 1 ; ui_test[i].num = 0x000000FF00000000 ; ui_test[i].expected = b"1095216660480"
        i += 1 ; ui_test[i].num = 0x00000000FF000000 ; ui_test[i].expected = b"4278190080"
        i += 1 ; ui_test[i].num = 0x0000000000FF0000 ; ui_test[i].expected = b"16711680"
        i += 1 ; ui_test[i].num = 0x000000000000FF00 ; ui_test[i].expected = b"65280"
        i += 1 ; ui_test[i].num = 0x00000000000000FF ; ui_test[i].expected = b"255"

        i += 1 ; ui_test[i].num = 0xF000000000000000 ; ui_test[i].expected = b"17293822569102704640"
        i += 1 ; ui_test[i].num = 0x0F00000000000000 ; ui_test[i].expected = b"1080863910568919040"
        i += 1 ; ui_test[i].num = 0x00F0000000000000 ; ui_test[i].expected = b"67553994410557440"
        i += 1 ; ui_test[i].num = 0x000F000000000000 ; ui_test[i].expected = b"4222124650659840"
        i += 1 ; ui_test[i].num = 0x0000F00000000000 ; ui_test[i].expected = b"263882790666240"
        i += 1 ; ui_test[i].num = 0x00000F0000000000 ; ui_test[i].expected = b"16492674416640"
        i += 1 ; ui_test[i].num = 0x000000F000000000 ; ui_test[i].expected = b"1030792151040"
        i += 1 ; ui_test[i].num = 0x0000000F00000000 ; ui_test[i].expected = b"64424509440"
        i += 1 ; ui_test[i].num = 0x00000000F0000000 ; ui_test[i].expected = b"4026531840"
        i += 1 ; ui_test[i].num = 0x000000000F000000 ; ui_test[i].expected = b"251658240"
        i += 1 ; ui_test[i].num = 0x0000000000F00000 ; ui_test[i].expected = b"15728640"
        i += 1 ; ui_test[i].num = 0x00000000000F0000 ; ui_test[i].expected = b"983040"
        i += 1 ; ui_test[i].num = 0x000000000000F000 ; ui_test[i].expected = b"61440"
        i += 1 ; ui_test[i].num = 0x0000000000000F00 ; ui_test[i].expected = b"3840"
        i += 1 ; ui_test[i].num = 0x00000000000000F0 ; ui_test[i].expected = b"240"
        i += 1 ; ui_test[i].num = 0x000000000000000F ; ui_test[i].expected = b"15"

        i += 1 ; ui_test[i].num = 0xC000000000000000 ; ui_test[i].expected = b"13835058055282163712"
        i += 1 ; ui_test[i].num = 0x0C00000000000000 ; ui_test[i].expected = b"864691128455135232"
        i += 1 ; ui_test[i].num = 0x00C0000000000000 ; ui_test[i].expected = b"54043195528445952"
        i += 1 ; ui_test[i].num = 0x000C000000000000 ; ui_test[i].expected = b"3377699720527872"
        i += 1 ; ui_test[i].num = 0x0000C00000000000 ; ui_test[i].expected = b"211106232532992"
        i += 1 ; ui_test[i].num = 0x00000C0000000000 ; ui_test[i].expected = b"13194139533312"
        i += 1 ; ui_test[i].num = 0x000000C000000000 ; ui_test[i].expected = b"824633720832"
        i += 1 ; ui_test[i].num = 0x0000000C00000000 ; ui_test[i].expected = b"51539607552"
        i += 1 ; ui_test[i].num = 0x00000000C0000000 ; ui_test[i].expected = b"3221225472"
        i += 1 ; ui_test[i].num = 0x000000000C000000 ; ui_test[i].expected = b"201326592"
        i += 1 ; ui_test[i].num = 0x0000000000C00000 ; ui_test[i].expected = b"12582912"
        i += 1 ; ui_test[i].num = 0x00000000000C0000 ; ui_test[i].expected = b"786432"
        i += 1 ; ui_test[i].num = 0x000000000000C000 ; ui_test[i].expected = b"49152"
        i += 1 ; ui_test[i].num = 0x0000000000000C00 ; ui_test[i].expected = b"3072"
        i += 1 ; ui_test[i].num = 0x00000000000000C0 ; ui_test[i].expected = b"192"
        i += 1 ; ui_test[i].num = 0x000000000000000C ; ui_test[i].expected = b"12"

        i += 1 ; ui_test[i].num = 0x00000001 ; ui_test[i].expected = b"1"
        i += 1 ; ui_test[i].num = 0x00000000 ; ui_test[i].expected = b"0"

        num_uint_tests = i

    # endif

    for i in range(1, num_uint_tests + 1):

        ct.memset(ui_test[i].result, ord(b'X'), BUFSZ)
        ui_test[i].result[BUFSZ - 1] = ord(b'\0')

        for j, ch in enumerate(b"%d" % ui_test[i].num):
            ui_test[i].result[j] = ch

        if bytes(ui_test[i].result[:len(ui_test[i].expected)]) != ui_test[i].expected:
            print("unsigned int test #%.2d: Failed (Expected: %s Got: %s)" %
                  (i, ui_test[i].expected, ui_test[i].result))
            failed += 1

    if not failed:
        print("All libcurl.mprintf() unsigned int tests OK!")
    else:
        print("Some libcurl.mprintf() unsigned int tests Failed!")

    return failed


def test_signed_int_formatting() -> int:

    num_sint_tests: int = 0
    failed: int = 0

    if ct.sizeof(ct.c_int) == 2:

        i  = 1 ; si_test[i].num = 0x7FFF ; si_test[i].expected = b"32767"
        i += 1 ; si_test[i].num = 0x7FFE ; si_test[i].expected = b"32766"
        i += 1 ; si_test[i].num = 0x7FFD ; si_test[i].expected = b"32765"
        i += 1 ; si_test[i].num = 0x7F00 ; si_test[i].expected = b"32512"
        i += 1 ; si_test[i].num = 0x07F0 ; si_test[i].expected = b"2032"
        i += 1 ; si_test[i].num = 0x007F ; si_test[i].expected = b"127"

        i += 1 ; si_test[i].num = 0x7000 ; si_test[i].expected = b"28672"
        i += 1 ; si_test[i].num = 0x0700 ; si_test[i].expected = b"1792"
        i += 1 ; si_test[i].num = 0x0070 ; si_test[i].expected = b"112"
        i += 1 ; si_test[i].num = 0x0007 ; si_test[i].expected = b"7"

        i += 1 ; si_test[i].num = 0x5000 ; si_test[i].expected = b"20480"
        i += 1 ; si_test[i].num = 0x0500 ; si_test[i].expected = b"1280"
        i += 1 ; si_test[i].num = 0x0050 ; si_test[i].expected = b"80"
        i += 1 ; si_test[i].num = 0x0005 ; si_test[i].expected = b"5"

        i += 1 ; si_test[i].num = 0x0001 ; si_test[i].expected = b"1"
        i += 1 ; si_test[i].num = 0x0000 ; si_test[i].expected = b"0"

        i += 1 ; si_test[i].num = -0x7FFF - 1 ; si_test[i].expected = b"-32768"
        i += 1 ; si_test[i].num = -0x7FFE - 1 ; si_test[i].expected = b"-32767"
        i += 1 ; si_test[i].num = -0x7FFD - 1 ; si_test[i].expected = b"-32766"
        i += 1 ; si_test[i].num = -0x7F00 - 1 ; si_test[i].expected = b"-32513"
        i += 1 ; si_test[i].num = -0x07F0 - 1 ; si_test[i].expected = b"-2033"
        i += 1 ; si_test[i].num = -0x007F - 1 ; si_test[i].expected = b"-128"

        i += 1 ; si_test[i].num = -0x7000 - 1 ; si_test[i].expected = b"-28673"
        i += 1 ; si_test[i].num = -0x0700 - 1 ; si_test[i].expected = b"-1793"
        i += 1 ; si_test[i].num = -0x0070 - 1 ; si_test[i].expected = b"-113"
        i += 1 ; si_test[i].num = -0x0007 - 1 ; si_test[i].expected = b"-8"

        i += 1 ; si_test[i].num = -0x5000 - 1 ; si_test[i].expected = b"-20481"
        i += 1 ; si_test[i].num = -0x0500 - 1 ; si_test[i].expected = b"-1281"
        i += 1 ; si_test[i].num = -0x0050 - 1 ; si_test[i].expected = b"-81"
        i += 1 ; si_test[i].num = -0x0005 - 1 ; si_test[i].expected = b"-6"

        i += 1 ; si_test[i].num =  0x0000 - 1 ; si_test[i].expected = b"-1"

        num_sint_tests = i

    elif ct.sizeof(ct.c_int) == 4:

        i  = 1 ; si_test[i].num = 0x7FFFFFFF ; si_test[i].expected = b"2147483647"
        i += 1 ; si_test[i].num = 0x7FFFFFFE ; si_test[i].expected = b"2147483646"
        i += 1 ; si_test[i].num = 0x7FFFFFFD ; si_test[i].expected = b"2147483645"
        i += 1 ; si_test[i].num = 0x7FFF0000 ; si_test[i].expected = b"2147418112"
        i += 1 ; si_test[i].num = 0x00007FFF ; si_test[i].expected = b"32767"

        i += 1 ; si_test[i].num = 0x7F000000 ; si_test[i].expected = b"2130706432"
        i += 1 ; si_test[i].num = 0x007F0000 ; si_test[i].expected = b"8323072"
        i += 1 ; si_test[i].num = 0x00007F00 ; si_test[i].expected = b"32512"
        i += 1 ; si_test[i].num = 0x0000007F ; si_test[i].expected = b"127"

        i += 1 ; si_test[i].num = 0x70000000 ; si_test[i].expected = b"1879048192"
        i += 1 ; si_test[i].num = 0x07000000 ; si_test[i].expected = b"117440512"
        i += 1 ; si_test[i].num = 0x00700000 ; si_test[i].expected = b"7340032"
        i += 1 ; si_test[i].num = 0x00070000 ; si_test[i].expected = b"458752"
        i += 1 ; si_test[i].num = 0x00007000 ; si_test[i].expected = b"28672"
        i += 1 ; si_test[i].num = 0x00000700 ; si_test[i].expected = b"1792"
        i += 1 ; si_test[i].num = 0x00000070 ; si_test[i].expected = b"112"
        i += 1 ; si_test[i].num = 0x00000007 ; si_test[i].expected = b"7"

        i += 1 ; si_test[i].num = 0x50000000 ; si_test[i].expected = b"1342177280"
        i += 1 ; si_test[i].num = 0x05000000 ; si_test[i].expected = b"83886080"
        i += 1 ; si_test[i].num = 0x00500000 ; si_test[i].expected = b"5242880"
        i += 1 ; si_test[i].num = 0x00050000 ; si_test[i].expected = b"327680"
        i += 1 ; si_test[i].num = 0x00005000 ; si_test[i].expected = b"20480"
        i += 1 ; si_test[i].num = 0x00000500 ; si_test[i].expected = b"1280"
        i += 1 ; si_test[i].num = 0x00000050 ; si_test[i].expected = b"80"
        i += 1 ; si_test[i].num = 0x00000005 ; si_test[i].expected = b"5"

        i += 1 ; si_test[i].num = 0x00000001 ; si_test[i].expected = b"1"
        i += 1 ; si_test[i].num = 0x00000000 ; si_test[i].expected = b"0"

        i += 1 ; si_test[i].num = -0x7FFFFFFF - 1 ; si_test[i].expected = b"-2147483648"
        i += 1 ; si_test[i].num = -0x7FFFFFFE - 1 ; si_test[i].expected = b"-2147483647"
        i += 1 ; si_test[i].num = -0x7FFFFFFD - 1 ; si_test[i].expected = b"-2147483646"
        i += 1 ; si_test[i].num = -0x7FFF0000 - 1 ; si_test[i].expected = b"-2147418113"
        i += 1 ; si_test[i].num = -0x00007FFF - 1 ; si_test[i].expected = b"-32768"

        i += 1 ; si_test[i].num = -0x7F000000 - 1 ; si_test[i].expected = b"-2130706433"
        i += 1 ; si_test[i].num = -0x007F0000 - 1 ; si_test[i].expected = b"-8323073"
        i += 1 ; si_test[i].num = -0x00007F00 - 1 ; si_test[i].expected = b"-32513"
        i += 1 ; si_test[i].num = -0x0000007F - 1 ; si_test[i].expected = b"-128"

        i += 1 ; si_test[i].num = -0x70000000 - 1 ; si_test[i].expected = b"-1879048193"
        i += 1 ; si_test[i].num = -0x07000000 - 1 ; si_test[i].expected = b"-117440513"
        i += 1 ; si_test[i].num = -0x00700000 - 1 ; si_test[i].expected = b"-7340033"
        i += 1 ; si_test[i].num = -0x00070000 - 1 ; si_test[i].expected = b"-458753"
        i += 1 ; si_test[i].num = -0x00007000 - 1 ; si_test[i].expected = b"-28673"
        i += 1 ; si_test[i].num = -0x00000700 - 1 ; si_test[i].expected = b"-1793"
        i += 1 ; si_test[i].num = -0x00000070 - 1 ; si_test[i].expected = b"-113"
        i += 1 ; si_test[i].num = -0x00000007 - 1 ; si_test[i].expected = b"-8"

        i += 1 ; si_test[i].num = -0x50000000 - 1 ; si_test[i].expected = b"-1342177281"
        i += 1 ; si_test[i].num = -0x05000000 - 1 ; si_test[i].expected = b"-83886081"
        i += 1 ; si_test[i].num = -0x00500000 - 1 ; si_test[i].expected = b"-5242881"
        i += 1 ; si_test[i].num = -0x00050000 - 1 ; si_test[i].expected = b"-327681"
        i += 1 ; si_test[i].num = -0x00005000 - 1 ; si_test[i].expected = b"-20481"
        i += 1 ; si_test[i].num = -0x00000500 - 1 ; si_test[i].expected = b"-1281"
        i += 1 ; si_test[i].num = -0x00000050 - 1 ; si_test[i].expected = b"-81"
        i += 1 ; si_test[i].num = -0x00000005 - 1 ; si_test[i].expected = b"-6"

        i += 1 ; si_test[i].num =  0x00000000 - 1 ; si_test[i].expected = b"-1"

        num_sint_tests = i

    elif ct.sizeof(ct.c_int) == 8:

        i  = 1 ; si_test[i].num = 0x7FFFFFFFFFFFFFFF ; si_test[i].expected = b"9223372036854775807"
        i += 1 ; si_test[i].num = 0x7FFFFFFFFFFFFFFE ; si_test[i].expected = b"9223372036854775806"
        i += 1 ; si_test[i].num = 0x7FFFFFFFFFFFFFFD ; si_test[i].expected = b"9223372036854775805"
        i += 1 ; si_test[i].num = 0x7FFFFFFF00000000 ; si_test[i].expected = b"9223372032559808512"
        i += 1 ; si_test[i].num = 0x000000007FFFFFFF ; si_test[i].expected = b"2147483647"

        i += 1 ; si_test[i].num = 0x7FFF000000000000 ; si_test[i].expected = b"9223090561878065152"
        i += 1 ; si_test[i].num = 0x00007FFF00000000 ; si_test[i].expected = b"140733193388032"
        i += 1 ; si_test[i].num = 0x000000007FFF0000 ; si_test[i].expected = b"2147418112"
        i += 1 ; si_test[i].num = 0x0000000000007FFF ; si_test[i].expected = b"32767"

        i += 1 ; si_test[i].num = 0x7F00000000000000 ; si_test[i].expected = b"9151314442816847872"
        i += 1 ; si_test[i].num = 0x007F000000000000 ; si_test[i].expected = b"35747322042253312"
        i += 1 ; si_test[i].num = 0x00007F0000000000 ; si_test[i].expected = b"139637976727552"
        i += 1 ; si_test[i].num = 0x0000007F00000000 ; si_test[i].expected = b"545460846592"
        i += 1 ; si_test[i].num = 0x000000007F000000 ; si_test[i].expected = b"2130706432"
        i += 1 ; si_test[i].num = 0x00000000007F0000 ; si_test[i].expected = b"8323072"
        i += 1 ; si_test[i].num = 0x0000000000007F00 ; si_test[i].expected = b"32512"
        i += 1 ; si_test[i].num = 0x000000000000007F ; si_test[i].expected = b"127"

        i += 1 ; si_test[i].num = 0x7000000000000000 ; si_test[i].expected = b"8070450532247928832"
        i += 1 ; si_test[i].num = 0x0700000000000000 ; si_test[i].expected = b"504403158265495552"
        i += 1 ; si_test[i].num = 0x0070000000000000 ; si_test[i].expected = b"31525197391593472"
        i += 1 ; si_test[i].num = 0x0007000000000000 ; si_test[i].expected = b"1970324836974592"
        i += 1 ; si_test[i].num = 0x0000700000000000 ; si_test[i].expected = b"123145302310912"
        i += 1 ; si_test[i].num = 0x0000070000000000 ; si_test[i].expected = b"7696581394432"
        i += 1 ; si_test[i].num = 0x0000007000000000 ; si_test[i].expected = b"481036337152"
        i += 1 ; si_test[i].num = 0x0000000700000000 ; si_test[i].expected = b"30064771072"
        i += 1 ; si_test[i].num = 0x0000000070000000 ; si_test[i].expected = b"1879048192"
        i += 1 ; si_test[i].num = 0x0000000007000000 ; si_test[i].expected = b"117440512"
        i += 1 ; si_test[i].num = 0x0000000000700000 ; si_test[i].expected = b"7340032"
        i += 1 ; si_test[i].num = 0x0000000000070000 ; si_test[i].expected = b"458752"
        i += 1 ; si_test[i].num = 0x0000000000007000 ; si_test[i].expected = b"28672"
        i += 1 ; si_test[i].num = 0x0000000000000700 ; si_test[i].expected = b"1792"
        i += 1 ; si_test[i].num = 0x0000000000000070 ; si_test[i].expected = b"112"
        i += 1 ; si_test[i].num = 0x0000000000000007 ; si_test[i].expected = b"7"

        i += 1 ; si_test[i].num = 0x0000000000000001 ; si_test[i].expected = b"1"
        i += 1 ; si_test[i].num = 0x0000000000000000 ; si_test[i].expected = b"0"

        i += 1 ; si_test[i].num = -0x7FFFFFFFFFFFFFFF - 1 ; si_test[i].expected = b"-9223372036854775808"
        i += 1 ; si_test[i].num = -0x7FFFFFFFFFFFFFFE - 1 ; si_test[i].expected = b"-9223372036854775807"
        i += 1 ; si_test[i].num = -0x7FFFFFFFFFFFFFFD - 1 ; si_test[i].expected = b"-9223372036854775806"
        i += 1 ; si_test[i].num = -0x7FFFFFFF00000000 - 1 ; si_test[i].expected = b"-9223372032559808513"
        i += 1 ; si_test[i].num = -0x000000007FFFFFFF - 1 ; si_test[i].expected = b"-2147483648"

        i += 1 ; si_test[i].num = -0x7FFF000000000000 - 1 ; si_test[i].expected = b"-9223090561878065153"
        i += 1 ; si_test[i].num = -0x00007FFF00000000 - 1 ; si_test[i].expected = b"-140733193388033"
        i += 1 ; si_test[i].num = -0x000000007FFF0000 - 1 ; si_test[i].expected = b"-2147418113"
        i += 1 ; si_test[i].num = -0x0000000000007FFF - 1 ; si_test[i].expected = b"-32768"

        i += 1 ; si_test[i].num = -0x7F00000000000000 - 1 ; si_test[i].expected = b"-9151314442816847873"
        i += 1 ; si_test[i].num = -0x007F000000000000 - 1 ; si_test[i].expected = b"-35747322042253313"
        i += 1 ; si_test[i].num = -0x00007F0000000000 - 1 ; si_test[i].expected = b"-139637976727553"
        i += 1 ; si_test[i].num = -0x0000007F00000000 - 1 ; si_test[i].expected = b"-545460846593"
        i += 1 ; si_test[i].num = -0x000000007F000000 - 1 ; si_test[i].expected = b"-2130706433"
        i += 1 ; si_test[i].num = -0x00000000007F0000 - 1 ; si_test[i].expected = b"-8323073"
        i += 1 ; si_test[i].num = -0x0000000000007F00 - 1 ; si_test[i].expected = b"-32513"
        i += 1 ; si_test[i].num = -0x000000000000007F - 1 ; si_test[i].expected = b"-128"

        i += 1 ; si_test[i].num = -0x7000000000000000 - 1 ; si_test[i].expected = b"-8070450532247928833"
        i += 1 ; si_test[i].num = -0x0700000000000000 - 1 ; si_test[i].expected = b"-504403158265495553"
        i += 1 ; si_test[i].num = -0x0070000000000000 - 1 ; si_test[i].expected = b"-31525197391593473"
        i += 1 ; si_test[i].num = -0x0007000000000000 - 1 ; si_test[i].expected = b"-1970324836974593"
        i += 1 ; si_test[i].num = -0x0000700000000000 - 1 ; si_test[i].expected = b"-123145302310913"
        i += 1 ; si_test[i].num = -0x0000070000000000 - 1 ; si_test[i].expected = b"-7696581394433"
        i += 1 ; si_test[i].num = -0x0000007000000000 - 1 ; si_test[i].expected = b"-481036337153"
        i += 1 ; si_test[i].num = -0x0000000700000000 - 1 ; si_test[i].expected = b"-30064771073"
        i += 1 ; si_test[i].num = -0x0000000070000000 - 1 ; si_test[i].expected = b"-1879048193"
        i += 1 ; si_test[i].num = -0x0000000007000000 - 1 ; si_test[i].expected = b"-117440513"
        i += 1 ; si_test[i].num = -0x0000000000700000 - 1 ; si_test[i].expected = b"-7340033"
        i += 1 ; si_test[i].num = -0x0000000000070000 - 1 ; si_test[i].expected = b"-458753"
        i += 1 ; si_test[i].num = -0x0000000000007000 - 1 ; si_test[i].expected = b"-28673"
        i += 1 ; si_test[i].num = -0x0000000000000700 - 1 ; si_test[i].expected = b"-1793"
        i += 1 ; si_test[i].num = -0x0000000000000070 - 1 ; si_test[i].expected = b"-113"
        i += 1 ; si_test[i].num = -0x0000000000000007 - 1 ; si_test[i].expected = b"-8"

        i += 1 ; si_test[i].num =  0x0000000000000000 - 1 ; si_test[i].expected = b"-1"

        num_sint_tests = i

    # endif

    for i in range(1, num_sint_tests + 1):

        ct.memset(si_test[i].result, ord(b'X'), BUFSZ)
        si_test[i].result[BUFSZ - 1] = ord(b'\0')

        for j, ch in enumerate(b"%d" % si_test[i].num):
            si_test[i].result[j] = ch

        if bytes(si_test[i].result[:len(si_test[i].expected)]) != si_test[i].expected:
            print("signed int test #%.2d: Failed (Expected: %s Got: %s)" %
                  (i, si_test[i].expected, si_test[i].result))
            failed += 1

    if not failed:
        print("All libcurl.mprintf() signed int tests OK!")
    else:
        print("Some libcurl.mprintf() signed int tests Failed!")

    return failed


def test_unsigned_long_formatting() -> int:

    num_ulong_tests: int = 0
    failed: int = 0

    if ct.sizeof(ct.c_long) == 2:

        i  = 1 ; ul_test[i].num = 0xFFFF ; ul_test[i].expected = b"65535"
        i += 1 ; ul_test[i].num = 0xFF00 ; ul_test[i].expected = b"65280"
        i += 1 ; ul_test[i].num = 0x00FF ; ul_test[i].expected = b"255"

        i += 1 ; ul_test[i].num = 0xF000 ; ul_test[i].expected = b"61440"
        i += 1 ; ul_test[i].num = 0x0F00 ; ul_test[i].expected = b"3840"
        i += 1 ; ul_test[i].num = 0x00F0 ; ul_test[i].expected = b"240"
        i += 1 ; ul_test[i].num = 0x000F ; ul_test[i].expected = b"15"

        i += 1 ; ul_test[i].num = 0xC000 ; ul_test[i].expected = b"49152"
        i += 1 ; ul_test[i].num = 0x0C00 ; ul_test[i].expected = b"3072"
        i += 1 ; ul_test[i].num = 0x00C0 ; ul_test[i].expected = b"192"
        i += 1 ; ul_test[i].num = 0x000C ; ul_test[i].expected = b"12"

        i += 1 ; ul_test[i].num = 0x0001 ; ul_test[i].expected = b"1"
        i += 1 ; ul_test[i].num = 0x0000 ; ul_test[i].expected = b"0"

        num_ulong_tests = i

    elif ct.sizeof(ct.c_long) == 4:

        i  = 1 ; ul_test[i].num = 0xFFFFFFFF ; ul_test[i].expected = b"4294967295"
        i += 1 ; ul_test[i].num = 0xFFFF0000 ; ul_test[i].expected = b"4294901760"
        i += 1 ; ul_test[i].num = 0x0000FFFF ; ul_test[i].expected = b"65535"

        i += 1 ; ul_test[i].num = 0xFF000000 ; ul_test[i].expected = b"4278190080"
        i += 1 ; ul_test[i].num = 0x00FF0000 ; ul_test[i].expected = b"16711680"
        i += 1 ; ul_test[i].num = 0x0000FF00 ; ul_test[i].expected = b"65280"
        i += 1 ; ul_test[i].num = 0x000000FF ; ul_test[i].expected = b"255"

        i += 1 ; ul_test[i].num = 0xF0000000 ; ul_test[i].expected = b"4026531840"
        i += 1 ; ul_test[i].num = 0x0F000000 ; ul_test[i].expected = b"251658240"
        i += 1 ; ul_test[i].num = 0x00F00000 ; ul_test[i].expected = b"15728640"
        i += 1 ; ul_test[i].num = 0x000F0000 ; ul_test[i].expected = b"983040"
        i += 1 ; ul_test[i].num = 0x0000F000 ; ul_test[i].expected = b"61440"
        i += 1 ; ul_test[i].num = 0x00000F00 ; ul_test[i].expected = b"3840"
        i += 1 ; ul_test[i].num = 0x000000F0 ; ul_test[i].expected = b"240"
        i += 1 ; ul_test[i].num = 0x0000000F ; ul_test[i].expected = b"15"

        i += 1 ; ul_test[i].num = 0xC0000000 ; ul_test[i].expected = b"3221225472"
        i += 1 ; ul_test[i].num = 0x0C000000 ; ul_test[i].expected = b"201326592"
        i += 1 ; ul_test[i].num = 0x00C00000 ; ul_test[i].expected = b"12582912"
        i += 1 ; ul_test[i].num = 0x000C0000 ; ul_test[i].expected = b"786432"
        i += 1 ; ul_test[i].num = 0x0000C000 ; ul_test[i].expected = b"49152"
        i += 1 ; ul_test[i].num = 0x00000C00 ; ul_test[i].expected = b"3072"
        i += 1 ; ul_test[i].num = 0x000000C0 ; ul_test[i].expected = b"192"
        i += 1 ; ul_test[i].num = 0x0000000C ; ul_test[i].expected = b"12"

        i += 1 ; ul_test[i].num = 0x00000001 ; ul_test[i].expected = b"1"
        i += 1 ; ul_test[i].num = 0x00000000 ; ul_test[i].expected = b"0"

        num_ulong_tests = i

    elif ct.sizeof(ct.c_long) == 8:

        i  = 1 ; ul_test[i].num = 0xFFFFFFFFFFFFFFFF ; ul_test[i].expected = b"18446744073709551615"
        i += 1 ; ul_test[i].num = 0xFFFFFFFF00000000 ; ul_test[i].expected = b"18446744069414584320"
        i += 1 ; ul_test[i].num = 0x00000000FFFFFFFF ; ul_test[i].expected = b"4294967295"

        i += 1 ; ul_test[i].num = 0xFFFF000000000000 ; ul_test[i].expected = b"18446462598732840960"
        i += 1 ; ul_test[i].num = 0x0000FFFF00000000 ; ul_test[i].expected = b"281470681743360"
        i += 1 ; ul_test[i].num = 0x00000000FFFF0000 ; ul_test[i].expected = b"4294901760"
        i += 1 ; ul_test[i].num = 0x000000000000FFFF ; ul_test[i].expected = b"65535"

        i += 1 ; ul_test[i].num = 0xFF00000000000000 ; ul_test[i].expected = b"18374686479671623680"
        i += 1 ; ul_test[i].num = 0x00FF000000000000 ; ul_test[i].expected = b"71776119061217280"
        i += 1 ; ul_test[i].num = 0x0000FF0000000000 ; ul_test[i].expected = b"280375465082880"
        i += 1 ; ul_test[i].num = 0x000000FF00000000 ; ul_test[i].expected = b"1095216660480"
        i += 1 ; ul_test[i].num = 0x00000000FF000000 ; ul_test[i].expected = b"4278190080"
        i += 1 ; ul_test[i].num = 0x0000000000FF0000 ; ul_test[i].expected = b"16711680"
        i += 1 ; ul_test[i].num = 0x000000000000FF00 ; ul_test[i].expected = b"65280"
        i += 1 ; ul_test[i].num = 0x00000000000000FF ; ul_test[i].expected = b"255"

        i += 1 ; ul_test[i].num = 0xF000000000000000 ; ul_test[i].expected = b"17293822569102704640"
        i += 1 ; ul_test[i].num = 0x0F00000000000000 ; ul_test[i].expected = b"1080863910568919040"
        i += 1 ; ul_test[i].num = 0x00F0000000000000 ; ul_test[i].expected = b"67553994410557440"
        i += 1 ; ul_test[i].num = 0x000F000000000000 ; ul_test[i].expected = b"4222124650659840"
        i += 1 ; ul_test[i].num = 0x0000F00000000000 ; ul_test[i].expected = b"263882790666240"
        i += 1 ; ul_test[i].num = 0x00000F0000000000 ; ul_test[i].expected = b"16492674416640"
        i += 1 ; ul_test[i].num = 0x000000F000000000 ; ul_test[i].expected = b"1030792151040"
        i += 1 ; ul_test[i].num = 0x0000000F00000000 ; ul_test[i].expected = b"64424509440"
        i += 1 ; ul_test[i].num = 0x00000000F0000000 ; ul_test[i].expected = b"4026531840"
        i += 1 ; ul_test[i].num = 0x000000000F000000 ; ul_test[i].expected = b"251658240"
        i += 1 ; ul_test[i].num = 0x0000000000F00000 ; ul_test[i].expected = b"15728640"
        i += 1 ; ul_test[i].num = 0x00000000000F0000 ; ul_test[i].expected = b"983040"
        i += 1 ; ul_test[i].num = 0x000000000000F000 ; ul_test[i].expected = b"61440"
        i += 1 ; ul_test[i].num = 0x0000000000000F00 ; ul_test[i].expected = b"3840"
        i += 1 ; ul_test[i].num = 0x00000000000000F0 ; ul_test[i].expected = b"240"
        i += 1 ; ul_test[i].num = 0x000000000000000F ; ul_test[i].expected = b"15"

        i += 1 ; ul_test[i].num = 0xC000000000000000 ; ul_test[i].expected = b"13835058055282163712"
        i += 1 ; ul_test[i].num = 0x0C00000000000000 ; ul_test[i].expected = b"864691128455135232"
        i += 1 ; ul_test[i].num = 0x00C0000000000000 ; ul_test[i].expected = b"54043195528445952"
        i += 1 ; ul_test[i].num = 0x000C000000000000 ; ul_test[i].expected = b"3377699720527872"
        i += 1 ; ul_test[i].num = 0x0000C00000000000 ; ul_test[i].expected = b"211106232532992"
        i += 1 ; ul_test[i].num = 0x00000C0000000000 ; ul_test[i].expected = b"13194139533312"
        i += 1 ; ul_test[i].num = 0x000000C000000000 ; ul_test[i].expected = b"824633720832"
        i += 1 ; ul_test[i].num = 0x0000000C00000000 ; ul_test[i].expected = b"51539607552"
        i += 1 ; ul_test[i].num = 0x00000000C0000000 ; ul_test[i].expected = b"3221225472"
        i += 1 ; ul_test[i].num = 0x000000000C000000 ; ul_test[i].expected = b"201326592"
        i += 1 ; ul_test[i].num = 0x0000000000C00000 ; ul_test[i].expected = b"12582912"
        i += 1 ; ul_test[i].num = 0x00000000000C0000 ; ul_test[i].expected = b"786432"
        i += 1 ; ul_test[i].num = 0x000000000000C000 ; ul_test[i].expected = b"49152"
        i += 1 ; ul_test[i].num = 0x0000000000000C00 ; ul_test[i].expected = b"3072"
        i += 1 ; ul_test[i].num = 0x00000000000000C0 ; ul_test[i].expected = b"192"
        i += 1 ; ul_test[i].num = 0x000000000000000C ; ul_test[i].expected = b"12"

        i += 1 ; ul_test[i].num = 0x00000001 ; ul_test[i].expected = b"1"
        i += 1 ; ul_test[i].num = 0x00000000 ; ul_test[i].expected = b"0"

        num_ulong_tests = i

    # endif

    for i in range(1, num_ulong_tests + 1):

        ct.memset(ul_test[i].result, ord(b'X'), BUFSZ)
        ul_test[i].result[BUFSZ - 1] = ord(b'\0')

        for j, ch in enumerate(b"%lu" % ul_test[i].num):
            ul_test[i].result[j] = ch

        if bytes(ul_test[i].result[:len(ul_test[i].expected)]) != ul_test[i].expected:
            print("unsigned long test #%.2d: Failed (Expected: %s Got: %s)" %
                  (i, ul_test[i].expected, ul_test[i].result))
            failed += 1

    if not failed:
        print("All libcurl.mprintf() unsigned long tests OK!")
    else:
        print("Some libcurl.mprintf() unsigned long tests Failed!")

    return failed


def test_signed_long_formatting() -> int:

    num_slong_tests: int = 0
    failed: int = 0

    if ct.sizeof(ct.c_long) == 2:

        i  = 1 ; sl_test[i].num = 0x7FFF ; sl_test[i].expected = b"32767"
        i += 1 ; sl_test[i].num = 0x7FFE ; sl_test[i].expected = b"32766"
        i += 1 ; sl_test[i].num = 0x7FFD ; sl_test[i].expected = b"32765"
        i += 1 ; sl_test[i].num = 0x7F00 ; sl_test[i].expected = b"32512"
        i += 1 ; sl_test[i].num = 0x07F0 ; sl_test[i].expected = b"2032"
        i += 1 ; sl_test[i].num = 0x007F ; sl_test[i].expected = b"127"

        i += 1 ; sl_test[i].num = 0x7000 ; sl_test[i].expected = b"28672"
        i += 1 ; sl_test[i].num = 0x0700 ; sl_test[i].expected = b"1792"
        i += 1 ; sl_test[i].num = 0x0070 ; sl_test[i].expected = b"112"
        i += 1 ; sl_test[i].num = 0x0007 ; sl_test[i].expected = b"7"

        i += 1 ; sl_test[i].num = 0x5000 ; sl_test[i].expected = b"20480"
        i += 1 ; sl_test[i].num = 0x0500 ; sl_test[i].expected = b"1280"
        i += 1 ; sl_test[i].num = 0x0050 ; sl_test[i].expected = b"80"
        i += 1 ; sl_test[i].num = 0x0005 ; sl_test[i].expected = b"5"

        i += 1 ; sl_test[i].num = 0x0001 ; sl_test[i].expected = b"1"
        i += 1 ; sl_test[i].num = 0x0000 ; sl_test[i].expected = b"0"

        i += 1 ; sl_test[i].num = -0x7FFF - 1 ; sl_test[i].expected = b"-32768"
        i += 1 ; sl_test[i].num = -0x7FFE - 1 ; sl_test[i].expected = b"-32767"
        i += 1 ; sl_test[i].num = -0x7FFD - 1 ; sl_test[i].expected = b"-32766"
        i += 1 ; sl_test[i].num = -0x7F00 - 1 ; sl_test[i].expected = b"-32513"
        i += 1 ; sl_test[i].num = -0x07F0 - 1 ; sl_test[i].expected = b"-2033"
        i += 1 ; sl_test[i].num = -0x007F - 1 ; sl_test[i].expected = b"-128"

        i += 1 ; sl_test[i].num = -0x7000 - 1 ; sl_test[i].expected = b"-28673"
        i += 1 ; sl_test[i].num = -0x0700 - 1 ; sl_test[i].expected = b"-1793"
        i += 1 ; sl_test[i].num = -0x0070 - 1 ; sl_test[i].expected = b"-113"
        i += 1 ; sl_test[i].num = -0x0007 - 1 ; sl_test[i].expected = b"-8"

        i += 1 ; sl_test[i].num = -0x5000 - 1 ; sl_test[i].expected = b"-20481"
        i += 1 ; sl_test[i].num = -0x0500 - 1 ; sl_test[i].expected = b"-1281"
        i += 1 ; sl_test[i].num = -0x0050 - 1 ; sl_test[i].expected = b"-81"
        i += 1 ; sl_test[i].num = -0x0005 - 1 ; sl_test[i].expected = b"-6"

        i += 1 ; sl_test[i].num =  0x0000 - 1 ; sl_test[i].expected = b"-1"

        num_slong_tests = i

    elif ct.sizeof(ct.c_long) == 4:

        i  = 1 ; sl_test[i].num = 0x7FFFFFFF ; sl_test[i].expected = b"2147483647"
        i += 1 ; sl_test[i].num = 0x7FFFFFFE ; sl_test[i].expected = b"2147483646"
        i += 1 ; sl_test[i].num = 0x7FFFFFFD ; sl_test[i].expected = b"2147483645"
        i += 1 ; sl_test[i].num = 0x7FFF0000 ; sl_test[i].expected = b"2147418112"
        i += 1 ; sl_test[i].num = 0x00007FFF ; sl_test[i].expected = b"32767"

        i += 1 ; sl_test[i].num = 0x7F000000 ; sl_test[i].expected = b"2130706432"
        i += 1 ; sl_test[i].num = 0x007F0000 ; sl_test[i].expected = b"8323072"
        i += 1 ; sl_test[i].num = 0x00007F00 ; sl_test[i].expected = b"32512"
        i += 1 ; sl_test[i].num = 0x0000007F ; sl_test[i].expected = b"127"

        i += 1 ; sl_test[i].num = 0x70000000 ; sl_test[i].expected = b"1879048192"
        i += 1 ; sl_test[i].num = 0x07000000 ; sl_test[i].expected = b"117440512"
        i += 1 ; sl_test[i].num = 0x00700000 ; sl_test[i].expected = b"7340032"
        i += 1 ; sl_test[i].num = 0x00070000 ; sl_test[i].expected = b"458752"
        i += 1 ; sl_test[i].num = 0x00007000 ; sl_test[i].expected = b"28672"
        i += 1 ; sl_test[i].num = 0x00000700 ; sl_test[i].expected = b"1792"
        i += 1 ; sl_test[i].num = 0x00000070 ; sl_test[i].expected = b"112"
        i += 1 ; sl_test[i].num = 0x00000007 ; sl_test[i].expected = b"7"

        i += 1 ; sl_test[i].num = 0x50000000 ; sl_test[i].expected = b"1342177280"
        i += 1 ; sl_test[i].num = 0x05000000 ; sl_test[i].expected = b"83886080"
        i += 1 ; sl_test[i].num = 0x00500000 ; sl_test[i].expected = b"5242880"
        i += 1 ; sl_test[i].num = 0x00050000 ; sl_test[i].expected = b"327680"
        i += 1 ; sl_test[i].num = 0x00005000 ; sl_test[i].expected = b"20480"
        i += 1 ; sl_test[i].num = 0x00000500 ; sl_test[i].expected = b"1280"
        i += 1 ; sl_test[i].num = 0x00000050 ; sl_test[i].expected = b"80"
        i += 1 ; sl_test[i].num = 0x00000005 ; sl_test[i].expected = b"5"

        i += 1 ; sl_test[i].num = 0x00000001 ; sl_test[i].expected = b"1"
        i += 1 ; sl_test[i].num = 0x00000000 ; sl_test[i].expected = b"0"

        i += 1 ; sl_test[i].num = -0x7FFFFFFF - 1 ; sl_test[i].expected = b"-2147483648"
        i += 1 ; sl_test[i].num = -0x7FFFFFFE - 1 ; sl_test[i].expected = b"-2147483647"
        i += 1 ; sl_test[i].num = -0x7FFFFFFD - 1 ; sl_test[i].expected = b"-2147483646"
        i += 1 ; sl_test[i].num = -0x7FFF0000 - 1 ; sl_test[i].expected = b"-2147418113"
        i += 1 ; sl_test[i].num = -0x00007FFF - 1 ; sl_test[i].expected = b"-32768"

        i += 1 ; sl_test[i].num = -0x7F000000 - 1 ; sl_test[i].expected = b"-2130706433"
        i += 1 ; sl_test[i].num = -0x007F0000 - 1 ; sl_test[i].expected = b"-8323073"
        i += 1 ; sl_test[i].num = -0x00007F00 - 1 ; sl_test[i].expected = b"-32513"
        i += 1 ; sl_test[i].num = -0x0000007F - 1 ; sl_test[i].expected = b"-128"

        i += 1 ; sl_test[i].num = -0x70000000 - 1 ; sl_test[i].expected = b"-1879048193"
        i += 1 ; sl_test[i].num = -0x07000000 - 1 ; sl_test[i].expected = b"-117440513"
        i += 1 ; sl_test[i].num = -0x00700000 - 1 ; sl_test[i].expected = b"-7340033"
        i += 1 ; sl_test[i].num = -0x00070000 - 1 ; sl_test[i].expected = b"-458753"
        i += 1 ; sl_test[i].num = -0x00007000 - 1 ; sl_test[i].expected = b"-28673"
        i += 1 ; sl_test[i].num = -0x00000700 - 1 ; sl_test[i].expected = b"-1793"
        i += 1 ; sl_test[i].num = -0x00000070 - 1 ; sl_test[i].expected = b"-113"
        i += 1 ; sl_test[i].num = -0x00000007 - 1 ; sl_test[i].expected = b"-8"

        i += 1 ; sl_test[i].num = -0x50000000 - 1 ; sl_test[i].expected = b"-1342177281"
        i += 1 ; sl_test[i].num = -0x05000000 - 1 ; sl_test[i].expected = b"-83886081"
        i += 1 ; sl_test[i].num = -0x00500000 - 1 ; sl_test[i].expected = b"-5242881"
        i += 1 ; sl_test[i].num = -0x00050000 - 1 ; sl_test[i].expected = b"-327681"
        i += 1 ; sl_test[i].num = -0x00005000 - 1 ; sl_test[i].expected = b"-20481"
        i += 1 ; sl_test[i].num = -0x00000500 - 1 ; sl_test[i].expected = b"-1281"
        i += 1 ; sl_test[i].num = -0x00000050 - 1 ; sl_test[i].expected = b"-81"
        i += 1 ; sl_test[i].num = -0x00000005 - 1 ; sl_test[i].expected = b"-6"

        i += 1 ; sl_test[i].num =  0x00000000 - 1 ; sl_test[i].expected = b"-1"

        num_slong_tests = i

    elif ct.sizeof(ct.c_long) == 8:

        i  = 1 ; sl_test[i].num = 0x7FFFFFFFFFFFFFFF ; sl_test[i].expected = b"9223372036854775807"
        i += 1 ; sl_test[i].num = 0x7FFFFFFFFFFFFFFE ; sl_test[i].expected = b"9223372036854775806"
        i += 1 ; sl_test[i].num = 0x7FFFFFFFFFFFFFFD ; sl_test[i].expected = b"9223372036854775805"
        i += 1 ; sl_test[i].num = 0x7FFFFFFF00000000 ; sl_test[i].expected = b"9223372032559808512"
        i += 1 ; sl_test[i].num = 0x000000007FFFFFFF ; sl_test[i].expected = b"2147483647"

        i += 1 ; sl_test[i].num = 0x7FFF000000000000 ; sl_test[i].expected = b"9223090561878065152"
        i += 1 ; sl_test[i].num = 0x00007FFF00000000 ; sl_test[i].expected = b"140733193388032"
        i += 1 ; sl_test[i].num = 0x000000007FFF0000 ; sl_test[i].expected = b"2147418112"
        i += 1 ; sl_test[i].num = 0x0000000000007FFF ; sl_test[i].expected = b"32767"

        i += 1 ; sl_test[i].num = 0x7F00000000000000 ; sl_test[i].expected = b"9151314442816847872"
        i += 1 ; sl_test[i].num = 0x007F000000000000 ; sl_test[i].expected = b"35747322042253312"
        i += 1 ; sl_test[i].num = 0x00007F0000000000 ; sl_test[i].expected = b"139637976727552"
        i += 1 ; sl_test[i].num = 0x0000007F00000000 ; sl_test[i].expected = b"545460846592"
        i += 1 ; sl_test[i].num = 0x000000007F000000 ; sl_test[i].expected = b"2130706432"
        i += 1 ; sl_test[i].num = 0x00000000007F0000 ; sl_test[i].expected = b"8323072"
        i += 1 ; sl_test[i].num = 0x0000000000007F00 ; sl_test[i].expected = b"32512"
        i += 1 ; sl_test[i].num = 0x000000000000007F ; sl_test[i].expected = b"127"

        i += 1 ; sl_test[i].num = 0x7000000000000000 ; sl_test[i].expected = b"8070450532247928832"
        i += 1 ; sl_test[i].num = 0x0700000000000000 ; sl_test[i].expected = b"504403158265495552"
        i += 1 ; sl_test[i].num = 0x0070000000000000 ; sl_test[i].expected = b"31525197391593472"
        i += 1 ; sl_test[i].num = 0x0007000000000000 ; sl_test[i].expected = b"1970324836974592"
        i += 1 ; sl_test[i].num = 0x0000700000000000 ; sl_test[i].expected = b"123145302310912"
        i += 1 ; sl_test[i].num = 0x0000070000000000 ; sl_test[i].expected = b"7696581394432"
        i += 1 ; sl_test[i].num = 0x0000007000000000 ; sl_test[i].expected = b"481036337152"
        i += 1 ; sl_test[i].num = 0x0000000700000000 ; sl_test[i].expected = b"30064771072"
        i += 1 ; sl_test[i].num = 0x0000000070000000 ; sl_test[i].expected = b"1879048192"
        i += 1 ; sl_test[i].num = 0x0000000007000000 ; sl_test[i].expected = b"117440512"
        i += 1 ; sl_test[i].num = 0x0000000000700000 ; sl_test[i].expected = b"7340032"
        i += 1 ; sl_test[i].num = 0x0000000000070000 ; sl_test[i].expected = b"458752"
        i += 1 ; sl_test[i].num = 0x0000000000007000 ; sl_test[i].expected = b"28672"
        i += 1 ; sl_test[i].num = 0x0000000000000700 ; sl_test[i].expected = b"1792"
        i += 1 ; sl_test[i].num = 0x0000000000000070 ; sl_test[i].expected = b"112"
        i += 1 ; sl_test[i].num = 0x0000000000000007 ; sl_test[i].expected = b"7"

        i += 1 ; sl_test[i].num = 0x0000000000000001 ; sl_test[i].expected = b"1"
        i += 1 ; sl_test[i].num = 0x0000000000000000 ; sl_test[i].expected = b"0"

        i += 1 ; sl_test[i].num = -0x7FFFFFFFFFFFFFFF - 1 ; sl_test[i].expected = b"-9223372036854775808"
        i += 1 ; sl_test[i].num = -0x7FFFFFFFFFFFFFFE - 1 ; sl_test[i].expected = b"-9223372036854775807"
        i += 1 ; sl_test[i].num = -0x7FFFFFFFFFFFFFFD - 1 ; sl_test[i].expected = b"-9223372036854775806"
        i += 1 ; sl_test[i].num = -0x7FFFFFFF00000000 - 1 ; sl_test[i].expected = b"-9223372032559808513"
        i += 1 ; sl_test[i].num = -0x000000007FFFFFFF - 1 ; sl_test[i].expected = b"-2147483648"

        i += 1 ; sl_test[i].num = -0x7FFF000000000000 - 1 ; sl_test[i].expected = b"-9223090561878065153"
        i += 1 ; sl_test[i].num = -0x00007FFF00000000 - 1 ; sl_test[i].expected = b"-140733193388033"
        i += 1 ; sl_test[i].num = -0x000000007FFF0000 - 1 ; sl_test[i].expected = b"-2147418113"
        i += 1 ; sl_test[i].num = -0x0000000000007FFF - 1 ; sl_test[i].expected = b"-32768"

        i += 1 ; sl_test[i].num = -0x7F00000000000000 - 1 ; sl_test[i].expected = b"-9151314442816847873"
        i += 1 ; sl_test[i].num = -0x007F000000000000 - 1 ; sl_test[i].expected = b"-35747322042253313"
        i += 1 ; sl_test[i].num = -0x00007F0000000000 - 1 ; sl_test[i].expected = b"-139637976727553"
        i += 1 ; sl_test[i].num = -0x0000007F00000000 - 1 ; sl_test[i].expected = b"-545460846593"
        i += 1 ; sl_test[i].num = -0x000000007F000000 - 1 ; sl_test[i].expected = b"-2130706433"
        i += 1 ; sl_test[i].num = -0x00000000007F0000 - 1 ; sl_test[i].expected = b"-8323073"
        i += 1 ; sl_test[i].num = -0x0000000000007F00 - 1 ; sl_test[i].expected = b"-32513"
        i += 1 ; sl_test[i].num = -0x000000000000007F - 1 ; sl_test[i].expected = b"-128"

        i += 1 ; sl_test[i].num = -0x7000000000000000 - 1 ; sl_test[i].expected = b"-8070450532247928833"
        i += 1 ; sl_test[i].num = -0x0700000000000000 - 1 ; sl_test[i].expected = b"-504403158265495553"
        i += 1 ; sl_test[i].num = -0x0070000000000000 - 1 ; sl_test[i].expected = b"-31525197391593473"
        i += 1 ; sl_test[i].num = -0x0007000000000000 - 1 ; sl_test[i].expected = b"-1970324836974593"
        i += 1 ; sl_test[i].num = -0x0000700000000000 - 1 ; sl_test[i].expected = b"-123145302310913"
        i += 1 ; sl_test[i].num = -0x0000070000000000 - 1 ; sl_test[i].expected = b"-7696581394433"
        i += 1 ; sl_test[i].num = -0x0000007000000000 - 1 ; sl_test[i].expected = b"-481036337153"
        i += 1 ; sl_test[i].num = -0x0000000700000000 - 1 ; sl_test[i].expected = b"-30064771073"
        i += 1 ; sl_test[i].num = -0x0000000070000000 - 1 ; sl_test[i].expected = b"-1879048193"
        i += 1 ; sl_test[i].num = -0x0000000007000000 - 1 ; sl_test[i].expected = b"-117440513"
        i += 1 ; sl_test[i].num = -0x0000000000700000 - 1 ; sl_test[i].expected = b"-7340033"
        i += 1 ; sl_test[i].num = -0x0000000000070000 - 1 ; sl_test[i].expected = b"-458753"
        i += 1 ; sl_test[i].num = -0x0000000000007000 - 1 ; sl_test[i].expected = b"-28673"
        i += 1 ; sl_test[i].num = -0x0000000000000700 - 1 ; sl_test[i].expected = b"-1793"
        i += 1 ; sl_test[i].num = -0x0000000000000070 - 1 ; sl_test[i].expected = b"-113"
        i += 1 ; sl_test[i].num = -0x0000000000000007 - 1 ; sl_test[i].expected = b"-8"

        i += 1 ; sl_test[i].num =  0x0000000000000000 - 1 ; sl_test[i].expected = b"-1"

        num_slong_tests = i

    # endif

    for i in range(1, num_slong_tests + 1):

        ct.memset(sl_test[i].result, ord(b'X'), BUFSZ)
        sl_test[i].result[BUFSZ - 1] = ord(b'\0')

        for j, ch in enumerate(b"%ld" % sl_test[i].num):
            sl_test[i].result[j] = ch

        if bytes(sl_test[i].result[:len(sl_test[i].expected)]) != sl_test[i].expected:
            print("signed long test #%.2d: Failed (Expected: %s Got: %s)" %
                  (i, sl_test[i].expected, sl_test[i].result))
            failed += 1

    if not failed:
        print("All libcurl.mprintf() signed long tests OK!")
    else:
        print("Some libcurl.mprintf() signed long tests Failed!")

    return failed


def test_curl_off_t_formatting() -> int:

    num_cofft_tests: int = 0
    failed: int = 0

    i  = 1 ; co_test[i].num = 0x7FFFFFFFFFFFFFFF ; co_test[i].expected = b"9223372036854775807"
    i += 1 ; co_test[i].num = 0x7FFFFFFFFFFFFFFE ; co_test[i].expected = b"9223372036854775806"
    i += 1 ; co_test[i].num = 0x7FFFFFFFFFFFFFFD ; co_test[i].expected = b"9223372036854775805"
    i += 1 ; co_test[i].num = 0x7FFFFFFF00000000 ; co_test[i].expected = b"9223372032559808512"
    i += 1 ; co_test[i].num = 0x000000007FFFFFFF ; co_test[i].expected = b"2147483647"

    i += 1 ; co_test[i].num = 0x7FFF000000000000 ; co_test[i].expected = b"9223090561878065152"
    i += 1 ; co_test[i].num = 0x00007FFF00000000 ; co_test[i].expected = b"140733193388032"
    i += 1 ; co_test[i].num = 0x000000007FFF0000 ; co_test[i].expected = b"2147418112"
    i += 1 ; co_test[i].num = 0x0000000000007FFF ; co_test[i].expected = b"32767"

    i += 1 ; co_test[i].num = 0x7F00000000000000 ; co_test[i].expected = b"9151314442816847872"
    i += 1 ; co_test[i].num = 0x007F000000000000 ; co_test[i].expected = b"35747322042253312"
    i += 1 ; co_test[i].num = 0x00007F0000000000 ; co_test[i].expected = b"139637976727552"
    i += 1 ; co_test[i].num = 0x0000007F00000000 ; co_test[i].expected = b"545460846592"
    i += 1 ; co_test[i].num = 0x000000007F000000 ; co_test[i].expected = b"2130706432"
    i += 1 ; co_test[i].num = 0x00000000007F0000 ; co_test[i].expected = b"8323072"
    i += 1 ; co_test[i].num = 0x0000000000007F00 ; co_test[i].expected = b"32512"
    i += 1 ; co_test[i].num = 0x000000000000007F ; co_test[i].expected = b"127"

    i += 1 ; co_test[i].num = 0x7000000000000000 ; co_test[i].expected = b"8070450532247928832"
    i += 1 ; co_test[i].num = 0x0700000000000000 ; co_test[i].expected = b"504403158265495552"
    i += 1 ; co_test[i].num = 0x0070000000000000 ; co_test[i].expected = b"31525197391593472"
    i += 1 ; co_test[i].num = 0x0007000000000000 ; co_test[i].expected = b"1970324836974592"
    i += 1 ; co_test[i].num = 0x0000700000000000 ; co_test[i].expected = b"123145302310912"
    i += 1 ; co_test[i].num = 0x0000070000000000 ; co_test[i].expected = b"7696581394432"
    i += 1 ; co_test[i].num = 0x0000007000000000 ; co_test[i].expected = b"481036337152"
    i += 1 ; co_test[i].num = 0x0000000700000000 ; co_test[i].expected = b"30064771072"
    i += 1 ; co_test[i].num = 0x0000000070000000 ; co_test[i].expected = b"1879048192"
    i += 1 ; co_test[i].num = 0x0000000007000000 ; co_test[i].expected = b"117440512"
    i += 1 ; co_test[i].num = 0x0000000000700000 ; co_test[i].expected = b"7340032"
    i += 1 ; co_test[i].num = 0x0000000000070000 ; co_test[i].expected = b"458752"
    i += 1 ; co_test[i].num = 0x0000000000007000 ; co_test[i].expected = b"28672"
    i += 1 ; co_test[i].num = 0x0000000000000700 ; co_test[i].expected = b"1792"
    i += 1 ; co_test[i].num = 0x0000000000000070 ; co_test[i].expected = b"112"
    i += 1 ; co_test[i].num = 0x0000000000000007 ; co_test[i].expected = b"7"

    i += 1 ; co_test[i].num = 0x0000000000000001 ; co_test[i].expected = b"1"
    i += 1 ; co_test[i].num = 0x0000000000000000 ; co_test[i].expected = b"0"

    i += 1 ; co_test[i].num = -0x7FFFFFFFFFFFFFFF - 1 ; co_test[i].expected = b"-9223372036854775808"
    i += 1 ; co_test[i].num = -0x7FFFFFFFFFFFFFFE - 1 ; co_test[i].expected = b"-9223372036854775807"
    i += 1 ; co_test[i].num = -0x7FFFFFFFFFFFFFFD - 1 ; co_test[i].expected = b"-9223372036854775806"
    i += 1 ; co_test[i].num = -0x7FFFFFFF00000000 - 1 ; co_test[i].expected = b"-9223372032559808513"
    i += 1 ; co_test[i].num = -0x000000007FFFFFFF - 1 ; co_test[i].expected = b"-2147483648"

    i += 1 ; co_test[i].num = -0x7FFF000000000000 - 1 ; co_test[i].expected = b"-9223090561878065153"
    i += 1 ; co_test[i].num = -0x00007FFF00000000 - 1 ; co_test[i].expected = b"-140733193388033"
    i += 1 ; co_test[i].num = -0x000000007FFF0000 - 1 ; co_test[i].expected = b"-2147418113"
    i += 1 ; co_test[i].num = -0x0000000000007FFF - 1 ; co_test[i].expected = b"-32768"

    i += 1 ; co_test[i].num = -0x7F00000000000000 - 1 ; co_test[i].expected = b"-9151314442816847873"
    i += 1 ; co_test[i].num = -0x007F000000000000 - 1 ; co_test[i].expected = b"-35747322042253313"
    i += 1 ; co_test[i].num = -0x00007F0000000000 - 1 ; co_test[i].expected = b"-139637976727553"
    i += 1 ; co_test[i].num = -0x0000007F00000000 - 1 ; co_test[i].expected = b"-545460846593"
    i += 1 ; co_test[i].num = -0x000000007F000000 - 1 ; co_test[i].expected = b"-2130706433"
    i += 1 ; co_test[i].num = -0x00000000007F0000 - 1 ; co_test[i].expected = b"-8323073"
    i += 1 ; co_test[i].num = -0x0000000000007F00 - 1 ; co_test[i].expected = b"-32513"
    i += 1 ; co_test[i].num = -0x000000000000007F - 1 ; co_test[i].expected = b"-128"

    i += 1 ; co_test[i].num = -0x7000000000000000 - 1 ; co_test[i].expected = b"-8070450532247928833"
    i += 1 ; co_test[i].num = -0x0700000000000000 - 1 ; co_test[i].expected = b"-504403158265495553"
    i += 1 ; co_test[i].num = -0x0070000000000000 - 1 ; co_test[i].expected = b"-31525197391593473"
    i += 1 ; co_test[i].num = -0x0007000000000000 - 1 ; co_test[i].expected = b"-1970324836974593"
    i += 1 ; co_test[i].num = -0x0000700000000000 - 1 ; co_test[i].expected = b"-123145302310913"
    i += 1 ; co_test[i].num = -0x0000070000000000 - 1 ; co_test[i].expected = b"-7696581394433"
    i += 1 ; co_test[i].num = -0x0000007000000000 - 1 ; co_test[i].expected = b"-481036337153"
    i += 1 ; co_test[i].num = -0x0000000700000000 - 1 ; co_test[i].expected = b"-30064771073"
    i += 1 ; co_test[i].num = -0x0000000070000000 - 1 ; co_test[i].expected = b"-1879048193"
    i += 1 ; co_test[i].num = -0x0000000007000000 - 1 ; co_test[i].expected = b"-117440513"
    i += 1 ; co_test[i].num = -0x0000000000700000 - 1 ; co_test[i].expected = b"-7340033"
    i += 1 ; co_test[i].num = -0x0000000000070000 - 1 ; co_test[i].expected = b"-458753"
    i += 1 ; co_test[i].num = -0x0000000000007000 - 1 ; co_test[i].expected = b"-28673"
    i += 1 ; co_test[i].num = -0x0000000000000700 - 1 ; co_test[i].expected = b"-1793"
    i += 1 ; co_test[i].num = -0x0000000000000070 - 1 ; co_test[i].expected = b"-113"
    i += 1 ; co_test[i].num = -0x0000000000000007 - 1 ; co_test[i].expected = b"-8"

    i += 1 ; co_test[i].num =  0x0000000000000000 - 1 ; co_test[i].expected = b"-1"

    num_cofft_tests = i

    for i in range(1, num_cofft_tests + 1):

        ct.memset(co_test[i].result, ord(b'X'), BUFSZ)
        co_test[i].result[BUFSZ - 1] = ord(b'\0')

        for j, ch in enumerate((b"%" + lcurl.CURL_FORMAT_CURL_OFF_T.encode("ascii")) % co_test[i].num):
            co_test[i].result[j] = ch

        if bytes(co_test[i].result[:len(co_test[i].expected)]) != co_test[i].expected:
            print("libcurl.off_t test #%.2d: Failed (Expected: %s Got: %s)" %
                  (i, co_test[i].expected, co_test[i].result))
            failed += 1

    if not failed:
        print("All libcurl.mprintf() libcurl.off_t tests OK!")
    else:
        print("Some libcurl.mprintf() libcurl.off_t tests Failed!")

    return failed


def string_check(buf: bytes, buf2: bytes):
    return _string_check(current_line(2), buf, buf2)

def _string_check(linenumber: int, buf: bytes, buf2: bytes) -> int:
    if buf != buf2:
        # they shouldn't differ
        print("sprintf line %d failed:\n"
              "we      '%s'\n"
              "system: '%s'" %
              (linenumber, buf.decode("utf-8"), buf2.decode("utf-8")))
        return 1
    return 0


def strlen_check(buf: bytes, len: int):
    return _strlen_check(current_line(2), buf, len)

def _strlen_check(linenumber: int, buf: bytes, len: int) -> int:
    buflen = strlen(buf)
    if len != buflen:
        # they shouldn't differ
        print("sprintf strlen:%d failed:\n"
              "we '%d'\n"
              "system: '%d'" %
              (linenumber, buflen, len))
        return 1
    return 0


def test_string_formatting() -> int:

    # The output strings in this test need to have been verified with a system
    # sprintf() before used here.

    errors: int = 0
    buf: bytes

    buf = b"%0*d%s" % (2, 9, b"foo")
    errors += string_check(buf, b"09foo")

    buf = b"%*.*s" % (5, 2, b"foo")
    errors += string_check(buf, b"   fo")

    buf = b"%*.*s" % (2, 5, b"foo")
    errors += string_check(buf, b"foo")

    buf = b"%*.*s" % (0, 10, b"foo")
    errors += string_check(buf, b"foo")

    buf = b"%-10s" % b"foo"
    errors += string_check(buf, b"foo       ")

    buf = b"%10s" % b"foo"
    errors += string_check(buf, b"       foo")

    buf = b"%*.*s" % (-10, 10, b"foo")
    errors += string_check(buf, b"foo       ")

    if not errors:
        print("All libcurl.mprintf() strings tests OK!")
    else:
        print("Some libcurl.mprintf() string tests Failed!")

    return errors


def test_pos_arguments() -> int:

    errors: int = 0
    buf: bytes

    buf = "{2:d} {1:d} {0:d}".format(500, 501, 502).encode("ascii")
    errors += string_check(buf, b"502 501 500")

    buf = "{2:d} {0:d} {1:d}".format(500, 501, 502).encode("ascii")
    errors += string_check(buf, b"502 500 501")

    # this is in invalid sequence but the output does not match
    # what glibc does
    try:
        buf = "{2:d} {:d} {1:d}".format(500, 501, 502).encode("ascii")
    except ValueError:
        pass
    else:
        errors += 1

    return errors


def test_width_precision() -> int:

    # 325 is max precision (and width) for a double

    SPACE60  = 60  * b" "
    SPACE300 = 300 * b" "
    OK325    = SPACE300 + b"                        0"

    errors: int = 0
    larger: bytes

    larger = b"%325.325f" % 0.1
    if len(larger) != 325:
        errors += 1
    errors += string_check(larger, OK325)

    larger = b"%326.326f" % 0.1
    if len(larger) != 325:
        errors += 1
    errors += string_check(larger, OK325)

    larger = b"%1000.1000f" % 0.1
    if len(larger) != 325:
        errors += 1
    errors += string_check(larger, OK325)

    larger = b"%324.324f" % 0.1
    if len(larger) != 324:
        errors += 1
    larger = b"%324.0f" % 0.1
    if len(larger) != 324:
        errors += 1
    larger = b"%0.324f" % 0.1
    if len(larger) != 325:
        errors += 1

    return errors


def test_weird_arguments() -> int:

    errors: int = 0
    buf: bytes

    # verify %%
    buf = b"%-20d%% right? %%" % 500
    errors += string_check(buf, b"500                 % right? %")

    # 100 x %
    buf = (b"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
           b"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
           b"%%%%%%%%%%%%%%%%%%%%%%") % ()
    # 50 x %
    errors += string_check(buf, b"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
                                b"%%%%%%%%%%%%%%%")

    # !!!
    #buf = b"%2 AA %d %K" % (500, 501, 502)
    #errors += string_check(buf, b"%2 AA 500 %K")

    # !!!
    #buf = b"%2 %d %K" % (500, 501, 502)
    #errors += string_check(buf, b"%2 500 %K")

    # MAX_PARAMETERS is 128, try exact 128!
    buf = (b"%d%d%d%d%d%d%d%d%d%d"  # 10
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 1
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 2
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 3
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 4
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 5
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 6
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 7
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 8
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 9
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 10
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 11
           b"%d%d%d%d%d%d%d%d"      # 8
           % (0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 1
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 2
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 3
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 4
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 5
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 6
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 7
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 8
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 9
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 10
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 11
              0, 1, 2, 3, 4, 5, 6, 7))       # 8

    if len(buf) != 128:
        print("libcurl.mprintf() returned %d and not 128!" % len(buf))
        errors += 1

    errors += string_check(buf,
                           b"0123456789"  # 10
                           b"0123456789"  # 10 1
                           b"0123456789"  # 10 2
                           b"0123456789"  # 10 3
                           b"0123456789"  # 10 4
                           b"0123456789"  # 10 5
                           b"0123456789"  # 10 6
                           b"0123456789"  # 10 7
                           b"0123456789"  # 10 8
                           b"0123456789"  # 10 9
                           b"0123456789"  # 10 10
                           b"0123456789"  # 10 11
                           b"01234567")   # 8

    # MAX_PARAMETERS is 128, try more!
    buf = (b"%d%d%d%d%d%d%d%d%d%d"  # 10
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 1
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 2
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 3
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 4
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 5
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 6
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 7
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 8
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 9
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 10
           b"%d%d%d%d%d%d%d%d%d%d"  # 10 11
           b"%d%d%d%d%d%d%d%d%d"    # 9
           % (0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 1
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 2
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 3
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 4
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 5
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 6
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 7
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 8
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 9
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 10
              0, 1, 2, 3, 4, 5, 6, 7, 8, 9,  # 10 11
              0, 1, 2, 3, 4, 5, 6, 7, 8))    # 9

    if len(buf) != 129:
        print("libcurl.mprintf() returned %d and not 129!" % len(buf))
        errors += 1

    errors += string_check(buf,
                           b"0123456789"  # 10
                           b"0123456789"  # 10 1
                           b"0123456789"  # 10 2
                           b"0123456789"  # 10 3
                           b"0123456789"  # 10 4
                           b"0123456789"  # 10 5
                           b"0123456789"  # 10 6
                           b"0123456789"  # 10 7
                           b"0123456789"  # 10 8
                           b"0123456789"  # 10 9
                           b"0123456789"  # 10 10
                           b"0123456789"  # 10 11
                           b"012345678")  # 9

    #errors += string_check(buf, b"")

    errors += test_width_precision()

    if errors:
        print("Some libcurl.mprintf() weird arguments tests failed!")

    return errors


def test_float_formatting() -> int:

    # DBL_MAX value from Linux
    MAXIMIZE = -1.7976931348623157081452E+308

    errors: int = 0
    buf: bytes

    buf = b"%f" % 9.0
    errors += string_check(buf, b"9.000000")

    buf = b"%.1f" % 9.1
    errors += string_check(buf, b"9.1")

    buf = b"%.2f" % 9.1
    errors += string_check(buf, b"9.10")

    buf = b"%.0f" % 9.1
    errors += string_check(buf, b"9")

    buf = b"%0f" % 9.1
    errors += string_check(buf, b"9.100000")

    buf = b"%10f" % 9.1
    errors += string_check(buf, b"  9.100000")

    buf = b"%10.3f" % 9.1
    errors += string_check(buf, b"     9.100")

    buf = b"%-10.3f" % 9.1
    errors += string_check(buf, b"9.100     ")

    buf = b"%-10.3f" % 9.123456
    errors += string_check(buf, b"9.123     ")

    # !!!
    #buf = b"%.-2f" % 9.1
    #errors += string_check(buf, b"9.100000")

    buf = b"%*f" % (10, 9.1)
    errors += string_check(buf, b"  9.100000")

    buf = b"%*f" % (3, 9.1)
    errors += string_check(buf, b"9.100000")

    buf = b"%*f" % (6, 9.2987654)
    errors += string_check(buf, b"9.298765")

    buf = b"%*f" % (6, 9.298765)
    errors += string_check(buf, b"9.298765")

    buf = b"%*f" % (6, 9.29876)
    errors += string_check(buf, b"9.298760")

    buf = b"%.*f" % (6, 9.2987654)
    errors += string_check(buf, b"9.298765")
    buf = b"%.*f" % (5, 9.2987654)
    errors += string_check(buf, b"9.29877")
    buf = b"%.*f" % (4, 9.2987654)
    errors += string_check(buf, b"9.2988")
    buf = b"%.*f" % (3, 9.2987654)
    errors += string_check(buf, b"9.299")
    buf = b"%.*f" % (2, 9.2987654)
    errors += string_check(buf, b"9.30")
    buf = b"%.*f" % (1, 9.2987654)
    errors += string_check(buf, b"9.3")
    buf = b"%.*f" % (0, 9.2987654)
    errors += string_check(buf, b"9")

    # very large precisions easily turn into system specific outputs so we only
    # check the output buffer length here as we know the internal limit

    # !!!
    #buf = b"%.*f" % (1 << 30, 9.2987654)
    #errors += strlen_check(buf, 325)

    # !!!
    #buf = b"%10000.10000f" % 9.2987654
    #errors += strlen_check(buf, 325)

    # !!!
    #buf = b"%240.10000f" % 123456789123456789123456789.2987654
    #errors += strlen_check(buf, 325)

    # check negative width argument when used signed, is treated as positive
    # and maxes out the internal float width == 325
    # !!!
    #buf = b"%*f" % (INT_MIN, 9.1)
    #errors += string_check(buf, b"9.100000                                                                                                                                                                                                                                                                                                                             ")

    # curl_msnprintf() limits a single float output to 325 bytes maximum
    # width
    # !!!
    #buf = b"%*f" % (1 << 30, 9.1)
    #errors += string_check(buf, b"                                                                                                                                                                                                                                                                                                                             9.100000")
    # !!!
    #buf = b"%100000f" % 9.1
    #errors += string_check(buf, b"                                                                                                                                                                                                                                                                                                                             9.100000")

    buf = b"%f" % MAXIMIZE
    errors += strlen_check(buf, 317)

    buf = (b"%f" % MAXIMIZE)[:1]
    errors += strlen_check(buf, 1)
    buf = (b"%f" % MAXIMIZE)[:2]
    errors += strlen_check(buf, 2)
    buf = (b"%f" % MAXIMIZE)[:3]
    errors += strlen_check(buf, 3)
    buf = (b"%f" % MAXIMIZE)[:4]
    errors += strlen_check(buf, 4)
    buf = (b"%f" % MAXIMIZE)[:5]
    errors += strlen_check(buf, 5)

    if not errors:
        print("All float strings tests OK!")
    else:
        print("test_float_formatting Failed!")

    return errors


def test_oct_hex_formatting() -> int:

    errors: int = 0
    buf: bytes

    buf = b"%ho %hx %hX" % (0xFA10, 0xFA10, 0xFA10)
    errors += string_check(buf, b"175020 fa10 FA10")

    if ct.sizeof(ct.c_int) == 2:
        buf = b"%o %x %X" % (0xFA10, 0xFA10, 0xFA10)
        errors += string_check(buf, b"175020 fa10 FA10")
    elif ct.sizeof(ct.c_int) == 4:
        buf = b"%o %x %X" % (0xFABC1230, 0xFABC1230, 0xFABC1230)
        errors += string_check(buf, b"37257011060 fabc1230 FABC1230")
    elif ct.sizeof(ct.c_int) == 8:
        buf = b"%o %x %X" % (0xFABCDEF123456780, 0xFABCDEF123456780, 0xFABCDEF123456780)
        errors += string_check(buf, b"1752746757044321263600 fabcdef123456780 FABCDEF123456780")
    # endif

    if ct.sizeof(ct.c_long) == 2:
        buf = b"%lo %lx %lX" % (0xFA10, 0xFA10, 0xFA10)
        errors += string_check(buf, b"175020 fa10 FA10")
    elif ct.sizeof(ct.c_long) == 4:
        buf = b"%lo %lx %lX" % (0xFABC1230, 0xFABC1230, 0xFABC1230)
        errors += string_check(buf, b"37257011060 fabc1230 FABC1230")
    elif ct.sizeof(ct.c_long) == 8:
        buf = b"%lo %lx %lX" % (0xFABCDEF123456780, 0xFABCDEF123456780, 0xFABCDEF123456780)
        errors += string_check(buf, b"1752746757044321263600 fabcdef123456780 FABCDEF123456780")
    # endif

    if not errors:
        print("All libcurl.mprintf() octal & hexadecimal tests OK!")
    else:
        print("Some libcurl.mprintf() octal & hexadecimal tests Failed!")

    return errors

# !checksrc! enable LONGLINE


def test_return_codes() -> int:

    errors: int = 0
    buf: bytes

    buf = b"%d" % 9999
    if len(buf) != 4:
        errors += 1

    buf = b"%d" % 99999
    if len(buf) != 5:
        errors += 1

    # returns the length excluding the nul byte
    buf = (b"%d" % 99999)[:4]
    if len(buf) != 4:
        errors += 1

    # returns the length excluding the nul byte
    buf = (b"%s" % b"helloooooooo")[:4]
    if len(buf) != 4:
        errors += 1

    # returns the length excluding the nul byte
    buf = (b"%s" % b"helloooooooo")[:5]
    if len(buf) != 5:
        errors += 1

    return errors


@curl_test_decorator
def test(URL: str = None) -> lcurl.CURLcode:
    # URL is not used

    errors: int = 0

    # if defined("HAVE_SETLOCALE"):
    # The test makes assumptions about the numeric locale (specifically,
    # RADIXCHAR) so set it to a known working (and portable) one.
    locale.setlocale(locale.LC_NUMERIC, "C")
    # endif

    errors += test_pos_arguments()

    errors += test_weird_arguments()

    errors += test_unsigned_short_formatting()

    errors += test_signed_short_formatting()

    errors += test_unsigned_int_formatting()

    errors += test_signed_int_formatting()

    errors += test_unsigned_long_formatting()

    errors += test_signed_long_formatting()

    errors += test_curl_off_t_formatting()

    errors += test_string_formatting()

    errors += test_float_formatting()

    errors += test_oct_hex_formatting()

    errors += test_return_codes()

    return TEST_ERR_MAJOR_BAD if errors else lcurl.CURLE_OK
