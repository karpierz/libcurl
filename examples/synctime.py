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

"""
Set your system time from a remote HTTP server's Date: header.
"""

# This example code only builds as-is on Windows.

# Synchronising your computer clock via Internet time server usually relies
# on DAYTIME, TIME, or NTP protocols. These protocols provide good accurate
# time synchronization but it does not work well through a firewall/proxy.
# Some adjustment has to be made to the firewall/proxy for these protocols to
# work properly.
#
# There is an indirect method. Since most webserver provide server time in
# their HTTP header, therefore you could synchronise your computer clock
# using HTTP protocol which has no problem with firewall/proxy.
#
# For this software to work, you should take note of these items.
# 1. Your firewall/proxy must allow your computer to surf Internet.
# 2. Webserver system time must in sync with the NTP time server,
#    or at least provide an accurate time keeping.
# 3. Webserver HTTP header does not provide the milliseconds units,
#    so there is no way to get an accurate time.
# 4. This software could only provide an accuracy of +- a few seconds,
#    as Round-Trip delay time is not taken into consideration.
#    Compensation of network, firewall/proxy delay cannot be simply divide
#    the Round-Trip delay time by half.
# 5. Win32 SetSystemTime() API sets your computer clock according to
#    GMT/UTC time. Therefore your computer timezone must be properly set.
# 6. Webserver data should not be cached by the proxy server. Some
#    webserver provide Cache-Control to prevent caching.
#
# Usage:
# This software synchronises your computer clock only when you issue
# it with --synctime. By default, it only display the webserver's clock.
#
# Written by: Frank (contributed to libcurl)
#
# THE SOFTWARE IS PROVIDED "AS-IS" AND WITHOUT WARRANTY OF ANY KIND,
# EXPRESS, IMPLIED OR OTHERWISE, INCLUDING WITHOUT LIMITATION, ANY
# WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
#
# IN NO EVENT SHALL THE AUTHOR OF THIS SOFTWARE BE LIABLE FOR
# ANY SPECIAL, INCIDENTAL, INDIRECT OR CONSEQUENTIAL DAMAGES OF ANY KIND,
# OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER OR NOT ADVISED OF THE POSSIBILITY OF DAMAGE, AND ON ANY THEORY OF
# LIABILITY, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.

import sys
import ctypes as ct
from dataclasses import dataclass
import time
import re

import libcurl as lcurl
from curl_utils import *  # noqa

if not is_windows:
    print("This example requires Windows.", file=sys.stderr)
    sys.exit(0)


@dataclass
class conf_t:
    http_proxy: str = ""
    proxy_user: bytearray = bytearray(256 + 1)
    timeserver: str = ""


DEFAULT_TIME_SERVERS = [
    "https://nist.time.gov/",
    "https://www.google.com/",
    None,
]

SYNCTIME_UA = "synctime/1.0"

DAY_STR = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MTH_STR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

HTTP_COMMAND_HEAD = 0
HTTP_COMMAND_GET  = 1

show_all_header: int = 0
auto_sync_time:  int = 0
SYSTEM_Time: win32.SYSTEMTIME = win32.SYSTEMTIME()
LOCAL_Time:  win32.SYSTEMTIME = win32.SYSTEMTIME()


