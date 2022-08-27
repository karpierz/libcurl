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
Upload to SFTP, resuming a previously aborted transfer.
"""

import sys
import io
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa

here = Path(__file__).resolve().parent


LOCAL_FILE = here/"input/file"


@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    # read data to upload
    file = lcurl.from_oid(stream)
    #if ferror(file):
    #    return lcurl.CURL_READFUNC_ABORT
    bread = file.read(size * nitems)
    if not bread: return 0
    nread = len(bread)
    ct.memmove(buffer, bread, nread)
    return nread


def get_remote_file_size(url: str) -> int:
    # Returns the remote file size in byte; -1 on error

    file_size = lcurl.off_t(-1)

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return -1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOBODY, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FILETIME, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        if res == lcurl.CURLE_OK:
            res = lcurl.easy_getinfo(curl,
                                     lcurl.CURLINFO_CONTENT_LENGTH_DOWNLOAD_T,
                                     ct.byref(file_size))
            if res:
                return -1

            print("filesize: %u" % file_size.value)

    return file_size.value


def resume_upload(curl: ct.POINTER(lcurl.CURL),
                  url: str, local_path: Path,
                  timeout: int, tries: int) -> bool:

    remote_file_size = get_remote_file_size(url)
    if remote_file_size == -1:
        print("Error reading the remote file size: unable to resume upload")
        return -1

    try:
        local_file = local_path.open("rb")
    except Exception as exc:
        print("{!s}".format(exc))
        return False
    with local_file:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_UPLOAD, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION, read_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_READDATA, id(local_file))

        local_file.seek(remote_file_size, io.SEEK_SET)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_APPEND, 1)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            print("%s" % lcurl.easy_strerror(res).decode("utf-8"),
                  file=sys.stderr)
            return False

    return True


def main(argv=sys.argv[1:]):

    url: str = (argv[0] if len(argv) >= 1 else
                "sftp://user:pass@example.com/path/filename")

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        if not resume_upload(curl, url, LOCAL_FILE, 0, 3):
            print("resumed upload using curl %s failed" %
                  lcurl.version().decode("utf-8"))

    return 0


sys.exit(main())
