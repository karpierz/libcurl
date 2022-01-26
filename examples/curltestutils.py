# Copyright (c) 2021-2022 Adam Karpierz
# Licensed under the MIT License
# https://opensource.org/licenses/MIT

from typing import List, Tuple
import sys
import os
import ctypes as ct

import libcurl as lcurl
from libcurl._platform import defined, is_windows
from _ct import c_ptr_add, c_ptr_sub, c_ptr_iadd, c_ptr_isub
if is_windows: import win32

if is_windows:
    libc = ct.cdll.msvcrt
else:
    libc = ct.CDLL("libc.so.6")


SKIP_PEER_VERIFICATION = 1


def file_size(fhandle):
    return os.fstat(fhandle.fileno()).st_size


def select(rlist, wlist, xlist, timeout=None):
    import select
    if timeout is None:
        return select.select(rlist, wlist, xlist)
    else:
        return select.select(rlist, wlist, xlist, timeout)


class curl_guard:

    def __init__(self, gcurl=False, curl=None, mcurl=None):
        self.gcurl = gcurl
        self.curls = (() if not curl else
                      (curl,) if not isinstance(curl, (List, Tuple)) else
                      curl)
        self.mcurl = mcurl

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc, exc_tb):
        # Always cleanup
        if self.mcurl:
            for curl in self.curls:
                lcurl.multi_remove_handle(self.mcurl, curl)
        if self.mcurl:
            lcurl.multi_cleanup(self.mcurl)
        if self.curls:
            for curl in self.curls:
                lcurl.easy_cleanup(curl)
        if self.gcurl:
            lcurl.global_cleanup()


def handle_global_init_error(res):
    if res != lcurl.CURLE_OK:
        print("libcurl.global_init() failed (code %d): %s" %
              (res, lcurl.easy_strerror(res).decode("utf-8")),
              file=sys.stderr)


def handle_easy_perform_error(res):
    if res != lcurl.CURLE_OK:
        print("libcurl.easy_perform() failed (code %d): %s" %
              (res, lcurl.easy_strerror(res).decode("utf-8")),
              file=sys.stderr)
