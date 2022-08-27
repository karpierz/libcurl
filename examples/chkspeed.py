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
Show transfer timing info after download completes.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


# Example source code to show how the callback function can be used to
# download data into a chunk of memory instead of storing it in a file.
# After successful download we use curl_easy_getinfo() calls to get the
# amount of downloaded bytes, the time used for the whole download, and
# the average download speed.
# On Linux you can create the download test files with:
# dd if=/dev/urandom of=file_1M.bin bs=1M count=1

URL_BASE = "http://speedtest.your.domain/"
URL_1M   = URL_BASE + "file_1M.bin"
URL_2M   = URL_BASE + "file_2M.bin"
URL_5M   = URL_BASE + "file_5M.bin"
URL_10M  = URL_BASE + "file_10M.bin"
URL_20M  = URL_BASE + "file_20M.bin"
URL_50M  = URL_BASE + "file_50M.bin"
URL_100M = URL_BASE + "file_100M.bin"

CHKSPEED_VERSION = "1.0"


@lcurl.write_callback
def write_skipped(buffer, size, nitems, stream):
    # we are not interested in the downloaded data itself,
    # so we only return the size we would have saved ...
    return size * nitems


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    prtall   = False
    prtsep   = False
    prttime  = False
    url: str = URL_1M
    # parse input parameters
    for arg in argv:
        if arg[0] == "-":
            uarg = arg.upper()
            if uarg == "-H":
                print("\rUsage: %s [-h] [-v] [-m=1|2|5|10|20|50|100] [-a] [-x] [-t] [url]" %
                      app_name, file=sys.stderr)
                return 1
            elif uarg == "-V":
                print("\r%s %s - %s" %
                      (app_name, CHKSPEED_VERSION, lcurl.version().decode("utf-8")),
                      file=sys.stderr)
                return 1
            elif uarg == "-A":
                prtall = True
            elif uarg == "-X":
                prtsep = True
            elif uarg == "-T":
                prttime = True
            elif uarg[:3] == "-M=":
                try:
                    m = int(arg[3:])
                except:
                    print("\r%s: invalid parameter %s" %
                          (app_name, arg[3:]), file=sys.stderr)
                    return 1
                if   m == 1:   url = URL_1M
                elif m == 2:   url = URL_2M
                elif m == 5:   url = URL_5M
                elif m == 10:  url = URL_10M
                elif m == 20:  url = URL_20M
                elif m == 50:  url = URL_50M
                elif m == 100: url = URL_100M
                else:
                    print("\r%s: invalid parameter %s" %
                          (app_name, arg[3:]), file=sys.stderr)
                    return 1
            else:
                print("\r%s: invalid or unknown option %s" %
                      (app_name, arg), file=sys.stderr)
                return 1
        else:
            url = arg

    # print separator line
    if prtsep:
        print("-" * 49)
    # print localtime
    if prttime:
        print("Localtime: %s" % time.ctime())

    # init libcurl
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    # init the curl session
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        # specify URL to get
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # send all data to this function 
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_skipped)
        # some servers do not like requests that are made without a user-agent
        # field, so we provide one
        lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT,
                          b"libcurl-speedchecker/" + CHKSPEED_VERSION.encode("utf-8"))

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        if res != lcurl.CURLE_OK:
            print("Error while fetching '%s' : %s" %
                  (url, lcurl.easy_strerror(res).decode("utf-8")),
                  file=sys.stderr)
        else:
            val = lcurl.off_t()

            # check for bytes downloaded
            res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_SIZE_DOWNLOAD_T,
                                     ct.byref(val))
            value = val.value
            if res == lcurl.CURLE_OK and value > 0:
                print("Data downloaded: %u bytes." % value)

            # check for total download time
            res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_TOTAL_TIME_T,
                                     ct.byref(val))
            value = val.value
            if res == lcurl.CURLE_OK and value > 0:
                print("Total download time: %u.%06u sec." %
                      (value // 1000000, value % 1000000))

            # check for average download speed
            res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_SPEED_DOWNLOAD_T,
                                     ct.byref(val))
            value = val.value
            if res == lcurl.CURLE_OK and value > 0:
                print("Average download speed: %u kbyte/sec." %
                      (value // 1024))

            if prtall:
                # check for name resolution time
                res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_NAMELOOKUP_TIME_T,
                                         ct.byref(val))
                value = val.value
                if res == lcurl.CURLE_OK and value > 0:
                  print("Name lookup time: %u.%06u sec." %
                        (value // 1000000, value % 1000000))

                # check for connect time
                res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_CONNECT_TIME_T,
                                         ct.byref(val))
                value = val.value
                if res == lcurl.CURLE_OK and value > 0:
                  print("Connect time: %u.%06u sec." %
                        (value // 1000000, value % 1000000))

    return 0


sys.exit(main())
