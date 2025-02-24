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

import libcurl as lcurl

TRC_IDS_FORMAT_IDS_1 = f"[%{lcurl.CURL_FORMAT_CURL_OFF_T}-x] "
TRC_IDS_FORMAT_IDS_2 = f"[%{lcurl.CURL_FORMAT_CURL_OFF_T}-%{lcurl.CURL_FORMAT_CURL_OFF_T}] "


_in_log_line: bool = False
_traced_data: bool = False

@lcurl.debug_callback
def debug_cb(curl, info_type, data, size, userptr):
    # callback for CURLOPT_DEBUGFUNCTION

    global _in_log_line, _traced_data
    output = sys.stderr

    xfer_id = lcurl.off_t()
    conn_id = lcurl.off_t()
    if not lcurl.easy_getinfo(curl, lcurl.CURLINFO_XFER_ID,
                              ct.byref(xfer_id)) and xfer_id.value >= 0:
        if not lcurl.easy_getinfo(curl, lcurl.CURLINFO_CONN_ID,
                                  ct.byref(conn_id)) and conn_id.value >= 0:
            idsbuf = TRC_IDS_FORMAT_IDS_2 % (xfer_id.value, conn_id.value)
        else:
            idsbuf = TRC_IDS_FORMAT_IDS_1 % xfer_id.value
    else:
        idsbuf = ""

    if info_type in [lcurl.CURLINFO_HEADER_OUT]:
        if size > 0:
            st = 0
            for i in range(size - 1):
                if data[i] == "\n":  # LF
                    if not _in_log_line:
                        _log_line_start(output, idsbuf, info_type)
                    output.write(data[st:i + 1])
                    st = i + 1
                    _in_log_line = False
            if not _in_log_line:
                _log_line_start(output, idsbuf, info_type)
            output.write(data[st:i + 1])
        _in_log_line = (size and data[size - 1] != "\n")
        _traced_data = False
    elif info_type in [lcurl.CURLINFO_TEXT,
                       lcurl.CURLINFO_HEADER_IN]:
        if not _in_log_line:
            _log_line_start(output, idsbuf, info_type)
        output.write(data[:size])
        _in_log_line = (size and data[size - 1] != "\n")
        _traced_data = False
    elif info_type in [lcurl.CURLINFO_DATA_OUT,
                       lcurl.CURLINFO_DATA_IN,
                       lcurl.CURLINFO_SSL_DATA_IN,
                       lcurl.CURLINFO_SSL_DATA_OUT]:
        if not _traced_data:
            if not _in_log_line:
                _log_line_start(output, idsbuf, info_type)
            print("[%ld bytes data]" % size, file=output)
            _in_log_line = False
            _traced_data = True
    else:  # nada
        _in_log_line = False
        _traced_data = True

    return 0


def _log_line_start(log, idsbuf: str, info_type: lcurl.infotype):
    # This is the trace look that is similar to what libcurl makes on its own.
    s_infotype = ["*", "<", ">", "{", "}", "{", "}"]
    if idsbuf:
        print("%s%s " % (idsbuf, s_infotype[info_type]), end="", file=log)
    else:
        print("%s " % s_infotype[info_type], end="", file=log)


def dump(text: str, data: ct.POINTER(ct.c_ubyte), size: int, no_hex: bool, stream):

    CR = 0x0D
    LF = 0x0A

    # without the hex output, we can fit more on screen
    width = 0x40 if no_hex else 0x10

    print("%s, %u bytes (0x%x)" % (text, size, size), file=stream)

    for i in range(0, size, width):
        print("%4.4x: " % i, end="", file=stream)

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
