# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

from typing import List, Tuple
import sys
import ctypes as ct

import libcurl as lcurl
from libcurl._platform import defined, is_windows
from libcurl._platform._limits import *  # noqa
from libcurl._ct import c_ptr_add, c_ptr_sub, c_ptr_iadd, c_ptr_isub
if is_windows: from libcurl._platform._windows import _win32 as win32

if is_windows:
    libc = ct.cdll.msvcrt
    libc.strdup = libc._strdup
else:
    libc = ct.CDLL("libc.so.6")

libc.malloc.restype,  libc.malloc.argtypes  = ct.c_void_p, [ct.c_size_t]
libc.calloc.restype,  libc.calloc.argtypes  = ct.c_void_p, [ct.c_size_t, ct.c_size_t]
libc.realloc.restype, libc.realloc.argtypes = ct.c_void_p, [ct.c_void_p, ct.c_size_t]
libc.free.restype,    libc.free.argtypes    = None,        [ct.c_void_p]
libc.strlen.restype,  libc.strlen.argtypes  = ct.c_size_t, [ct.c_char_p]
libc.strdup.restype,  libc.strdup.argtypes  = ct.c_void_p, [ct.c_char_p]

from curl_setup import *
#include "curl_printf.h"


def current_file(level=1):
    from sys import _getframe
    from inspect import getframeinfo
    return getframeinfo(_getframe(level)).filename

def current_line(level=1):
    from sys import _getframe
    from inspect import getframeinfo
    return getframeinfo(_getframe(level)).lineno


def strlen(str):
    try:
        return bytes(str).index(b'\0')
    except ValueError:
        return len(bytes(str))


def file_size(fhandle):
    import os
    return os.fstat(fhandle.fileno()).st_size


class curl_guard:

    class Break(Exception):
      """Break out of the with statement"""

    def __init__(self, gcurl=False, curl=None, mcurl=None, share=None):
        self.gcurl = gcurl
        self.curls = ([] if not curl else
                      list(curl) if isinstance(curl, (List, Tuple)) else
                      [curl])
        self.mcurl = mcurl
        self.share = share
        self.slists = []
        self.mimes  = []

    def add_curl(self, curl):
        if curl: self.curls.append(curl)

    def free_curl(self, curl):
        if not curl: return
        lcurl.easy_cleanup(curl)
        try: self.curls.remove(curl)
        except: pass

    def add_slist(self, slist):
        if slist: self.slists.append(slist)

    def free_slist(self, slist):
        if not slist: return
        lcurl.slist_free_all(slist)
        try: self.slists.remove(slist)
        except: pass

    def add_mime(self, mime):
        if mime: self.mimes.append(mime)

    def free_mime(self, mime):
        if not mime: return
        lcurl.mime_free(mime)
        try: self.mimes.remove(mime)
        except: pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, exc_tb):
        # Always cleanup
        for mime in self.mimes:
            if mime: lcurl.mime_free(mime)
        mime = None ; self.mimes = []
        for slist in self.slists:
            if slist: lcurl.slist_free_all(slist)
        slist = None ; self.slists = []
        if self.mcurl and self.curls:
            for curl in self.curls:
                lcurl.multi_remove_handle(self.mcurl, curl)
        if self.mcurl:
            lcurl.multi_cleanup(self.mcurl)
        self.mcurl = None
        if self.share:
            lcurl.share_cleanup(self.share)
        self.share = None
        if self.curls:
            for curl in self.curls:
                if curl: lcurl.easy_cleanup(curl)
            curl = None
        self.curls = []
        if self.gcurl:
            lcurl.global_cleanup()
        self.gcurl = False

        if exc_type is self.Break:
            return True

#   # proper cleanup sequence
#   print("cleanup: %d %d" % (timercb, socketcb), file=sys.stderr)
#   lcurl.multi_remove_handle(m, curl);
#   lcurl.easy_cleanup(curl)
#   lcurl.multi_cleanup(m)
#   lcurl.global_cleanup()

#                # Close the easy handle *before* the multi handle. Doing it the other
#                # way around avoids the issue.
#                lcurl.easy_cleanup(easy)
#            lcurl.multi_cleanup(multi)  # double-free happens here


def handle_global_init_error(res):
    if res != lcurl.CURLE_OK:
        print("libcurl.global_init() failed (code %d): %s" %
              (res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)


def handle_easy_perform_error(res):
    if res != lcurl.CURLE_OK:
        print("libcurl.easy_perform() failed (code %d): %s" %
              (res, lcurl.easy_strerror(res).decode("utf-8")), file=sys.stderr)
