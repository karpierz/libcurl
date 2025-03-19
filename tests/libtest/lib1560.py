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

from scanf import scanf

import libcurl as lcurl
from curl_test import *  # noqa

# Note:
#
# Since the URL parser by default only accepts schemes that *this instance*
# of libcurl supports, make sure that the test1560 file lists all the schemes
# that this test will assume to be present!

#if defined(USE_LIBIDN2) || defined(USE_WIN32_IDN) || defined(USE_APPLE_IDN)
#define USE_IDN
#endif

class part(ct.Structure):
    _fields_ = [
    ("part", lcurl.CURLUPart),
    ("name", ct.c_char_p),
]


def checkparts(u: ct.POINTER(lcurl.CURLU),
               inp: ct.c_char_p, wanted: ct.c_char_p,
               getflags: ct.c_uint) -> int:

    rc: lcurl.CURLUcode

    parts = [
        part(lcurl.CURLUPART_SCHEME,   b"scheme"),
        part(lcurl.CURLUPART_USER,     b"user"),
        part(lcurl.CURLUPART_PASSWORD, b"password"),
        part(lcurl.CURLUPART_OPTIONS,  b"options"),
        part(lcurl.CURLUPART_HOST,     b"host"),
        part(lcurl.CURLUPART_PORT,     b"port"),
        part(lcurl.CURLUPART_PATH,     b"path"),
        part(lcurl.CURLUPART_QUERY,    b"query"),
        part(lcurl.CURLUPART_FRAGMENT, b"fragment"),
        part(lcurl.CURLUPART_URL,      None),
    ]

    buf = (ct.c_char * 256)()
    size = ct.sizeof(buf)
    ct.memset(buf, 0, ct.sizeof(buf))

    bufp: ct.c_char_p = b"???" # &buf[0] # !!!
    for part_item in parts:

        p = ct.c_char_p(None)
        rc = lcurl.url_get(u, part_item.part, ct.byref(p), getflags)
        if not rc and p:
            msnprintf(bufp, size, "%s%s",   " | " if buf[0] else "", p)
        else:
            msnprintf(bufp, size, "%s[%d]", " | " if buf[0] else "", int(rc))

        n: int = strlen(bufp)
        bufp += n
        size -= n
        lcurl.free(p)

    if (strcmp(buf, wanted)):
        print("in: %s\nwanted: %s\ngot:    %s" %
              (inp, wanted, buf), file=sys.stderr)
        return 1

    return 0


class redircase(ct.Structure):
    _fields_ = [
    ("inp",      ct.c_char_p),
    ("set",      ct.c_char_p),
    ("out",      ct.c_char_p),
    ("urlflags", ct.c_uint),
    ("setflags", ct.c_uint),
    ("ucode",    lcurl.CURLUcode),
]

class setcase(ct.Structure):
    _fields_ = [
    ("inp",      ct.c_char_p),
    ("set",      ct.c_char_p),
    ("out",      ct.c_char_p),
    ("urlflags", ct.c_uint),
    ("setflags", ct.c_uint),
    ("ucode",    lcurl.CURLUcode),  # for the main URL set
    ("pcode",    lcurl.CURLUcode),  # for updating parts
]

class setgetcase(ct.Structure):
    _fields_ = [
    ("inp",      ct.c_char_p),
    ("set",      ct.c_char_p),
    ("out",      ct.c_char_p),
    ("urlflags", ct.c_uint),        # for setting the URL
    ("setflags", ct.c_uint),        # for updating parts
    ("getflags", ct.c_uint),        # for getting parts
    ("pcode",    lcurl.CURLUcode),  # for updating parts
]

class testcase(ct.Structure):
    _fields_ = [
    ("inp",      ct.c_char_p),
    ("out",      ct.c_char_p),
    ("urlflags", ct.c_uint),
    ("getflags", ct.c_uint),
    ("ucode",    lcurl.CURLUcode),
]

class urltestcase(ct.Structure):
    _fields_ = [
    ("inp",      ct.c_char_p),
    ("out",      ct.c_char_p),
    ("urlflags", ct.c_uint),  # pass to curl_url()
    ("getflags", ct.c_uint),  # pass to curl_url_get()
    ("ucode",    lcurl.CURLUcode),
]

class querycase(ct.Structure):
    _fields_ = [
    ("inp",      ct.c_char_p),
    ("q",        ct.c_char_p),
    ("out",      ct.c_char_p),
    ("urlflags", ct.c_uint),  # pass to curl_url()
    ("qflags",   ct.c_uint),  # pass to curl_url_get()
    ("ucode",    lcurl.CURLUcode),
]

class clearurlcase(ct.Structure):
    _fields_ = [
    ("part",  lcurl.CURLUPart),
    ("inp",   ct.c_char_p),
    ("out",   ct.c_char_p),
    ("ucode", lcurl.CURLUcode),
]