@lcurl.write_callback
def SyncTime_CURL_WriteHeader(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = nitems * size
    buffer = bytes(buffer[:buffer_size])

    global show_all_header
    global auto_sync_time
    global SYSTEM_Time

    if show_all_header == 1:
        print("%s" % buffer.decode("utf-8"), end="", file=sys.stderr)

    if buffer[:5] == b"Date:":

        if show_all_header == 0:
            print("HTTP Server. %s" % buffer.decode("utf-8"), end="", file=sys.stderr)

        if auto_sync_time == 1:
            if strlen(buffer) > 50:  # Can prevent buffer overflow to TmpStr1 & 2?
                auto_sync_time = 0
            else:
                pattern = re.compile(rb"Date: \w{25} (\d+) (\w+) (\d+) (\d+):(\d+):(\d+)")
                match = pattern.match(buffer)
                if match:
                    SYSTEM_Time.wDay    = int(match.group(1))
                    SYSTEM_Time.wMonth  = MTH_STR.index(match.group(2).decode("utf-8")) + 1
                    SYSTEM_Time.wYear   = int(match.group(3))
                    SYSTEM_Time.wHour   = int(match.group(4))
                    SYSTEM_Time.wMinute = int(match.group(5))
                    SYSTEM_Time.wSecond = int(match.group(6))
                    SYSTEM_Time.wMilliseconds = 500  # adjust to midpoint, 0.5 sec
                    auto_sync_time = 3  # Computer clock is adjusted
                else:
                    auto_sync_time = 0  # Error in sscanf() fields conversion

    if buffer[:12] == b"X-Cache: HIT":
        print("ERROR: HTTP Server data is cached."
              " Server Date is no longer valid.", file=sys.stderr)
        auto_sync_time = 0

    return buffer_size


def SyncTime_CURL_Init(curl: ct.POINTER(lcurl.CURL), proxy: str, proxy_login: bytearray):
    """ """
    if proxy:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PROXY, proxy.encode("utf-8"))
    if proxy_login:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_PROXYUSERPWD, bytes(proxy_login))
    lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, SYNCTIME_UA.encode("utf-8"))
    lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_to_file)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, SyncTime_CURL_WriteHeader)


def SyncTime_CURL_Fetch(curl: ct.POINTER(lcurl.CURL),
                        URL: str, out_filename: str, http_get_body: int) -> lcurl.CURLcode:
    res: lcurl.CURLcode

    out_file = None
    if http_get_body == HTTP_COMMAND_HEAD:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOBODY, 1)
    else:
        out_file = open(out_filename, "wb")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(out_file))
    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))

    res = lcurl.easy_perform(curl)

    if out_file:
        out_file.close()

    return lcurl.CURLcode(res)  # (CURLE_OK)


def show_usage():
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]
    print("synctime: Synchronising computer clock with time server"
          " using HTTP protocol.", file=sys.stderr)
    print("Usage   : python %s [Option]" % app_name, file=sys.stderr)
    print("Options :", file=sys.stderr)
    print(" --server=WEBSERVER        Use this time server instead of default.",
          file=sys.stderr)
    print(" --showall                 Show all HTTP header.",
          file=sys.stderr)
    print(" --synctime                Synchronising computer clock with time "
          "server.", file=sys.stderr)
    print(" --proxy-user=USER[:PASS]  Set proxy username and password.",
          file=sys.stderr)
    print(" --proxy=HOST[:PORT]       Use HTTP proxy on given port.",
          file=sys.stderr)
    print(" --help                    Print this help.", file=sys.stderr)
    print(file=sys.stderr)


def conf_init(conf: conf_t) -> int:
    """ """
    conf.http_proxy = ""
    # Clean up password from memory
    conf.proxy_user[:] = bytearray(b'\0' * len(conf.proxy_user))
    conf.proxy_user[:] = b'\0'
    conf.timeserver = ""

    return 1


