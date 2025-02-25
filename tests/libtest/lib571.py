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
from curl_test import *  # noqa

# from warnless.c
def curlx_uztosi(uznum) -> int: return int(uznum)

RTP_PKT_CHANNEL = lambda p: p[1]
RTP_PKT_LENGTH  = lambda p: (p[2] << 8) | p[3]

RTP_DATA = b"$_1234\n\0Rsdf"

rtp_packet_count: int = 0


@lcurl.write_callback
def rtp_write(buffer, size, nitems, stream):

    global rtp_packet_count

    data_size   = nitems * size
    data: bytes = bytes(buffer[:data_size])

    channel: int    = RTP_PKT_CHANNEL(data)
    coded_size: int = RTP_PKT_LENGTH(data)
    failure: int    = 0 if data_size else 1

    message_size: int = curlx_uztosi(data_size) - 4

    print("RTP: message size %d, channel %d" % (message_size, channel))
    if message_size != coded_size:
        print("RTP embedded size (%d) does not match the write size (%d)." %
              (coded_size, message_size))
        return failure

    data = data[4:]
    for i in range(0, message_size, len(RTP_DATA)):
        chunk = data[i:]
        size  = min(len(RTP_DATA), message_size - i)
        if RTP_DATA[:size] != chunk[:size]:
            if message_size - i > len(RTP_DATA):
                print("RTP PAYLOAD CORRUPTED [%s]" % chunk)
            else:
                print("RTP PAYLOAD END CORRUPTED (%d), [%s]" % (size, chunk))
            # return failure

    rtp_packet_count += 1
    print("packet count is %d" % rtp_packet_count, file=sys.stderr)

    return data_size


# build request url
def suburl(base: str, i: int) -> str:
    return "%s%.4d" % (base, i)


@curl_test_decorator
def test(URL: str, filename: str) -> lcurl.CURLcode:
    filename = str(filename)

    global rtp_packet_count

    res: lcurl.CURLcode = lcurl.CURLE_OK

    try:
        protofile = open(filename, "wb")
    except OSError as exc:
        print("Couldn't open the protocol dump file", file=sys.stderr)
        return TEST_ERR_MAJOR_BAD

    with protofile:

        if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
            return TEST_ERR_MAJOR_BAD

        curl: ct.POINTER(lcurl.CURL) = easy_init()

        with curl_guard(True, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            request: int = 1

            test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            stream_uri = suburl(URL, request)
            request += 1
            test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
            test_setopt(curl, lcurl.CURLOPT_INTERLEAVEFUNCTION, rtp_write)
            test_setopt(curl, lcurl.CURLOPT_TIMEOUT, 30)
            test_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            test_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_to_file)
            test_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(protofile))
            test_setopt(curl, lcurl.CURLOPT_RTSP_TRANSPORT, b"RTP/AVP/TCP;interleaved=0-1")
            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_SETUP)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            # This PLAY starts the interleave
            stream_uri = suburl(URL, request)
            request += 1
            test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_PLAY)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            # The DESCRIBE request will try to consume data after the Content
            stream_uri = suburl(URL, request)
            request += 1
            test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_DESCRIBE)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            stream_uri = suburl(URL, request)
            request += 1
            test_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI, stream_uri.encode("utf-8"))
            test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_PLAY)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK: raise guard.Break

            print("PLAY COMPLETE", file=sys.stderr)

            # Use Receive to get the rest of the data
            while res == lcurl.CURLE_OK and rtp_packet_count < 19:
                print("LOOPY LOOP!", file=sys.stderr)
                test_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST, lcurl.CURL_RTSPREQ_RECEIVE)
                res = lcurl.easy_perform(curl)

    return res