get_parts_list = [
    testcase(b"curl.se",
             b"[10] | [11] | [12] | [13] | curl.se | [15] | / | [16] | [17]",
             lcurl.CURLU_GUESS_SCHEME, lcurl.CURLU_NO_GUESS_SCHEME, lcurl.CURLUE_OK),
    testcase(b"https://curl.se:0/#",
             b"https | [11] | [12] | [13] | curl.se | 0 | / | [16] | ",
             0, lcurl.CURLU_GET_EMPTY, lcurl.CURLUE_OK),
    testcase(b"https://curl.se/#",
             b"https | [11] | [12] | [13] | curl.se | [15] | / | [16] | ",
             0, lcurl.CURLU_GET_EMPTY, lcurl.CURLUE_OK),
    testcase(b"https://curl.se/?#",
             b"https | [11] | [12] | [13] | curl.se | [15] | / |  | ",
             0, lcurl.CURLU_GET_EMPTY, lcurl.CURLUE_OK),
    testcase(b"https://curl.se/?",
             b"https | [11] | [12] | [13] | curl.se | [15] | / |  | [17]",
             0, lcurl.CURLU_GET_EMPTY, lcurl.CURLUE_OK),
    testcase(b"https://curl.se/?",
             b"https | [11] | [12] | [13] | curl.se | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"https://curl.se/?#",
             b"https | [11] | [12] | [13] | curl.se | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"https://curl.se/#  ",
             b"https | [11] | [12] | [13] | curl.se | [15] | / | [16] | %20%20",
             lcurl.CURLU_URLENCODE | lcurl.CURLU_ALLOW_SPACE, 0, lcurl.CURLUE_OK),
    testcase(b"", b"", 0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b" ", b"", 0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"1h://example.net", b"", 0, 0, lcurl.CURLUE_BAD_SCHEME),
    testcase(b"..://example.net", b"", 0, 0, lcurl.CURLUE_BAD_SCHEME),
    testcase(b"-ht://example.net", b"", 0, 0, lcurl.CURLUE_BAD_SCHEME),
    testcase(b"+ftp://example.net", b"", 0, 0, lcurl.CURLUE_BAD_SCHEME),
    testcase(b"hej.hej://example.net",
             b"hej.hej | [11] | [12] | [13] | example.net | [15] | / | [16] | [17]",
             lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"ht-tp://example.net",
             b"ht-tp | [11] | [12] | [13] | example.net | [15] | / | [16] | [17]",
             lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"ftp+more://example.net",
             b"ftp+more | [11] | [12] | [13] | example.net | [15] | / | [16] | [17]",
             lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"f1337://example.net",
             b"f1337 | [11] | [12] | [13] | example.net | [15] | / | [16] | [17]",
             lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://user@example.net?hello# space ",
             b"https | user | [12] | [13] | example.net | [15] | / | hello | %20space%20",
             lcurl.CURLU_ALLOW_SPACE | lcurl.CURLU_URLENCODE, 0, lcurl.CURLUE_OK),
    testcase(b"https://test%test", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://example.com%252f%40@example.net",
             b"https | example.com%2f@ | [12] | [13] | example.net | [15] | / "
             b"| [16] | [17]",
             0, lcurl.CURLU_URLDECODE, lcurl.CURLUE_OK ),
    #ifdef USE_IDN
        testcase("https://räksmörgås.se".encode("utf-8"),
                 b"https | [11] | [12] | [13] | xn--rksmrgs-5wao1o.se | "
                 b"[15] | / | [16] | [17]", 0, lcurl.CURLU_PUNYCODE, lcurl.CURLUE_OK),
        testcase(b"https://xn--rksmrgs-5wao1o.se",
                 "https | [11] | [12] | [13] | räksmörgås.se | ".encode("utf-8") +
                 b"[15] | / | [16] | [17]", 0, lcurl.CURLU_PUNY2IDN, lcurl.CURLUE_OK),
    #else
        testcase("https://räksmörgås.se".encode("utf-8"),
                 b"https | [11] | [12] | [13] | [30] | [15] | / | [16] | [17]",
                 0, lcurl.CURLU_PUNYCODE, lcurl.CURLUE_OK),
    # endif
    # https://ℂᵤⓇℒ。𝐒🄴
    testcase(b"https://"
             b"%e2%84%82%e1%b5%a4%e2%93%87%e2%84%92%e3%80%82%f0%9d%90%92%f0%9f%84%b4",
             "https | [11] | [12] | [13] | ℂᵤⓇℒ。𝐒🄴 | [15] |".encode("utf-8") +
             b" / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"https://"
             b"%e2%84%82%e1%b5%a4%e2%93%87%e2%84%92%e3%80%82%f0%9d%90%92%f0%9f%84%b4",
             b"https | [11] | [12] | [13] | "
             b"%e2%84%82%e1%b5%a4%e2%93%87%e2%84%92%e3%80%82%f0%9d%90%92%f0%9f%84%b4 "
             b"| [15] | / | [16] | [17]",
             0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK),
    testcase(b"https://"
             b"\xe2\x84\x82\xe1\xb5\xa4\xe2\x93\x87\xe2\x84\x92"
             b"\xe3\x80\x82\xf0\x9d\x90\x92\xf0\x9f\x84\xb4",
             b"https | [11] | [12] | [13] | "
             b"%e2%84%82%e1%b5%a4%e2%93%87%e2%84%92%e3%80%82%f0%9d%90%92%f0%9f%84%b4 "
             b"| [15] | / | [16] | [17]",
             0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK),
    testcase(b"https://user@example.net?he l lo",
             b"https | user | [12] | [13] | example.net | [15] | / | he+l+lo | [17]",
             lcurl.CURLU_ALLOW_SPACE, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK),
    testcase(b"https://user@example.net?he l lo",
             b"https | user | [12] | [13] | example.net | [15] | / | he l lo | [17]",
             lcurl.CURLU_ALLOW_SPACE, 0, lcurl.CURLUE_OK),
    testcase(b"https://exam{}[]ple.net", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam{ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam}ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam]ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam\\ple.net",   b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam$ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam'ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam\"ple.net",   b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam^ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam`ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam*ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam<ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam>ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam=ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://exam;ple.net",    b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://example,net",     b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://example&net",     b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://example+net",     b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://example(net",     b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://example)net",     b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    testcase(b"https://example.net/}",
             b"https | [11] | [12] | [13] | example.net | [15] | /} | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),

    # blank user is blank
    testcase(b"https://:password@example.net",
             b"https |  | password | [13] | example.net | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    # blank user + blank password
    testcase(b"https://:@example.net",
             b"https |  |  | [13] | example.net | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    # user-only (no password)
    testcase(b"https://user@example.net",
             b"https | user | [12] | [13] | example.net | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    #ifndef CURL_DISABLE_WEBSOCKETS
        testcase(b"ws://example.com/color/?green",
                 b"ws | [11] | [12] | [13] | example.com | [15] | /color/ | green |"
                 b" [17]",
                 lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK ),
        testcase(b"wss://example.com/color/?green",
                 b"wss | [11] | [12] | [13] | example.com | [15] | /color/ | green |"
                 b" [17]",
                 lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK ),
    # endif

    testcase(b"https://user:password@example.net/get?this=and#but frag then", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"https://user:password@example.net/get?this=and what", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"https://user:password@example.net/ge t?this=and-what", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"https://user:pass word@example.net/get?this=and-what", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"https://u ser:password@example.net/get?this=and-what", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"imap://user:pass;opt ion@server/path", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    # no space allowed in scheme
    testcase(b"htt ps://user:password@example.net/get?this=and-what", b"",
             lcurl.CURLU_NON_SUPPORT_SCHEME | lcurl.CURLU_ALLOW_SPACE, 0, lcurl.CURLUE_BAD_SCHEME),
    testcase(b"https://user:password@example.net/get?this=and what",
             b"https | user | password | [13] | example.net | [15] | /get | "
             b"this=and what | [17]",
             lcurl.CURLU_ALLOW_SPACE, 0, lcurl.CURLUE_OK),
    testcase(b"https://user:password@example.net/ge t?this=and-what",
             b"https | user | password | [13] | example.net | [15] | /ge t | "
             b"this=and-what | [17]",
             lcurl.CURLU_ALLOW_SPACE, 0, lcurl.CURLUE_OK),
    testcase(b"https://user:pass word@example.net/get?this=and-what",
             b"https | user | pass word | [13] | example.net | [15] | /get | "
             b"this=and-what | [17]",
             lcurl.CURLU_ALLOW_SPACE, 0, lcurl.CURLUE_OK),
    testcase(b"https://u ser:password@example.net/get?this=and-what",
             b"https | u ser | password | [13] | example.net | [15] | /get | "
             b"this=and-what | [17]",
             lcurl.CURLU_ALLOW_SPACE, 0, lcurl.CURLUE_OK),
    testcase(b"https://user:password@example.net/ge t?this=and-what",
             b"https | user | password | [13] | example.net | [15] | /ge%20t | "
             b"this=and-what | [17]",
             lcurl.CURLU_ALLOW_SPACE | lcurl.CURLU_URLENCODE, 0, lcurl.CURLUE_OK),
    testcase(b"[0:0:0:0:0:0:0:1]",
             b"http | [11] | [12] | [13] | [::1] | [15] | / | [16] | [17]",
             lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"[::1]",
             b"http | [11] | [12] | [13] | [::1] | [15] | / | [16] | [17]",
             lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"[::]",
             b"http | [11] | [12] | [13] | [::] | [15] | / | [16] | [17]",
             lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"https://[::1]",
             b"https | [11] | [12] | [13] | [::1] | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK ),
    testcase(b"user:moo@ftp.example.com/color/#green?no-red",
             b"ftp | user | moo | [13] | ftp.example.com | [15] | /color/ | [16] | "
             b"green?no-red",
             lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"ftp.user:moo@example.com/color/#green?no-red",
             b"http | ftp.user | moo | [13] | example.com | [15] | /color/ | [16] | "
             b"green?no-red",
             lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK ),
    # if is_windows:
        testcase(b"file:/C:\\programs\\foo",
                 b"file | [11] | [12] | [13] | [14] | [15] | C:\\programs\\foo | [16] | [17]",
                 lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
        testcase(b"file://C:\\programs\\foo",
                 b"file | [11] | [12] | [13] | [14] | [15] | C:\\programs\\foo | [16] | [17]",
                 lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
        testcase(b"file:///C:\\programs\\foo",
                 b"file | [11] | [12] | [13] | [14] | [15] | C:\\programs\\foo | [16] | [17]",
                 lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
        testcase(b"file://host.example.com/Share/path/to/file.txt",
                 b"file | [11] | [12] | [13] | host.example.com | [15] | "
                 b"//host.example.com/Share/path/to/file.txt | [16] | [17]",
                 lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    # endif
    testcase(b"https://example.com/color/#green?no-red",
             b"https | [11] | [12] | [13] | example.com | [15] | /color/ | [16] | "
             b"green?no-red",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"https://example.com/color/#green#no-red",
             b"https | [11] | [12] | [13] | example.com | [15] | /color/ | [16] | "
             b"green#no-red",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"https://example.com/color/?green#no-red",
             b"https | [11] | [12] | [13] | example.com | [15] | /color/ | green | "
             b"no-red",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"https://example.com/#color/?green#no-red",
             b"https | [11] | [12] | [13] | example.com | [15] | / | [16] | "
             b"color/?green#no-red",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"https://example.#com/color/?green#no-red",
             b"https | [11] | [12] | [13] | example. | [15] | / | [16] | "
             b"com/color/?green#no-red",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK ),
    testcase(b"http://[ab.be:1]/x", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_BAD_IPV6),
    testcase(b"http://[ab.be]/x", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_BAD_IPV6),
    # URL without host name
    testcase(b"http://a:b@/x", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_NO_HOST),
    testcase(b"boing:80",
             b"https | [11] | [12] | [13] | boing | 80 | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME | lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://[fd00:a41::50]:8080",
             b"http | [11] | [12] | [13] | [fd00:a41::50] | 8080 | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://[fd00:a41::50]/",
             b"http | [11] | [12] | [13] | [fd00:a41::50] | [15] | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://[fd00:a41::50]",
             b"http | [11] | [12] | [13] | [fd00:a41::50] | [15] | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://[::1%252]:1234",
             b"https | [11] | [12] | [13] | [::1] | 1234 | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),

    # here's "bad" zone id
    testcase(b"https://[fe80::20c:29ff:fe9c:409b%eth0]:1234",
             b"https | [11] | [12] | [13] | [fe80::20c:29ff:fe9c:409b] | 1234 "
             b"| / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://127.0.0.1:443",
             b"https | [11] | [12] | [13] | 127.0.0.1 | [15] | / | [16] | [17]",
             0, lcurl.CURLU_NO_DEFAULT_PORT, lcurl.CURLUE_OK),
    testcase(b"http://%3a:%3a@ex4mple/%3f+?+%3f+%23#+%23%3f%g7",
             b"http | : | : | [13] | ex4mple | [15] | /?+ |  ? # | +#?%g7",
             0, lcurl.CURLU_URLDECODE, lcurl.CURLUE_OK),
    testcase(b"http://%3a:%3a@ex4mple/%3f?%3f%35#%35%3f%g7",
             b"http | %3a | %3a | [13] | ex4mple | [15] | /%3f | %3f%35 | %35%3f%g7",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"http://HO0_-st%41/",
             b"http | [11] | [12] | [13] | HO0_-stA | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"file://hello.html",
             b"",
             0, 0, lcurl.CURLUE_BAD_FILE_URL),
    testcase(b"http://HO0_-st/",
             b"http | [11] | [12] | [13] | HO0_-st | [15] | / | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"imap://user:pass;option@server/path",
             b"imap | user | pass | option | server | [15] | /path | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"http://user:pass;option@server/path",
             b"http | user | pass;option | [13] | server | [15] | /path | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"file:/hello.html",
             b"file | [11] | [12] | [13] | [14] | [15] | /hello.html | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"file:/h",
             b"file | [11] | [12] | [13] | [14] | [15] | /h | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"file:/",
             b"file | [11] | [12] | [13] | [14] | [15] | | [16] | [17]",
             0, 0, lcurl.CURLUE_BAD_FILE_URL),
    testcase(b"file://127.0.0.1/hello.html",
             b"file | [11] | [12] | [13] | [14] | [15] | /hello.html | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"file:////hello.html",
             b"file | [11] | [12] | [13] | [14] | [15] | //hello.html | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"file:///hello.html",
             b"file | [11] | [12] | [13] | [14] | [15] | /hello.html | [16] | [17]",
             0, 0, lcurl.CURLUE_OK),
    testcase(b"https://127.0.0.1",
             b"https | [11] | [12] | [13] | 127.0.0.1 | 443 | / | [16] | [17]",
             0, lcurl.CURLU_DEFAULT_PORT, lcurl.CURLUE_OK),
    testcase(b"https://127.0.0.1",
             b"https | [11] | [12] | [13] | 127.0.0.1 | [15] | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://[::1]:1234",
             b"https | [11] | [12] | [13] | [::1] | 1234 | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://127abc.com",
             b"https | [11] | [12] | [13] | 127abc.com | [15] | / | [16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https:// example.com?check", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"https://e x a m p l e.com?check", b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    testcase(b"https://example.com?check",
             b"https | [11] | [12] | [13] | example.com | [15] | / | check | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://example.com:65536",
             b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_BAD_PORT_NUMBER),
    testcase(b"https://example.com:-1#moo",
             b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_BAD_PORT_NUMBER),
    testcase(b"https://example.com:0#moo",
             b"https | [11] | [12] | [13] | example.com | 0 | / | "
             b"[16] | moo",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://example.com:01#moo",
             b"https | [11] | [12] | [13] | example.com | 1 | / | "
             b"[16] | moo",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://example.com:1#moo",
             b"https | [11] | [12] | [13] | example.com | 1 | / | "
             b"[16] | moo",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://example.com#moo",
             b"http | [11] | [12] | [13] | example.com | [15] | / | "
             b"[16] | moo",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://example.com",
             b"http | [11] | [12] | [13] | example.com | [15] | / | "
             b"[16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://example.com/path/html",
             b"http | [11] | [12] | [13] | example.com | [15] | /path/html | "
             b"[16] | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://example.com/path/html?query=name",
             b"http | [11] | [12] | [13] | example.com | [15] | /path/html | "
             b"query=name | [17]",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://example.com/path/html?query=name#anchor",
             b"http | [11] | [12] | [13] | example.com | [15] | /path/html | "
             b"query=name | anchor",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://example.com:1234/path/html?query=name#anchor",
             b"http | [11] | [12] | [13] | example.com | 1234 | /path/html | "
             b"query=name | anchor",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http:///user:password@example.com:1234/path/html?query=name#anchor",
             b"http | user | password | [13] | example.com | 1234 | /path/html | "
             b"query=name | anchor",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"https://user:password@example.com:1234/path/html?query=name#anchor",
             b"https | user | password | [13] | example.com | 1234 | /path/html | "
             b"query=name | anchor",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http://user:password@example.com:1234/path/html?query=name#anchor",
             b"http | user | password | [13] | example.com | 1234 | /path/html | "
             b"query=name | anchor",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http:/user:password@example.com:1234/path/html?query=name#anchor",
             b"http | user | password | [13] | example.com | 1234 | /path/html | "
             b"query=name | anchor",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    testcase(b"http:////user:password@example.com:1234/path/html?query=name#anchor",
             b"",
             lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_BAD_SLASHES),
]

get_url_list = [
    urltestcase(b"example.com",
                b"example.com/",
                lcurl.CURLU_GUESS_SCHEME, lcurl.CURLU_NO_GUESS_SCHEME, lcurl.CURLUE_OK),
    urltestcase(b"http://user@example.com?#",
                b"http://user@example.com/?#",
                0, lcurl.CURLU_GET_EMPTY, lcurl.CURLUE_OK),
    # WHATWG disgrees, it wants "https:/0.0.0.0/"
    urltestcase(b"https://0x.0x.0", b"https://0x.0x.0/", 0, 0, lcurl.CURLUE_OK),

    urltestcase(b"https://example.com:000000000000000000000443/foo",
                b"https://example.com/foo",
                0, lcurl.CURLU_NO_DEFAULT_PORT, lcurl.CURLUE_OK),
    urltestcase(b"https://example.com:000000000000000000000/foo",
                b"https://example.com:0/foo",
                0, lcurl.CURLU_NO_DEFAULT_PORT, lcurl.CURLUE_OK),
    urltestcase(b"https://192.0x0000A80001", b"https://192.168.0.1/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0xffffffff", b"https://255.255.255.255/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.0x1000000", b"https://1.0x1000000/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0x7f.1", b"https://127.0.0.1/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.2.3.256.com", b"https://1.2.3.256.com/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://10.com", b"https://10.com/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.2.com", b"https://1.2.com/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.2.3.com", b"https://1.2.3.com/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.2.com.99", b"https://1.2.com.99/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://[fe80::0000:20c:29ff:fe9c:409b]:80/moo",
                b"https://[fe80::20c:29ff:fe9c:409b]:80/moo",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://[fe80::020c:29ff:fe9c:409b]:80/moo",
                b"https://[fe80::20c:29ff:fe9c:409b]:80/moo",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://[fe80:0000:0000:0000:020c:29ff:fe9c:409b]:80/moo",
                b"https://[fe80::20c:29ff:fe9c:409b]:80/moo",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://[fe80:0:0:0:409b::]:80/moo",
                b"https://[fe80::409b:0:0:0]:80/moo",
                0, 0, lcurl.CURLUE_OK),
    # normalize to lower case
    urltestcase(b"https://[FE80:0:A:0:409B:0:0:0]:80/moo",
                b"https://[fe80:0:a:0:409b::]:80/moo",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://[::%25fakeit];80/moo",
                b"",
                0, 0, lcurl.CURLUE_BAD_PORT_NUMBER),
    urltestcase(b"https://[fe80::20c:29ff:fe9c:409b]-80/moo",
                b"",
                0, 0, lcurl.CURLUE_BAD_PORT_NUMBER),
    #ifdef USE_IDN
        urltestcase("https://räksmörgås.se/path?q#frag".encode("utf-8"),
                    b"https://xn--rksmrgs-5wao1o.se/path?q#frag", 0, lcurl.CURLU_PUNYCODE, lcurl.CURLUE_OK),
    # endif
    # unsupported schemes with no guessing enabled
    urltestcase(b"data:text/html;charset=utf-8;base64,PCFET0NUWVBFIEhUTUw+PG1ldGEgY",
                b"", 0, 0, lcurl.CURLUE_UNSUPPORTED_SCHEME),
    urltestcase(b"d:anything-really", b"", 0, 0, lcurl.CURLUE_UNSUPPORTED_SCHEME),
    urltestcase(b"about:config", b"", 0, 0, lcurl.CURLUE_UNSUPPORTED_SCHEME),
    urltestcase(b"example://foo", b"", 0, 0, lcurl.CURLUE_UNSUPPORTED_SCHEME),
    urltestcase(b"mailto:infobot@example.com?body=send%20current-issue", b"", 0, 0,
                lcurl.CURLUE_UNSUPPORTED_SCHEME),
    urltestcase(b"about:80", b"https://about:80/", lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    # percent encoded host names
    urltestcase(b"http://example.com%40127.0.0.1/", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"http://example.com%21127.0.0.1/", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"http://example.com%3f127.0.0.1/", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"http://example.com%23127.0.0.1/", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"http://example.com%3a127.0.0.1/", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"http://example.com%09127.0.0.1/", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"http://example.com%2F127.0.0.1/", b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"https://%41", b"https://A/",           0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://%20",                     b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"https://%41%0d",                  b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"https://%25",                     b"", 0, 0, lcurl.CURLUE_BAD_HOSTNAME),
    urltestcase(b"https://_%c0_", b"https://_\xC0_/",    0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://_%c0_", b"https://_%C0_/",     0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK),

    # IPv4 trickeries
    urltestcase(b"https://16843009",     b"https://1.1.1.1/",       0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0177.1",       b"https://127.0.0.1/",     0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0111.02.0x3",  b"https://73.2.0.3/",      0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0111.02.0x3.", b"https://0111.02.0x3./",  0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0111.02.030",  b"https://73.2.0.24/",     0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0111.02.030.", b"https://0111.02.030./",  0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://0xff.0xff.0377.255", b"https://255.255.255.255/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.0xffffff",   b"https://1.255.255.255/", 0, 0, lcurl.CURLUE_OK),
    # IPv4 numerical overflows or syntax errors will not normalize
    urltestcase(b"https://a127.0.0.1", b"https://a127.0.0.1/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://\xff.127.0.0.1", b"https://%FF.127.0.0.1/", 0, lcurl.CURLU_URLENCODE,
                lcurl.CURLUE_OK),
    urltestcase(b"https://127.-0.0.1",  b"https://127.-0.0.1/",  0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://127.0. 1",    b"https://127.0.0.1/",   0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    urltestcase(b"https://1.2.3.256",   b"https://1.2.3.256/",   0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.2.3.256.",  b"https://1.2.3.256./",  0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.2.3.4.5",   b"https://1.2.3.4.5/",   0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://1.2.0x100.3", b"https://1.2.0x100.3/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://4294967296",  b"https://4294967296/",  0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://123host",     b"https://123host/",     0, 0, lcurl.CURLUE_OK),
    # 40 bytes scheme is the max allowed
    urltestcase(b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA://hostname/path",
                b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa://hostname/path",
                lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_OK),
    # 41 bytes scheme is not allowed
    urltestcase(b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA://hostname/path",
                b"",
                lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_BAD_SCHEME),
    urltestcase(b"https://[fe80::20c:29ff:fe9c:409b%]:1234",
                b"",
                0, 0, lcurl.CURLUE_BAD_IPV6),
    urltestcase(b"https://[fe80::20c:29ff:fe9c:409b%25]:1234",
                b"https://[fe80::20c:29ff:fe9c:409b%2525]:1234/",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://[fe80::20c:29ff:fe9c:409b%eth0]:1234",
                b"https://[fe80::20c:29ff:fe9c:409b%25eth0]:1234/",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"https://[::%25fakeit]/moo",
                b"https://[::%25fakeit]/moo",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"smtp.example.com/path/html",
                b"smtp://smtp.example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"https.example.com/path/html",
                b"http://https.example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"dict.example.com/path/html",
                b"dict://dict.example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"pop3.example.com/path/html",
                b"pop3://pop3.example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"ldap.example.com/path/html",
                b"ldap://ldap.example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"imap.example.com/path/html",
                b"imap://imap.example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"ftp.example.com/path/html",
                b"ftp://ftp.example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"example.com/path/html",
                b"http://example.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"smtp.com/path/html",
                b"smtp://smtp.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"dict.com/path/html",
                b"dict://dict.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"pop3.com/path/html",
                b"pop3://pop3.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"ldap.com/path/html",
                b"ldap://ldap.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"imap.com/path/html",
                b"imap://imap.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"ftp.com/path/html",
                b"ftp://ftp.com/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"smtp/path/html",
                b"http://smtp/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"dict/path/html",
                b"http://dict/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"pop3/path/html",
                b"http://pop3/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"ldap/path/html",
                b"http://ldap/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"imap/path/html",
                b"http://imap/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"ftp/path/html",
                b"http://ftp/path/html",
                lcurl.CURLU_GUESS_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"HTTP://test/", b"http://test/", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://HO0_-st..~./", b"http://HO0_-st..~./", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http:/@example.com: 123/", b"", 0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    urltestcase(b"http:/@example.com:123 /", b"", 0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    urltestcase(b"http:/@example.com:123a/", b"", 0, 0, lcurl.CURLUE_BAD_PORT_NUMBER),
    urltestcase(b"http://host/file\r", b"",       0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    urltestcase(b"http://host/file\n\x03", b"",   0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    urltestcase(b"htt\x02://host/file", b"",
                lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_MALFORMED_INPUT),
    urltestcase(b" http://host/file", b"", 0, 0, lcurl.CURLUE_MALFORMED_INPUT),
    # here the password ends at the semicolon and options is 'word'
    urltestcase(b"imap://user:pass;word@host/file",
                b"imap://user:pass;word@host/file",
                0, 0, lcurl.CURLUE_OK),
    # here the password has the semicolon
    urltestcase(b"http://user:pass;word@host/file",
                b"http://user:pass;word@host/file", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"file:///file.txt#moo", b"file:///file.txt#moo", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"file:////file.txt", b"file:////file.txt", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"file:///file.txt", b"file:///file.txt", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"file:./", b"file://", 0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://example.com/hello/../here",
                b"http://example.com/hello/../here",
                lcurl.CURLU_PATH_AS_IS, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://example.com/hello/../here",
                b"http://example.com/here",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://example.com:80",
                b"http://example.com/",
                0, lcurl.CURLU_NO_DEFAULT_PORT, lcurl.CURLUE_OK),
    urltestcase(b"tp://example.com/path/html",
                b"",
                0, 0, lcurl.CURLUE_UNSUPPORTED_SCHEME),
    urltestcase(b"http://hello:fool@example.com",
                b"",
                lcurl.CURLU_DISALLOW_USER, 0, lcurl.CURLUE_USER_NOT_ALLOWED),
    urltestcase(b"http:/@example.com:123",
                b"http://@example.com:123/",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http:/:password@example.com",
                b"http://:password@example.com/",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://user@example.com?#",
                b"http://user@example.com/",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://user@example.com?",
                b"http://user@example.com/",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://user@example.com#anchor",
                b"http://user@example.com/#anchor",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"example.com/path/html",
                b"https://example.com/path/html",
                lcurl.CURLU_DEFAULT_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"example.com/path/html",
                b"",
                0, 0, lcurl.CURLUE_BAD_SCHEME),
    urltestcase(b"http://user:password@example.com:1234/path/html?query=name#anchor",
                b"http://user:password@example.com:1234/path/html?query=name#anchor",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://example.com:1234/path/html?query=name#anchor",
                b"http://example.com:1234/path/html?query=name#anchor",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://example.com/path/html?query=name#anchor",
                b"http://example.com/path/html?query=name#anchor",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://example.com/path/html?query=name",
                b"http://example.com/path/html?query=name",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"http://example.com/path/html",
                b"http://example.com/path/html",
                0, 0, lcurl.CURLUE_OK),
    urltestcase(b"tp://example.com/path/html",
                b"tp://example.com/path/html",
                lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"custom-scheme://host?expected=test-good",
                b"custom-scheme://host/?expected=test-good",
                lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_OK),
    urltestcase(b"custom-scheme://?expected=test-bad",
                b"",
                lcurl.CURLU_NON_SUPPORT_SCHEME, 0, lcurl.CURLUE_NO_HOST),
    urltestcase(b"custom-scheme://?expected=test-new-good",
                b"custom-scheme:///?expected=test-new-good",
                lcurl.CURLU_NON_SUPPORT_SCHEME | lcurl.CURLU_NO_AUTHORITY, 0, lcurl.CURLUE_OK),
    urltestcase(b"custom-scheme://host?expected=test-still-good",
                b"custom-scheme://host/?expected=test-still-good",
                lcurl.CURLU_NON_SUPPORT_SCHEME | lcurl.CURLU_NO_AUTHORITY, 0, lcurl.CURLUE_OK),
]


def checkurl(org: bytes, url: bytes, out: bytes) -> int:
    if out != url:
        print("Org:    %s\n"
              "Wanted: %s\n"
              "Got   : %s" %
              (org.decode("utf-8"), out.decode("utf-8"), url.decode("utf-8")), file=sys.stderr)
        return 1
    return 0


# 1. Set the URL
# 2. Set components
# 3. Extract all components (not URL)
#
setget_parts_list = [
    setgetcase(b"https://example.com/",
               b"query=\"\",",
               b"https | [11] | [12] | [13] | example.com | [15] | / |  | [17]",
               0, 0, lcurl.CURLU_GET_EMPTY, lcurl.CURLUE_OK),
    setgetcase(b"https://example.com/",
               b"fragment=\"\",",
               b"https | [11] | [12] | [13] | example.com | [15] | / | [16] | ",
               0,0, lcurl.CURLU_GET_EMPTY, lcurl.CURLUE_OK),
    setgetcase(b"https://example.com/",
               b"query=\"\",",
               b"https | [11] | [12] | [13] | example.com | [15] | / | [16] | [17]",
               0,0, 0, lcurl.CURLUE_OK),
    setgetcase(b"https://example.com",
               b"path=get,",
               b"https | [11] | [12] | [13] | example.com | [15] | /get | [16] | [17]",
               0,0, 0, lcurl.CURLUE_OK),
    setgetcase(b"https://example.com",
               b"path=/get,",
               b"https | [11] | [12] | [13] | example.com | [15] | /get | [16] | [17]",
               0,0, 0, lcurl.CURLUE_OK),
    setgetcase(b"https://example.com",
               b"path=g e t,",
               b"https | [11] | [12] | [13] | example.com | [15] | /g%20e%20t | "
               b"[16] | [17]",
               0,lcurl.CURLU_URLENCODE, 0, lcurl.CURLUE_OK),
]

set_parts_list = [
    setcase(b"https://example.com/",
            b"host=%43url.se,",
            b"https://%43url.se/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://example.com/",
            b"host=%25url.se,",
            b"",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"https://example.com/?param=value",
            b"query=\"\",",
            b"https://example.com/",
            0, lcurl.CURLU_APPENDQUERY | lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://example.com/",
            b"host=\"\",",
            b"https://example.com/",
            0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"https://example.com/",
            b"host=\"\",",
            b"https://example.com/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"https://example.com",
            b"path=get,",
            b"https://example.com/get",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://example.com/",
            b"scheme=ftp+-.123,",
            b"ftp+-.123://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://example.com/",
            b"scheme=1234,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_SCHEME),
    setcase(b"https://example.com/",
            b"scheme=1http,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_SCHEME),
    setcase(b"https://example.com/",
            b"scheme=-ftp,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_SCHEME),
    setcase(b"https://example.com/",
            b"scheme=+ftp,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_SCHEME),
    setcase(b"https://example.com/",
            b"scheme=.ftp,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_SCHEME),
    setcase(b"https://example.com/",
            b"host=example.com%2fmoo,",
            b"",
            0,  # get
            0,  # set
            lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"https://example.com/",
            b"host=http://fake,",
            b"",
            0,  # get
            0,  # set
            lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"https://example.com/",
            b"host=test%,",
            b"",
            0,  # get
            0,  # set
            lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"https://example.com/",
            b"host=te st,",
            b"",
            0,  # get
            0,  # set
            lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"https://example.com/",
            b"host=0xff,",  # '++' there's no automatic URL decode when setting this
            # part
            b"https://0xff/",
            0,  # get
            0,  # set
            lcurl.CURLUE_OK, lcurl.CURLUE_OK),

    setcase(b"https://example.com/",
            b"query=Al2cO3tDkcDZ3EWE5Lh+LX8TPHs,",  # contains '+'
            b"https://example.com/?Al2cO3tDkcDZ3EWE5Lh%2bLX8TPHs",
            lcurl.CURLU_URLDECODE,  # decode on get
            lcurl.CURLU_URLENCODE,  # encode on set
            lcurl.CURLUE_OK, lcurl.CURLUE_OK),

    setcase(b"https://example.com/",
            # Set a bad scheme *including* ://
            b"scheme=https://,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_SCHEME),
    setcase(b"https://example.com/",
            # Set a 41 bytes scheme. That's too long so the old scheme remains set.
            b"scheme=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbc,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_SCHEME),
    setcase(b"https://example.com/",
            # set a 40 bytes scheme
            b"scheme=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,",
            b"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://[::1%25fake]:1234/",
            b"zoneid=NULL,",
            b"https://[::1]:1234/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://host:1234/",
            b"port=NULL,",
            b"https://host/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://host:1234/",
            b"port=\"\",",
            b"https://host:1234/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_PORT_NUMBER),
    setcase(b"https://host:1234/",
            b"port=56 78,",
            b"https://host:1234/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_PORT_NUMBER),
    setcase(b"https://host:1234/",
            b"port=0,",
            b"https://host:0/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://host:1234/",
            b"port=65535,",
            b"https://host:65535/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://host:1234/",
            b"port=65536,",
            b"https://host:1234/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_PORT_NUMBER),
    setcase(b"https://host/",
            b"path=%4A%4B%4C,",
            b"https://host/%4a%4b%4c",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://host/mooo?q#f",
            b"path=NULL,query=NULL,fragment=NULL,",
            b"https://host/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"https://user:secret@host/",
            b"user=NULL,password=NULL,",
            b"https://host/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(None,
            b"scheme=https,user=   @:,host=foobar,",
            b"https://%20%20%20%40%3a@foobar/",
            0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    # Setting a host name with spaces is not OK:
    setcase(None,
            b"scheme=https,host=  ,path= ,user= ,password= ,query= ,fragment= ,",
            b"[nothing]",
            0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK, lcurl.CURLUE_BAD_HOSTNAME),
    setcase(None,
            b"scheme=https,host=foobar,path=/this /path /is /here,",
            b"https://foobar/this%20/path%20/is%20/here",
            0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(None,
            b"scheme=https,host=foobar,path=\xc3\xa4\xc3\xb6\xc3\xbc,",
            b"https://foobar/%c3%a4%c3%b6%c3%bc",
            0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"imap://user:secret;opt@host/",
            b"options=updated,scheme=imaps,password=p4ssw0rd,",
            b"imaps://user:p4ssw0rd;updated@host/",
            0, 0, lcurl.CURLUE_NO_HOST, lcurl.CURLUE_OK),
    setcase(b"imap://user:secret;optit@host/",
            b"scheme=https,",
            b"https://user:secret@host/",
            0, 0, lcurl.CURLUE_NO_HOST, lcurl.CURLUE_OK),
    setcase(b"file:///file#anchor",
            b"scheme=https,host=example,",
            b"https://example/file#anchor",
            0, 0, lcurl.CURLUE_NO_HOST, lcurl.CURLUE_OK),
    setcase(None,  # start fresh!
            b"scheme=file,host=127.0.0.1,path=/no,user=anonymous,",
            b"file:///no",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(None,  # start fresh!
            b"scheme=ftp,host=127.0.0.1,path=/no,user=anonymous,",
            b"ftp://anonymous@127.0.0.1/no",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(None,  # start fresh!
            b"scheme=https,host=example.com,",
            b"https://example.com/",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"http://user:foo@example.com/path?query#frag",
            b"fragment=changed,",
            b"http://user:foo@example.com/path?query#changed",
            0, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"http://example.com/",
            b"scheme=foo,",  # not accepted
            b"http://example.com/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_UNSUPPORTED_SCHEME),
    setcase(b"http://example.com/",
            b"scheme=https,path=/hello,fragment=snippet,",
            b"https://example.com/hello#snippet",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"http://example.com:80",
            b"user=foo,port=1922,",
            b"http://foo@example.com:1922/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"http://example.com:80",
            b"user=foo,password=bar,",
            b"http://foo:bar@example.com:80/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"http://example.com:80",
            b"user=foo,",
            b"http://foo@example.com:80/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"http://example.com",
            b"host=www.example.com,",
            b"http://www.example.com/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"http://example.com:80",
            b"scheme=ftp,",
            b"ftp://example.com:80/",
            0, 0, lcurl.CURLUE_OK, lcurl.CURLUE_OK),
    setcase(b"custom-scheme://host",
            b"host=\"\",",
            b"custom-scheme://host/",
            lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLUE_OK,
            lcurl.CURLUE_BAD_HOSTNAME),
    setcase(b"custom-scheme://host",
            b"host=\"\",",
            b"custom-scheme:///",
            lcurl.CURLU_NON_SUPPORT_SCHEME, lcurl.CURLU_NON_SUPPORT_SCHEME | lcurl.CURLU_NO_AUTHORITY,
            lcurl.CURLUE_OK, lcurl.CURLUE_OK),
]


def part2id(part: str) -> lcurl.CURLUPart:

    if part == "url":
        return lcurl.CURLUPART_URL
    if part == "scheme":
        return lcurl.CURLUPART_SCHEME
    if part == "user":
        return lcurl.CURLUPART_USER
    if part == "password":
        return lcurl.CURLUPART_PASSWORD
    if part == "options":
        return lcurl.CURLUPART_OPTIONS
    if part == "host":
        return lcurl.CURLUPART_HOST
    if part == "port":
        return lcurl.CURLUPART_PORT
    if part == "path":
        return lcurl.CURLUPART_PATH
    if part == "query":
        return lcurl.CURLUPART_QUERY
    if part == "fragment":
        return lcurl.CURLUPART_FRAGMENT
    if part == "zoneid":
        return lcurl.CURLUPART_ZONEID
    return lcurl.CURLUPart(9999).value  # bad input => bad output


def updateurl(u: ct.POINTER(lcurl.CURLU), cmd: bytes, setflags: ct.c_uint) -> lcurl.CURLUcode:

    ptr: bytes = cmd
    uc: lcurl.CURLUcode

    # make sure the last command ends with a comma too!
    while ptr:
        n = ptr.find(b",")
        if n == -1: break

        part_and_value = scanf("%79[^=]=%79[^,]", ptr[:n].decode("utf-8"))
        if part_and_value and len(part_and_value) == 2:
            part, value = part_and_value
            what: lcurl.CURLUPart = part2id(part)
            if 0:  # for debugging this
                print("%s = \"%s\" [%d]" % (part, value, int(what)),
                      file=sys.stderr)
            # endif
            if what > lcurl.CURLUPART_ZONEID:
                print("UNKNOWN part '%s'" % part, file=sys.stderr)

            if value == "NULL":
                uc = lcurl.url_set(u, what, None, setflags)
            elif value == '""':
                uc = lcurl.url_set(u, what, b"", setflags)
            else:
                uc = lcurl.url_set(u, what, value.encode("utf-8"), setflags)
            if uc:
                return uc

        ptr = ptr[n + 1:]

    return lcurl.CURLUE_OK


set_url_list = [
    redircase(b"http://example.org#withs/ash", b"/moo#frag",
              b"http://example.org/moo#frag",  0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/",          b"../path/././../././../moo",
              b"http://example.org/moo",       0, 0, lcurl.CURLUE_OK),

    redircase(b"http://example.org?bar/moo",    b"?weird",
              b"http://example.org/?weird",     0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo?bar",    b"?weird",
              b"http://example.org/foo?weird",  0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo",        b"?weird",
              b"http://example.org/foo?weird",  0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org",            b"?weird",
              b"http://example.org/?weird",     0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/#original",  b"?weird#moo",
              b"http://example.org/?weird#moo", 0, 0, lcurl.CURLUE_OK),

    redircase(b"http://example.org?bar/moo#yes/path",   b"#new/slash",
              b"http://example.org/?bar/moo#new/slash", 0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo?bar",            b"#weird",
              b"http://example.org/foo?bar#weird",      0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo?bar#original",   b"#weird",
              b"http://example.org/foo?bar#weird",      0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo#original",       b"#weird",
              b"http://example.org/foo#weird",          0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/#original",          b"#weird",
              b"http://example.org/#weird",             0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org#original",           b"#weird",
              b"http://example.org/#weird",             0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo?bar",            b"moo?hey#weird",
              b"http://example.org/moo?hey#weird",      0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/",
              b"../path/././../../moo",
              b"http://example.org/moo",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/",
              b"//example.org/../path/../../",
              b"http://example.org/",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/",
              b"///example.org/../path/../../",
              b"http://example.org/",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b":23",
              b"http://example.org/foo/:23",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b"\\x",
              b"http://example.org/foo/\\x",
              # WHATWG disagrees
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b"#/",
              b"http://example.org/foo/bar#/",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b"?/",
              b"http://example.org/foo/bar?/",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b"#;?",
              b"http://example.org/foo/bar#;?",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b"#",
              b"http://example.org/foo/bar",
              # This happens because the parser removes empty fragments
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b"?",
              b"http://example.org/foo/bar",
              # This happens because the parser removes empty queries
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/foo/bar",
              b"?#",
              b"http://example.org/foo/bar",
              # This happens because the parser removes empty queries and fragments
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.com/please/../gimme/%TESTNUMBER?foobar#hello",
              b"http://example.net/there/it/is/../../tes t case=/%TESTNUMBER0002? yes no",
              b"http://example.net/there/tes%20t%20case=/%TESTNUMBER0002?+yes+no",
              0, lcurl.CURLU_URLENCODE | lcurl.CURLU_ALLOW_SPACE, lcurl.CURLUE_OK),
    redircase(b"http://local.test?redirect=http://local.test:80?-321",
              b"http://local.test:80?-123",
              b"http://local.test:80/?-123",
              0, lcurl.CURLU_URLENCODE | lcurl.CURLU_ALLOW_SPACE, lcurl.CURLUE_OK),
    redircase(b"http://local.test?redirect=http://local.test:80?-321",
              b"http://local.test:80?-123",
              b"http://local.test:80/?-123",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.org/static/favicon/wikipedia.ico",
              b"//fake.example.com/licenses/by-sa/3.0/",
              b"http://fake.example.com/licenses/by-sa/3.0/",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"https://example.org/static/favicon/wikipedia.ico",
              b"//fake.example.com/licenses/by-sa/3.0/",
              b"https://fake.example.com/licenses/by-sa/3.0/",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"file://localhost/path?query#frag",
              b"foo#another",
              b"file:///foo#another",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.com/path?query#frag",
              b"https://two.example.com/bradnew",
              b"https://two.example.com/bradnew",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://example.com/path?query#frag",
              b"../../newpage#foo",
              b"http://example.com/newpage#foo",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://user:foo@example.com/path?query#frag",
              b"../../newpage",
              b"http://user:foo@example.com/newpage",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://user:foo@example.com/path?query#frag",
              b"../newpage",
              b"http://user:foo@example.com/newpage",
              0, 0, lcurl.CURLUE_OK),
    redircase(b"http://user:foo@example.com/path?query#frag",
              b"http://?hi",
              b"http:///?hi",
              0, lcurl.CURLU_NO_AUTHORITY, lcurl.CURLUE_OK),
]


def set_url() -> int:

    error: int = 0

    for set_url_item in set_url_list:
        if error: break

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            break

        rc: lcurl.CURLUcode
        rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, set_url_item.inp,
                           set_url_item.urlflags)
        if not rc:
            rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, set_url_item.set,
                               set_url_item.setflags);
            if rc:
                print("%s:%d Set URL %s returned %d (%s)" %
                      (current_file(), current_line(), set_url_item.set,
                       int(rc), lcurl.url_strerror(rc).decode("utf-8")),
                      file=sys.stderr)
                error += 1
            else:
                url = ct.c_char_p(None)
                rc = lcurl.url_get(urlp, lcurl.CURLUPART_URL, ct.byref(url), 0)
                if rc:
                    print("%s:%d Get URL returned %d (%s)" %
                          (current_file(), current_line(),
                           int(rc), lcurl.url_strerror(rc).decode("utf-8")),
                          file=sys.stderr)
                    error += 1
                else:
                    if checkurl(set_url_item.inp, url.value, set_url_item.out):
                        error += 1
                lcurl.free(url)
        elif rc != set_url_item.ucode:
            print("Set URL\nin: %s\nreturned %d (expected %d)" %
                  (set_url_item.inp, int(rc), set_url_item.ucode),
                  file=sys.stderr)
            error += 1

        lcurl.url_cleanup(urlp)

    return error


# 1. Set a URL
# 2. Set one or more parts
# 3. Extract and compare all parts - not the URL
#
def setget_parts() -> int:

    error: int = 0

    for setget_parts_item in setget_parts_list:
        if error: break

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            error += 1
            break

        rc: lcurl.CURLUcode
        if setget_parts_item.inp:
            rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, setget_parts_item.inp,
                               setget_parts_item.urlflags)
        else:
            rc = lcurl.CURLUE_OK
        if not rc:
            url = ct.c_char_p(None)
            uc: lcurl.CURLUcode = updateurl(urlp, setget_parts_item.set,
                                            setget_parts_item.setflags);

            if uc != setget_parts_item.pcode:
                print("updateurl\nin: %s\nreturned %d (expected %d)" %
                      (setget_parts_item.set, int(uc), setget_parts_item.pcode),
                      file=sys.stderr)
                error += 1
            if not uc:
                if checkparts(urlp, setget_parts_item.set, setget_parts_item.out,
                              setget_parts_item.getflags):
                    error += 1  # add
            lcurl.free(url)
        elif rc != lcurl.CURLUE_OK:
            print("Set parts\nin: %s\nreturned %d (expected %d)" %
                  (setget_parts_item.inp, int(rc), 0), file=sys.stderr)
            error += 1

        lcurl.url_cleanup(urlp)

    return error


def set_parts() -> int:

    error: int = 0

    for set_parts_item in set_parts_list:
        if error: break

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            error += 1
            break

        rc: lcurl.CURLUcode
        if set_parts_item.inp:
            rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, set_parts_item.inp,
                               set_parts_item.urlflags);
        else:
            rc = lcurl.CURLUE_OK
        if not rc:
            uc: lcurl.CURLUcode = updateurl(urlp, set_parts_item.set,
                                            set_parts_item.setflags)

            if uc != set_parts_item.pcode:
                print("updateurl\nin: %s\nreturned %d (expected %d)" %
                      (set_parts_item.set, int(uc), set_parts_item.pcode),
                      file=sys.stderr)
                error += 1
            if not uc:
                # only do this if it worked
                url = ct.c_char_p(None)
                rc = lcurl.url_get(urlp, lcurl.CURLUPART_URL, ct.byref(url), 0)
                if rc:
                    print("%s:%d Get URL returned %d (%s)" %
                          (current_file(), current_line(),
                           int(rc), lcurl.url_strerror(rc).decode("utf-8")),
                          file=sys.stderr)
                    error += 1
                elif checkurl(set_parts_item.inp, url.value, set_parts_item.out):
                    error += 1
                lcurl.free(url)
        elif rc != set_parts_item.ucode:
            print("Set parts\nin: %s\nreturned %d (expected %d)" %
                  (set_parts_item.inp, int(rc), set_parts_item.ucode),
                  file=sys.stderr)
            error += 1

        lcurl.url_cleanup(urlp)

    return error


def get_url() -> int:

    error: int = 0

    for get_url_item in get_url_list:
        if error: break

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            error += 1
            break

        rc: lcurl.CURLUcode
        rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, get_url_item.inp,
                           get_url_item.urlflags)
        if not rc:
            url = ct.c_char_p(None)
            rc = lcurl.url_get(urlp, lcurl.CURLUPART_URL, ct.byref(url),
                               get_url_item.getflags)
            if rc:
                print("%s:%d returned %d (%s). URL: '%s'" %
                      (current_file(), current_line(),
                       int(rc), lcurl.url_strerror(rc).decode("utf-8"),
                       get_url_item.inp), file=sys.stderr)
                error += 1
            else:
                if checkurl(get_url_item.inp, url.value, get_url_item.out):
                    error += 1
            lcurl.free(url)

        if rc != get_url_item.ucode:
            print("Get URL\nin: %s\nreturned %d (expected %d)" %
                  (get_url_item.inp, int(rc), get_url_item.ucode),
                  file=sys.stderr)
            error += 1

        lcurl.url_cleanup(urlp)

    return error


def get_parts() -> int:

    error: int = 0

    for get_parts_item in get_parts_list:
        if error: break

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            error += 1
            break

        rc: lcurl.CURLUcode
        rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, get_parts_item.inp,
                           get_parts_item.urlflags);
        if rc != get_parts_item.ucode:
            print("Get parts\nin: %s\nreturned %d (expected %d)" %
                  (get_parts_item.inp, int(rc), get_parts_item.ucode),
                  file=sys.stderr)
            error += 1
        elif get_parts_item.ucode:
            # the expected error happened
            pass
        elif checkparts(urlp, get_parts_item.inp, get_parts_item.out,
                        get_parts_item.getflags):
            error += 1

        lcurl.url_cleanup(urlp)

    return error


append_list = [
    querycase(b"HTTP://test/?s",        b"name=joe\x02", b"http://test/?s&name=joe%02",
              0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK),
    querycase(b"HTTP://test/?size=2#f", b"name=joe=",    b"http://test/?size=2&name=joe%3d#f",
              0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK),
    querycase(b"HTTP://test/?size=2#f", b"name=joe doe", b"http://test/?size=2&name=joe+doe#f",
              0, lcurl.CURLU_URLENCODE, lcurl.CURLUE_OK),
    querycase(b"HTTP://test/",          b"name=joe",     b"http://test/?name=joe",
              0, 0, lcurl.CURLUE_OK),
    querycase(b"HTTP://test/?size=2",   b"name=joe",     b"http://test/?size=2&name=joe",
              0, 0, lcurl.CURLUE_OK),
    querycase(b"HTTP://test/?size=2&",  b"name=joe",     b"http://test/?size=2&name=joe",
              0, 0, lcurl.CURLUE_OK),
    querycase(b"HTTP://test/?size=2#f", b"name=joe",     b"http://test/?size=2&name=joe#f",
              0, 0, lcurl.CURLUE_OK),
]


def append() -> int:

    error: int = 0

    for append_item in append_list:
        if error: break

        urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
        if not urlp:
            error += 1
            break

        rc: lcurl.CURLUcode
        rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, append_item.inp,
                           append_item.urlflags)
        if rc:
            error += 1
        else:
            rc = lcurl.url_set(urlp, lcurl.CURLUPART_QUERY, append_item.q,
                               append_item.qflags | lcurl.CURLU_APPENDQUERY)
        if error:
            pass
        elif rc != append_item.ucode:
            print("Append\nin: %s\nreturned %d (expected %d)" %
                  (append_item.inp, int(rc), append_item.ucode),
                  file=sys.stderr)
            error += 1
        elif append_item.ucode:
            # the expected error happened
            pass
        else:
            url = ct.c_char_p(None)
            rc = lcurl.url_get(urlp, lcurl.CURLUPART_URL, ct.byref(url), 0)
            if rc:
                print("%s:%d Get URL returned %d (%s)" %
                      (current_file(), current_line(),
                       int(rc), lcurl.url_strerror(rc).decode("utf-8")),
                      file=sys.stderr)
                error += 1
            else:
                if checkurl(append_item.inp, url.value, append_item.out):
                    error += 1
                lcurl.free(url)

        lcurl.url_cleanup(urlp)

    return error


def scopeid() -> int:

    error: int = 0

    u: ct.POINTER(lcurl.CURLU) = lcurl.url()
    url = ct.c_char_p(None)

    rc: lcurl.CURLUcode
    rc = lcurl.url_set(u, lcurl.CURLUPART_URL,
                       b"https://[fe80::20c:29ff:fe9c:409b%25eth0]/hello.html", 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_set returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1

    rc = lcurl.url_get(u, lcurl.CURLUPART_HOST, ct.byref(url), 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_get CURLUPART_HOST returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1
    else:
        lcurl.free(url)

    rc = lcurl.url_set(u, lcurl.CURLUPART_HOST, b"[::1]", 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_set CURLUPART_HOST returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1

    rc = lcurl.url_get(u, lcurl.CURLUPART_URL, ct.byref(url), 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_get CURLUPART_URL returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1
    else:
        lcurl.free(url)

    rc = lcurl.url_set(u, lcurl.CURLUPART_HOST, b"example.com", 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_set CURLUPART_HOST returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1

    rc = lcurl.url_get(u, lcurl.CURLUPART_URL, ct.byref(url), 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_get CURLUPART_URL returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1
    else:
        lcurl.free(url)

    rc = lcurl.url_set(u, lcurl.CURLUPART_HOST,
                       b"[fe80::20c:29ff:fe9c:409b%25eth0]", 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_set CURLUPART_HOST returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1

    rc = lcurl.url_get(u, lcurl.CURLUPART_URL, ct.byref(url), 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_get CURLUPART_URL returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1
    else:
        lcurl.free(url)

    rc = lcurl.url_get(u, lcurl.CURLUPART_HOST, ct.byref(url), 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_get CURLUPART_HOST returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1
    else:
        lcurl.free(url)

    rc = lcurl.url_get(u, lcurl.CURLUPART_ZONEID, ct.byref(url), 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_get CURLUPART_ZONEID returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1
    else:
        lcurl.free(url)

    rc = lcurl.url_set(u, lcurl.CURLUPART_ZONEID, b"clown", 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_set CURLUPART_ZONEID returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1

    rc = lcurl.url_get(u, lcurl.CURLUPART_URL, ct.byref(url), 0)
    if rc != lcurl.CURLUE_OK:
        print("%s:%d curl_url_get CURLUPART_URL returned %d (%s)" %
              (current_file(), current_line(),
               int(rc), lcurl.url_strerror(rc).decode("utf-8")), file=sys.stderr)
        error += 1
    else:
        lcurl.free(url)

    lcurl.url_cleanup(u)

    return error


def get_nothing() -> int:

    u: ct.POINTER(lcurl.CURLU) = lcurl.url()
    if not u: return 0

    p = ct.c_char_p(None)

    rc: lcurl.CURLUcode
    rc = lcurl.url_get(u, lcurl.CURLUPART_SCHEME, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_SCHEME:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)

    rc = lcurl.url_get(u, lcurl.CURLUPART_HOST, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_HOST:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)

    rc = lcurl.url_get(u, lcurl.CURLUPART_USER, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_USER:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)

    rc = lcurl.url_get(u, lcurl.CURLUPART_PASSWORD, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_PASSWORD:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)

    rc = lcurl.url_get(u, lcurl.CURLUPART_OPTIONS, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_OPTIONS:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)

    rc = lcurl.url_get(u, lcurl.CURLUPART_PATH, ct.byref(p), 0)
    if rc != lcurl.CURLUE_OK:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)
    else:
        lcurl.free(p)

    rc = lcurl.url_get(u, lcurl.CURLUPART_QUERY, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_QUERY:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)

    rc = lcurl.url_get(u, lcurl.CURLUPART_FRAGMENT, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_FRAGMENT:
        print("unexpected return code line %u" % current_line(), file=sys.stderr)

    rc = lcurl.url_get(u, lcurl.CURLUPART_ZONEID, ct.byref(p), 0)
    if rc != lcurl.CURLUE_NO_ZONEID:
        print("unexpected return code %u on line %u" % (int(rc), current_line()),
              file=sys.stderr)

    lcurl.url_cleanup(u)

    return 0


clear_url_list = [
    clearurlcase(lcurl.CURLUPART_SCHEME,   b"http",     None, lcurl.CURLUE_NO_SCHEME),
    clearurlcase(lcurl.CURLUPART_USER,     b"user",     None, lcurl.CURLUE_NO_USER),
    clearurlcase(lcurl.CURLUPART_PASSWORD, b"password", None, lcurl.CURLUE_NO_PASSWORD),
    clearurlcase(lcurl.CURLUPART_OPTIONS,  b"options",  None, lcurl.CURLUE_NO_OPTIONS),
    clearurlcase(lcurl.CURLUPART_HOST,     b"host",     None, lcurl.CURLUE_NO_HOST),
    clearurlcase(lcurl.CURLUPART_ZONEID,   b"eth0",     None, lcurl.CURLUE_NO_ZONEID),
    clearurlcase(lcurl.CURLUPART_PORT,     b"1234",     None, lcurl.CURLUE_NO_PORT),
    clearurlcase(lcurl.CURLUPART_PATH,     b"/hello",   b"/", lcurl.CURLUE_OK),
    clearurlcase(lcurl.CURLUPART_QUERY,    b"a=b",      None, lcurl.CURLUE_NO_QUERY),
    clearurlcase(lcurl.CURLUPART_FRAGMENT, b"anchor",   None, lcurl.CURLUE_NO_FRAGMENT),
]


def clear_url() -> int:

    error: int = 0

    u: ct.POINTER(lcurl.CURLU) = lcurl.url()
    if not u: return 0

    p = ct.c_char_p(None)
    rc: lcurl.CURLUcode

    for clear_url_item in clear_url_list:
        if error: break

        rc = lcurl.url_set(u, clear_url_item.part, clear_url_item.inp, 0)
        if rc != lcurl.CURLUE_OK:
            print("unexpected return code line %u" % current_line(), file=sys.stderr)

        rc = lcurl.url_set(u, lcurl.CURLUPART_URL, None, 0)
        if rc != lcurl.CURLUE_OK:
            print("unexpected return code line %u" % current_line(), file=sys.stderr)

        rc = lcurl.url_get(u, clear_url_item.part, ct.byref(p), 0)
        if (rc != clear_url_item.ucode or
            (clear_url_item.out and p.value != clear_url_item.out)):
            print("unexpected return code line %u" % current_line(), file=sys.stderr)
            error += 1

        if rc == lcurl.CURLUE_OK:
            lcurl.free(p)

    lcurl.url_cleanup(u)

    return error


total   = (ct.c_char * 128000)()
bigpart = (ct.c_char * 120000)()

def huge() -> int:
    #
    # verify ridiculous URL part sizes
    #
    global bigpart, total

    url_fmt:   ct.c_char_p = b"%s://%s:%s@%s/%s?%s#%s"
    smallpart: ct.c_char_p = b"c"

    part = [  # List[CURLUPart]
        lcurl.CURLUPART_SCHEME,
        lcurl.CURLUPART_USER,
        lcurl.CURLUPART_PASSWORD,
        lcurl.CURLUPART_HOST,
        lcurl.CURLUPART_PATH,
        lcurl.CURLUPART_QUERY,
        lcurl.CURLUPART_FRAGMENT
    ]

    urlp: ct.POINTER(lcurl.CURLU) = lcurl.url()
    if not urlp:
        return 1

    rc: lcurl.CURLUcode
    error: int = 0

    ct.memset(bigpart, ord(b"a"), ct.sizeof(bigpart) - 1)
    bigpart[0] = b"/"  # for the path
    bigpart[ct.sizeof(bigpart) - 1] = b"\0"

    bigpart1p = b"???" # &bigpart[1] # !!!
    for i in range(7):
        partp: ct.c_char_p(None)
        msnprintf(total, sizeof(total), url_fmt,
                   bigpart1p if i == 0 else smallpart,
                   bigpart1p if i == 1 else smallpart,
                   bigpart1p if i == 2 else smallpart,
                   bigpart1p if i == 3 else smallpart,
                   bigpart1p if i == 4 else smallpart,
                   bigpart1p if i == 5 else smallpart,
                   bigpart1p if i == 6 else smallpart)
        rc = lcurl.url_set(urlp, lcurl.CURLUPART_URL, total,
                           lcurl.CURLU_NON_SUPPORT_SCHEME)
        if (i == 0 and rc != lcurl.CURLUE_BAD_SCHEME) or (i != 0 and rc):
            print("URL %u: failed to parse [%s]" % (i, total))
            error += 1

        # only extract if the parse worked
        if not rc:
            lcurl.url_get(urlp, part[i], ct.byref(partp), 0)
            bigpart0 = b"???" # &bigpart[1 - (i == 4)] # !!!
            if not partp or partp != bigpart0:
                print("URL %u part %u: failure" % (i, part[i]))
                error += 1
            lcurl.free(partp)

    lcurl.url_cleanup(urlp)

    return error


def urldup() -> int:

    urls = [  # List[ct.c_char_p]
        b"http://"
        b"user:pwd@"
        b"[2a04:4e42:e00::347%25eth0]"
        b":80"
        b"/path"
        b"?query"
        b"#fraggie",
        b"https://example.com",
        b"https://user@example.com",
        b"https://user.pwd@example.com",
        b"https://user.pwd@example.com:1234",
        b"https://example.com:1234",
        b"example.com:1234",
        b"https://user.pwd@example.com:1234/path?query#frag",
    ]

    h:    ct.POINTER(lcurl.CURLU) = lcurl.url()
    copy: ct.POINTER(lcurl.CURLU) = ct.POINTER(lcurl.CURLU)()
    h_str    = ct.c_char_p(None)
    copy_str = ct.c_char_p(None)

    if not h:
        goto(err)

    for url in urls:

        rc: lcurl.CURLUcode = lcurl.url_set(h, lcurl.CURLUPART_URL, url,
                                            lcurl.CURLU_GUESS_SCHEME)
        if rc:
            goto(err)
        copy = lcurl.url_dup(h)

        rc = lcurl.url_get(h, lcurl.CURLUPART_URL, ct.byref(h_str), 0)
        if rc:
            goto(err)

        rc = lcurl.url_get(copy, lcurl.CURLUPART_URL, ct.byref(copy_str), 0)
        if rc:
            goto(err)

        if h_str.value != copy_str.value:
            print("Original:  %s\nParsed:    %s\nCopy:      %s" % (url,
                  h_str.value.decode("utf-8"), copy_str.value.decode("utf-8")))
            goto(err)

        lcurl.free(copy_str)
        lcurl.free(h_str)
        lcurl.url_cleanup(copy)
        h_str    = ct.c_char_p(None)
        copy_str = ct.c_char_p(None)
        copy     = ct.POINTER(lcurl.CURLU)()

    lcurl.url_cleanup(h)

    return 0

    #err:
    lcurl.free(copy_str)
    lcurl.free(h_str)
    lcurl.url_cleanup(copy)
    lcurl.url_cleanup(h)

    return 1


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    if urldup():
        return lcurl.CURLcode(11).value

    #if setget_parts():  # !!!
    #    return lcurl.CURLcode(10).value

    if get_url():
        return lcurl.CURLcode(3).value

    #if huge():  # !!!
    #    return lcurl.CURLcode(9).value

    if get_nothing():
        return lcurl.CURLcode(7).value

    if scopeid():
        return lcurl.CURLcode(6).value

    if append():
        return lcurl.CURLcode(5).value

    if set_url():
        return lcurl.CURLcode(1).value

    #if set_parts():  # !!!
    #    return lcurl.CURLcode(2).value

    #if get_parts():  # !!!
    #    return lcurl.CURLcode(4).value

    if clear_url():
        return lcurl.CURLcode(8).value

    print("success")

    return lcurl.CURLE_OK
