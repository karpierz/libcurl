# Copyright (c) 2011 - 2021, Jim Hollinger
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of Jim Hollinger nor the names of its contributors
#     may be used to endorse or promote products derived from this
#     software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
A basic RTSP transfer
"""

import sys
import re
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa
#include <conio.h>  /* _getch() */

here = Path(__file__).resolve().parent


OUT_DIR = here/"output"
VERSION_STR = "V1.0"


def get_sdp_filepath(url: str) -> Path:
    # convert url into an sdp filename
    global OUT_DIR
    idx = url.rfind("/")
    sdp_filename = ("%s.sdp" % url[idx + 1:]
                    if idx != -1 and url[idx + 1:] else "video.sdp")
    return OUT_DIR/sdp_filename


# error handling macros

def my_curl_easy_setopt(A, B, C):
    res: lcurl.CURLcode = lcurl.easy_setopt(A, B, C)
    if res != lcurl.CURLE_OK:
        print("libcurl.easy_setopt(%s, %s, %s) failed: %d" %
              (A, B, C, res), file=sys.stderr)

def my_curl_easy_perform(A):
    res = lcurl.easy_perform(A)
    if res != lcurl.CURLE_OK:
        print("libcurl.easy_perform(%s) failed: %d" %
              (A, res), file=sys.stderr)


@lcurl.write_callback
def write_b_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten)
    return nwritten


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten.decode("utf-8"))
    return nwritten


def rtsp_options(curl: ct.POINTER(lcurl.CURL), uri: str):
    """send RTSP OPTIONS request"""
    print("\nRTSP: OPTIONS %s" % uri)
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI,
                              uri.encode("utf-8"))
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST,
                              lcurl.CURL_RTSPREQ_OPTIONS)
    my_curl_easy_perform(curl)


def rtsp_describe(curl: ct.POINTER(lcurl.CURL), uri: str, sdp_filepath: Path):
    """send RTSP DESCRIBE request and write sdp response to a file"""
    print("\nRTSP: DESCRIBE %s" % uri)
    try:
        sdp_fp = sdp_filepath.open("wb")
    except:
        print("Could not open '%s' for writing" % sdp_filepath,
              file=sys.stderr)
        sdp_fp = sys.stdout
    else:
        print("Writing SDP to '%s'" % sdp_filepath)
    try:
        my_curl_easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_b_function)
        my_curl_easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sdp_fp))
        my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST,
                                  lcurl.CURL_RTSPREQ_DESCRIBE)
        my_curl_easy_perform(curl)
        my_curl_easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        my_curl_easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sys.stdout))
    finally:
        if sdp_fp is not sys.stdout:
            sdp_fp.close()


def rtsp_setup(curl: ct.POINTER(lcurl.CURL), uri: str, transport: str):
    """send RTSP SETUP request"""
    print("\nRTSP: SETUP %s" % uri)
    print("      TRANSPORT %s" % transport)
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI,
                              uri.encode("utf-8"))
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_TRANSPORT,
                              transport.encode("utf-8"))
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST,
                              lcurl.CURL_RTSPREQ_SETUP)
    my_curl_easy_perform(curl)


def rtsp_play(curl: ct.POINTER(lcurl.CURL), uri: str, transfer_range: str):
    """send RTSP PLAY request"""
    print("\nRTSP: PLAY %s" % uri)
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_STREAM_URI,
                              uri.encode("utf-8"))
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RANGE,
                              transfer_range.encode("utf-8"))
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST,
                              lcurl.CURL_RTSPREQ_PLAY)
    my_curl_easy_perform(curl)
    # switch off using range again
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RANGE, None)


def rtsp_teardown(curl: ct.POINTER(lcurl.CURL), uri: str):
    """send RTSP TEARDOWN request"""
    print("\nRTSP: TEARDOWN %s" % uri)
    my_curl_easy_setopt(curl, lcurl.CURLOPT_RTSP_REQUEST,
                              lcurl.CURL_RTSPREQ_TEARDOWN)
    my_curl_easy_perform(curl)


def get_media_control_attribute(sdp_filepath: Path) -> str:
    # scan sdp file for media control attribute
    try:
        sdp_fp = sdp_filepath.open("rb")
    except:
        return ""
    control = ""
    with sdp_fp:
        max_len = 256
        while True:
            chunk = sdp_fp.read(max_len)
            if not chunk: break
            match = re.match(chunk, rb" a = control: (\S+)")
            if match:
                control = match.group(1)
    return control


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]
    global VERSION_STR

    if 1:
        # UDP
        transport = "RTP/AVP;unicast;client_port=1234-1235"
    else:
        # TCP
        transport = "RTP/AVP/TCP;unicast;client_port=1234-1235"
    transfer_range = "0.000-"

    print("\nRTSP request %s" % VERSION_STR)
    print("    Project website: %s" %
          "https://github.com/BackupGGCode/rtsprequest")
    print("    Requires curl V7.20 or greater\n")

    # check command line
    if not (1 <= len(argv) <= 2):
        print("Usage:   %s url [transport]\n" % app_name)
        print("         url of video server")
        print("         transport (optional) specifier for media stream protocol")
        print("         default transport: %s" % transport)
        print("Example: %s rtsp://192.168.0.2/media/video1\n" % app_name)

        return 1

    url: str = argv[0]
    if len(argv) >= 2: transport = argv[1]
    # lcurl.CURLcode res
    sdp_filepath: Path = get_sdp_filepath(url)

    # initialize curl
    res = lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # initialize this curl session
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if res != lcurl.CURLE_OK:
            print("curl_global_init(%s) failed: %d" %
                  ("CURL_GLOBAL_ALL", res), file=sys.stderr)
            return 1
        if not curl:
            print("curl_easy_init() failed", file=sys.stderr)
            return 1

        ver = lcurl.version_info(lcurl.CURLVERSION_NOW).contents
        print("    curl V%s loaded" % ver.version, file=sys.stderr)

        my_curl_easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 0)
        my_curl_easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        my_curl_easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, write_function)
        my_curl_easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, id(sys.stdout))
        my_curl_easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))

        # request server options
        uri = "%s" % url
        rtsp_options(curl, uri)

        # request session description and write response to sdp file
        rtsp_describe(curl, uri, sdp_filepath)

        # get media control attribute from sdp file
        control = get_media_control_attribute(sdp_filepath)

        # setup media stream
        uri = "%s/%s" % (url, control)
        rtsp_setup(curl, uri, transport)

        # start playing media stream
        uri = "%s/" % url
        rtsp_play(curl, uri, transfer_range)
        input("Playing video, press any key to stop ...")
        print()

        # teardown session
        rtsp_teardown(curl, uri)

    return 0


sys.exit(main())