def main(argv=sys.argv[1:]):

    import time

    ret_value = 0  # Successful Exit

    global SYSTEM_Time
    global LOCAL_Time

    global show_all_header
    global auto_sync_time
    show_all_header = 0  # Do not show HTTP Header
    auto_sync_time  = 0  # Do not synchronise computer clock

    conf = conf_t()
    conf_init(conf)

    for arg in argv:
        if arg[:9] == "--server=":
            conf.timeserver = "%s" % arg[9:]
        if arg == "--showall":
            show_all_header = 1
        if arg == "--synctime":
            auto_sync_time = 1
        if arg[:13] == "--proxy-user=":
            conf.proxy_user = bytearray(b"%s\0" %
                              arg[13:].encode("utf-8"))
        if arg[:8] == "--proxy=":
            conf.http_proxy = "%s" % arg[8:]
        if arg in ("--help", "/?"):
            show_usage()
            return 0

    if not conf.timeserver:  # Use default server for time information
        conf.timeserver = "%s" % DEFAULT_TIME_SERVERS[0]

    # Init CURL before usage
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()
    if not curl:
        conf_init(conf)
        return 1

    with curl_guard(True, curl) as guard:

        SyncTime_CURL_Init(curl, conf.http_proxy, conf.proxy_user)

        # Calculating time diff between GMT and localtime
        tt = time.time()
        lt:  time.struct_time = time.localtime(tt)
        gmt: time.struct_time = time.gmtime(tt)
        tt_local: float = time.mktime(lt)
        tt_gmt:   float = time.mktime(gmt)
        tzone_diff_secs: float = tt_local - tt_gmt  # difftime(tt_local, tt_gmt)
        tzone_diff_hours:  int = int(tzone_diff_secs / 3600.0)
        if float(tzone_diff_hours * 3600) == tzone_diff_secs:
            timezone = "%+03d'00'" % tzone_diff_hours
        else:
            timezone = "%+03d'30'" % tzone_diff_hours

        # Get current system time
        win32.GetSystemTime(ct.byref(SYSTEM_Time))

        # Get current local time before
        win32.GetLocalTime(ct.byref(LOCAL_Time))
        time = "%s, %02d %s %04d %02d:%02d:%02d.%03d, " % (
               DAY_STR[LOCAL_Time.wDayOfWeek], LOCAL_Time.wDay,
               MTH_STR[LOCAL_Time.wMonth - 1], LOCAL_Time.wYear,
               LOCAL_Time.wHour, LOCAL_Time.wMinute, LOCAL_Time.wSecond,
               LOCAL_Time.wMilliseconds)

        print("Fetch: %s\n" % conf.timeserver, file=sys.stderr)
        print("Before HTTP. Date: %s%s\n" % (time, timezone), file=sys.stderr)

        # HTTP HEAD command to the Webserver
        SyncTime_CURL_Fetch(curl, conf.timeserver, "index.htm", HTTP_COMMAND_HEAD)

        # Get current local time after
        win32.GetLocalTime(ct.byref(LOCAL_Time))
        time = "%s, %02d %s %04d %02d:%02d:%02d.%03d, " % (
               DAY_STR[LOCAL_Time.wDayOfWeek], LOCAL_Time.wDay,
               MTH_STR[LOCAL_Time.wMonth - 1], LOCAL_Time.wYear,
               LOCAL_Time.wHour, LOCAL_Time.wMinute, LOCAL_Time.wSecond,
               LOCAL_Time.wMilliseconds)
        print("\nAfter  HTTP. Date: %s%s" % (time, timezone), file=sys.stderr)

        if auto_sync_time == 3:

            # Synchronising computer clock
            if not win32.SetSystemTime(ct.byref(SYSTEM_Time)):  # Set system time
                print("ERROR: Unable to set system time.", file=sys.stderr)
                conf_init(conf)
                return 1

            # Successfully re-adjusted computer clock
            win32.GetLocalTime(ct.byref(LOCAL_Time))
            time = "%s, %02d %s %04d %02d:%02d:%02d.%03d, " % (
                   DAY_STR[LOCAL_Time.wDayOfWeek], LOCAL_Time.wDay,
                   MTH_STR[LOCAL_Time.wMonth - 1], LOCAL_Time.wYear,
                   LOCAL_Time.wHour, LOCAL_Time.wMinute, LOCAL_Time.wSecond,
                   LOCAL_Time.wMilliseconds)
            print("\nNew System's Date: %s%s" % (time, timezone), file=sys.stderr)

        # Cleanup before exit
        conf_init(conf)

    return ret_value


sys.exit(main())
