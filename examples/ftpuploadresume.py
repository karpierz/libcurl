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
Upload to FTP, resuming failed transfers. Active mode.
"""

import sys
import ctypes as ct
from pathlib import Path
import io
import re

import libcurl as lcurl
from curl_utils import *  # noqa

here = Path(__file__).resolve().parent

LOCAL_FILE = here/"input/file"


@lcurl.write_callback
def content_len_function(buffer, size, nitems, stream):
    uploaded_len_p = ct.cast(stream, ct.POITER(ct.c_long))
    buffer_size = nitems * size
    # parse headers for Content-Length
    match = re.match(bytes(buffer[:buffer_size]),
                     rb"Content-Length: ([-+]?\d+)\n")
    if match:
        uploaded_len_p.contents.value = int(match.group(1))
    return buffer_size


@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    # read data to upload
    file = lcurl.from_oid(stream)
    #if ferror(file):
    #    return lcurl.CURL_READFUNC_ABORT
    buffer_size = nitems * size
    bread = file.read(buffer_size)
    if not bread: return 0
    nread = len(bread)
    ct.memmove(buffer, bread, nread)
    return nread


def resume_upload(curl: ct.POINTER(lcurl.CURL),
                  url: str, local_path: Path,
                  timeout: int, tries: int) -> bool:
    try:
        local_file = local_path.open("rb")
    except Exception as exc:
        print("{!s}".format(exc))
        return False
    with local_file:

        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if timeout:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SERVER_RESPONSE_TIMEOUT, timeout)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, content_len_function)
        uploaded_len = ct.c_long(0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, ct.byref(uploaded_len))
        # we are not interested in the downloaded data itself
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_skipped)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION,  read_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, id(local_file))
        # enable active mode
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FTPPORT, b"-")
        # allow the server no more than 7 seconds to connect back
        lcurl.easy_setopt(curl, lcurl.CURLOPT_ACCEPTTIMEOUT_MS, 7000)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FTP_CREATE_MISSING_DIRS, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        lcurl.easy_setopt(curl, lcurl.CURLOPT_APPEND, 0)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)
        for _ in range(1, tries):
            if res == lcurl.CURLE_OK: break

            # Are we resuming

            # Determine the length of the file already written.

            # With NOBODY and NOHEADER, libcurl issues a SIZE command, but the only
            # way to retrieve the result is to parse the returned Content-Length
            # header. Thus, getcontentlengthfunc(). We need discardfunc() above
            # because HEADER dumps the headers to stdout without it.
            lcurl.easy_setopt(curl, lcurl.CURLOPT_NOBODY, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)

            res = lcurl.easy_perform(curl)
            if res != lcurl.CURLE_OK:
                continue

            lcurl.easy_setopt(curl, lcurl.CURLOPT_NOBODY, 0)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER, 0)

            local_file.seek(uploaded_len.value, io.SEEK_SET)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_APPEND, 1)

            # Perform the request again
            res = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            print("%s" % lcurl.easy_strerror(res).decode("utf-8"),
                  file=sys.stderr)
            return False

    return True


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "ftp://user:pass@example.com/path/file"

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return 1

        resume_upload(curl, url, LOCAL_FILE, 0, 3)

    return 0


sys.exit(main())
