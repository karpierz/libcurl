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

from typing import Optional
from dataclasses import dataclass
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa

# argv1 = URL
# argv2 = proxy with embedded user+password


@dataclass
class testdata:
    trace_ascii: bool = False


@lcurl.debug_callback
def debug_function(curl, info_type, data, size, userptr):
    config = lcurl.from_oid(userptr)
    debug_output(info_type, None, sys.stderr, data, size, config.trace_ascii)
    return 0


def debug_output(info_type, num: Optional[int], stream,
                 data: ct.POINTER(ct.c_ubyte), size: int, no_hex: bool):

    if info_type == lcurl.CURLINFO_TEXT:
        if num is None:
            print("== Info: %s" % bytes(data[:size]).decode("utf-8"),
                  end="", file=stream)
        else:
            print("== [%d] Info: %s" % (num, bytes(data[:size]).decode("utf-8")),
                  end="", file=stream)
    else:
        if   info_type == lcurl.CURLINFO_HEADER_OUT:   text = "=> Send header"
        elif info_type == lcurl.CURLINFO_DATA_OUT:     text = "=> Send data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_OUT: text = "=> Send SSL data"
        elif info_type == lcurl.CURLINFO_HEADER_IN:    text = "<= Recv header"
        elif info_type == lcurl.CURLINFO_DATA_IN:      text = "<= Recv data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_IN:  text = "<= Recv SSL data"
        else: return 0  # in case a new one is introduced to shock us
        dump(num, text, stream, data, size, no_hex)

    return 0


def dump(num: Optional[int], text: str, stream,
         data: ct.POINTER(ct.c_ubyte), size: int, no_hex: bool):

    CR = 0x0D
    LF = 0x0A

    # without the hex output, we can fit more on screen
    width = 0x40 if no_hex else 0x10

    if num is None:
        print("%s, %d bytes (0x%x)" % (text, size, size), file=stream)
    else:
        print("%d %s, %d bytes (0x%x)" % (num, text, size, size), file=stream)

    for i in range(0, size, width):

        print("%04x: " % i, end="", file=stream)

        if not no_hex:
            # hex not disabled, show it
            for c in range(width):
                idx = i + c
                if idx < size:
                    print("%02x " % data[idx], end="", file=stream)
                else:
                    print("   ", end="", file=stream)

        for c in range(width):
            idx = i + c
            if idx >= size:
                break
            # check for CR/LF; if found, skip past and start a new line of output
            if (no_hex and (idx + 1) < size and
                data[idx] == CR and data[idx + 1] == LF):
                i += c + 2 - width
                break
            idx = i + c
            print("%c" % (data[idx] if 0x20 <= data[idx] < 0x80 else "."),
                  end="", file=stream)
            # check again for CR/LF, to avoid an extra \n if it's at width
            idx += 1
            if (no_hex and (idx + 1) < size and
                data[idx] == CR and data[idx + 1] == LF):
                i += c + 3 - width
                break

        print(file=stream)  # newline

    stream.flush()


current_offset: int = 0
databuf = (ct.c_char * 70000)()  # MUST be more than 64k OR MAX_INITIAL_POST_SIZE


@lcurl.read_callback
def read_callback(buffer, size, nitems, stream):
    global current_offset, databuf
    buffer_size = nitems * size                      # Total bytes curl wants
    available = ct.sizeof(databuf) - current_offset  # What we have to give
    given     = min(buffer_size, available)          # What is given
    ct.memmove(buffer, ct.byref(databuf, current_offset), given)
    current_offset += given
    return given;


@lcurl.write_callback
def write_callback(buffer, size, nitems, stream):
    global current_offset
    buffer_size = nitems * size
    #!!!amount = curlx_uztosi(buffer_size)
    amount = buffer_size
    print("%.*s" % (amount, bytes(buffer[:buffer_size]).decode("utf-8")), end="")
    return buffer_size


@lcurl.ioctl_callback
def ioctl_callback(handle, cmd, clientp):
    global current_offset
    if cmd == lcurl.CURLIOCMD_RESTARTREAD:
        print("APPLICATION received a CURLIOCMD_RESTARTREAD request")
        print("APPLICATION ** REWINDING! **")
        current_offset = 0
        return lcurl.CURLIOE_OK
    else:
        return lcurl.CURLIOE_UNKNOWNCMD


@curl_test_decorator
def test(URL: str, proxy: str = None) -> lcurl.CURLcode:

    global databuf

    res: lcurl.CURLcode = lcurl.CURLE_OK

    fill = b"test data"

    config = testdata(trace_ascii=True)  # enable ASCII tracing

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        test_setopt(curl, lcurl.CURLOPT_DEBUGFUNCTION, debug_function)
        test_setopt(curl, lcurl.CURLOPT_DEBUGDATA, id(config))
        # the DEBUGFUNCTION has no effect until we enable VERBOSE
        test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # setup repeated data string
        for i in range(ct.sizeof(databuf)):
            databuf[i] = fill[i % len(fill)]
        # Post
        test_setopt(curl, lcurl.CURLOPT_POST, 1)
        # Setup read callback
        test_setopt(curl, lcurl.CURLOPT_POSTFIELDSIZE, ct.sizeof(databuf))
        test_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_callback)
        # Write callback
        test_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_callback)
        # Ioctl function
        # CURL_IGNORE_DEPRECATION(
        test_setopt(curl, lcurl.CURLOPT_IOCTLFUNCTION, ioctl_callback)
        # )
        test_setopt(curl, lcurl.CURLOPT_PROXY,
                          proxy.encode("utf-8") if proxy else None)
        # Accept any auth. But for this bug configure proxy with DIGEST, basic
        # might work too, not NTLM
        test_setopt(curl, lcurl.CURLOPT_PROXYAUTH, lcurl.CURLAUTH_ANY)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK: raise guard.Break

    return res
