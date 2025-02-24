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

from typing import Optional
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa


def loadfile(filename: str) -> Optional[bytes]:
    try:
        with open(filename, "rb") as fi_cert:
            data_size: int = file_size(fi_cert)
            data: bytes = fi_cert.read(data_size)
            if len(data) != data_size:
                return None
    except:
        return None

    return data


def test_cert_blob(URL: str, cafile: str) -> lcurl.CURLcode:

    code: lcurl.CURLcode = lcurl.CURLE_OUT_OF_MEMORY

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(False, curl) as guard:
        if not curl: return lcurl.CURLE_FAILED_INIT

        certdata: Optional[bytes] = loadfile(cafile)
        if certdata is not None:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
            lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER, 1)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT,
                                    b"CURLOPT_CAINFO_BLOB")
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_OPTIONS,
                                    lcurl.CURLSSLOPT_REVOKE_BEST_EFFORT)
            blob = lcurl.blob()
            blob.data  = ct.cast(ct.c_char_p(certdata), ct.c_void_p)
            blob.len   = len(certdata)
            blob.flags = lcurl.CURL_BLOB_COPY
            lcurl.easy_setopt(curl, lcurl.CURLOPT_CAINFO_BLOB, ct.byref(blob))
            certdata = None

            code = lcurl.easy_perform(curl)

    return code


@curl_test_decorator
def test(URL: str, cafile: str = None) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_DEFAULT) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    if URL == "check":

        curl: ct.POINTER(lcurl.CURL) = easy_init()

        with curl_guard(True, curl) as guard:
            if not curl: return TEST_ERR_EASY_INIT

            blob = lcurl.blob(0)
            res = lcurl.easy_setopt(curl, lcurl.CURLOPT_CAINFO_BLOB,
                                    ct.byref(blob))
            if res:
                print("CURLOPT_CAINFO_BLOB is not supported")

    else:

        with curl_guard(True) as guard:
            res = test_cert_blob(URL, cafile)

    return res
