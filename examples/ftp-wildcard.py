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
FTP wildcard pattern matching
"""

from dataclasses import dataclass
import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa

here = Path(__file__).resolve().parent


OUT_DIR = here/"output"


@dataclass
class callback_data:
    outstream: object = None


@lcurl.chunk_bgn_callback
def file_is_coming(transfer_info, ptr, remains):
    finfo = ct.cast(transfer_info, ct.POINTER(lcurl.fileinfo)).contents
    data  = lcurl.from_oid(ptr)
    fname = finfo.filename.decode("utf-8")
    global OUT_DIR
 
    print("%3d %40s %10uB " %
          (remains, fname, finfo.size), end="")

    if finfo.filetype == lcurl.CURLFILETYPE_DIRECTORY:
        print(" DIR")
    elif finfo.filetype == lcurl.CURLFILETYPE_FILE:
        print("FILE ", end="")
        # do not transfer files >= 50B
        if finfo.size > 50:
            print("SKIPPED")
            return lcurl.CURL_CHUNK_BGN_FUNC_SKIP
        try:
            data.outstream = (OUT_DIR/fname).open("wb")
        except:
            data.outstream = None
            return lcurl.CURL_CHUNK_BGN_FUNC_FAIL
    else:
        print("OTHER")

    return lcurl.CURL_CHUNK_BGN_FUNC_OK


@lcurl.chunk_end_callback
def file_is_downloaded(stream):
    data = lcurl.from_oid(stream)
    if data.outstream:
        print("DOWNLOADED")
        data.outstream.close()
        data.outstream = None
    return lcurl.CURL_CHUNK_END_FUNC_OK


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    data = lcurl.from_oid(stream)
    file = data.outstream or sys.stdout
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten)
    return nwritten


def main(argv=sys.argv[1:]):

    url: str = (argv[0] if len(argv) >= 1 else # 
                "ftp://example.com/test/*")
               #"ftp://ftp.gnu.org/gnu/binutils/binutils-2.*.tar.bz2")

    # help data
    data = callback_data()

    rc: int = lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if rc: return rc
        if not curl:
            return lcurl.CURLE_OUT_OF_MEMORY

        # set an URL containing wildcard pattern (only in the last part)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # turn on wildcard matching
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WILDCARDMATCH, 1)
        # callback is called before download of concrete file started
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CHUNK_BGN_FUNCTION, file_is_coming)
        # callback is called after data from the file have been transferred
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CHUNK_END_FUNCTION, file_is_downloaded)
        # Define our callback to get called when there's data to be written
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        # put transfer data into callbacks
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CHUNK_DATA, id(data))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA,  id(data))
        # enable progress meter, set to 1 to disable it
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        # Switch on full protocol/debug output
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            # we failed
            handle_easy_perform_error(res)

    return res


sys.exit(main())
