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

import time
import sys
import ctypes as ct

import libcurl as lcurl
import _tutil as tutil
#from curl_test import *  # noqa


class libtest_trace_cfg(ct.Structure):
    _fields_ = [
   ("tracetime", ct.c_int),  # 0 represents False, anything else True
   ("nohex",     ct.c_int),  # 0 represents False, anything else True
]

libtest_debug_config = libtest_trace_cfg(0, 0)


_known_offset = False  # for test time tracing
_epoch_offset = 0      # for test time tracing

@lcurl.debug_callback
def libtest_debug_cb(handle: ct.POINTER(lcurl.CURL), info_type: lcurl.infotype,
                     data: ct.POINTER(ct.c_ubyte), size: int, userp):
    global _known_offset, _epoch_offset
    trace_cfg = ct.cast(userp, ct.POINTER(libtest_trace_cfg)).contents

    curr_time = ""
    if trace_cfg.tracetime:
        tv: lcurl.timeval = tutil.tvnow()
        if not _known_offset:
            _epoch_offset = int(time.time()) - tv.tv_sec
            _known_offset = True
        secs: lcurl.time_t = _epoch_offset + tv.tv_sec
        now: time.struct_time = time.localtime(secs)
        curr_time = "%02d:%02d:%02d.%06ld " % (
                    now.tm_hour, now.tm_min, now.tm_sec, tv.tv_usec)

    if info_type == lcurl.CURLINFO_TEXT:
        print("%s== Info: %s" %
              (curr_time, ct.cast(data, ct.c_char_p).value.decode("utf-8")),
              end="", file=sys.stderr)
    else:
        if   info_type == lcurl.CURLINFO_HEADER_OUT:   text = "=> Send header"
        elif info_type == lcurl.CURLINFO_DATA_OUT:     text = "=> Send data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_OUT: text = "=> Send SSL data"
        elif info_type == lcurl.CURLINFO_HEADER_IN:    text = "<= Recv header"
        elif info_type == lcurl.CURLINFO_DATA_IN:      text = "<= Recv data"
        elif info_type == lcurl.CURLINFO_SSL_DATA_IN:  text = "<= Recv SSL data"
        else: return 0  # in case a new one is introduced to shock us
        dump(None, curr_time + text, sys.stderr, data, size, bool(trace_cfg.nohex))

    return 0


def dump(num: int, text: str, stream,
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
