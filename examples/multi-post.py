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

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/upload.cgi"

    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()
    curl:  ct.POINTER(lcurl.CURL)  = lcurl.easy_init()

    with curl_guard(False, curl, mcurl):
        if not curl or not mcurl: return 1

        # Create the form
        form: ct.POINTER(lcurl.mime) = lcurl.mime_init(curl)
        field = ct.POINTER(lcurl.mimepart)()

        # Fill in the file upload field
        field = lcurl.mime_addpart(form)
        lcurl.mime_name(field, b"sendfile")
        lcurl.mime_filedata(field, b"multi-post.py")

        # Fill in the filename field
        field = lcurl.mime_addpart(form)
        lcurl.mime_name(field, b"filename")
        lcurl.mime_string(field, b"multi-post.py")

        # Fill in the submit field too, even if this is rarely needed
        field = lcurl.mime_addpart(form)
        lcurl.mime_name(field, b"submit")
        lcurl.mime_string(field, b"send")

        # what URL that receives this POST
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        # initialize custom header list (stating that Expect: 100-continue
        # is not wanted
        header_list = ct.POINTER(lcurl.slist)()
        header_list = lcurl.slist_append(header_list, b"Expect:")
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPHEADER, header_list)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_MIMEPOST, form)

        lcurl.multi_add_handle(mcurl, curl)

        still_running = ct.c_int(1)
        while still_running.value:
            mc: int = lcurl.multi_perform(mcurl, ct.byref(still_running))
            if still_running.value:
                # wait for activity, timeout or "nothing"
                mc = lcurl.multi_poll(mcurl, None, 0, 1000, None)
            if mc:
                break

        # then cleanup the form
        lcurl.mime_free(form)
        # free slist
        lcurl.slist_free_all(header_list)

    return 0


sys.exit(main())
