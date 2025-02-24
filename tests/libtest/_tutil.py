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

import libcurl as lcurl
from libcurl._platform import is_windows


def tvnow() -> lcurl.timeval:
    # Returns: current monotonic time as lcurl.timeval structure.
    #
    nanoseconds = time.monotonic_ns()
    return lcurl.timeval(tv_sec =(nanoseconds // 1_000_000_000),
                         tv_usec=(nanoseconds %  1_000_000_000) // 1000)


def tvdiff(newer: lcurl.timeval, older: lcurl.timeval) -> int:
    # Make sure that the first argument is the more recent time,
    # as otherwise we'll get a weird negative time-diff back...
    #
    # Returns: the time difference in number of milliseconds.
    #
    return (int(newer.tv_sec  - older.tv_sec)  *  1000 +
            int(newer.tv_usec - older.tv_usec) // 1000)


def tvdiff_secs(newer: lcurl.timeval, older: lcurl.timeval) -> float:
    # Same as tvdiff but with full usec resolution.
    #
    # Returns: the time difference in seconds with subsecond resolution.
    #
    return (float(newer.tv_sec  - older.tv_sec) +
            float(newer.tv_usec - older.tv_usec) / 1_000_000.0)

if is_windows:

    def win32_load_system_library(filename: str): # -> HMODULE:
        """ """
        """
        # ifdef CURL_WINDOWS_UWP
            (void)filename;
            return NULL;
        # else
            filename_len  = _tcslen(filename);
            systemdir_len = GetSystemDirectory(NULL, 0);
            size_t written;
            TCHAR *path;

            if (filename_len  == 0 || filename_len  > 32768 ||
                systemdir_len == 0 || systemdir_len > 32768):
                return None

            # systemdir_len includes null character
            path = malloc(sizeof(TCHAR) * (systemdir_len + 1 + filename_len));
            if(!path)
                return None

            # if written >= systemdir_len then nothing was written
            written = GetSystemDirectory(path, (unsigned int)systemdir_len);
            if(!written || written >= systemdir_len)
                return None

            if(path[written - 1] != _T('\\'))
                path[written++] = _T('\\');

            _tcscpy(path + written, filename);

            return LoadLibrary(path);
        # endif
        """

# endif
