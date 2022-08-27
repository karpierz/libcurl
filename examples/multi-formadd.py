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
Using the multi interface to do a multipart formpost without blocking
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def main(argv=sys.argv[1:]):

    no_expect_header = True
    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/upload.cgi"

    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    curl:  ct.POINTER(lcurl.CURL)  = lcurl.easy_init()

    with curl_guard(False, curl, mcurl):
        if not curl:  return 1
        if not mcurl: return 2

        # Create the form post
        formpost = ct.POINTER(lcurl.httppost)()
        lastptr  = ct.POINTER(lcurl.httppost)()

        # Fill in the file upload field. This makes libcurl load data
        # from the given file name when libcurl.multi_perform() is called.
        fields1 = (lcurl.forms * 3)()
        fields1[0].option = lcurl.CURLFORM_COPYNAME
        fields1[0].value  = b"sendfile"
        fields1[1].option = lcurl.CURLFORM_FILE
        fields1[1].value  = b"multi-formadd.py"
        fields1[2].option = lcurl.CURLFORM_END
        lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields1)

        # Fill in the filename field
        fields2 = (lcurl.forms * 3)()
        fields2[0].option = lcurl.CURLFORM_COPYNAME
        fields2[0].value  = b"filename"
        fields2[1].option = lcurl.CURLFORM_COPYCONTENTS
        fields2[1].value  = b"multi-formadd.py"
        fields2[2].option = lcurl.CURLFORM_END
        lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields2)

        # Fill in the submit field too, even if this is rarely needed
        fields3 = (lcurl.forms * 3)()
        fields3[0].option = lcurl.CURLFORM_COPYNAME
        fields3[0].value  = b"submit"
        fields3[1].option = lcurl.CURLFORM_COPYCONTENTS
        fields3[1].value  = b"send"
        fields3[2].option = lcurl.CURLFORM_END
        lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields3)

        # what URL that receives this POST
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # initialize custom header list (stating that Expect: 100-continue
        # is not wanted
        headerlist = ct.POINTER(lcurl.slist)()
        headerlist = lcurl.slist_append(headerlist, b"Expect:")
        if no_expect_header:
            # only disable 100-continue header if explicitly requested
            lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, headerlist)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPPOST, formpost)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        lcurl.multi_add_handle(mcurl, curl)

        still_running = ct.c_int(1)
        while still_running.value:
            mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            if still_running.value:
                # wait for activity, timeout or "nothing"
                mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mc:
                break

        # then cleanup the formpost chain
        lcurl.formfree(formpost)
        # free slist
        lcurl.slist_free_all(headerlist)

    return 0


sys.exit(main())
