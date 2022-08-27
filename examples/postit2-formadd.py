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
HTTP Multipart formpost with file upload and two additional parts.
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


# Example code that uploads a file name 'foo' to a remote script that accepts
# "HTML form based" (as described in RFC1738) uploads using HTTP POST.
#
# The imaginary form we will fill in looks like:
#
# <form method="post" enctype="multipart/form-data" action="examplepost.cgi">
# Enter file: <input type="file" name="sendfile" size="40">
# Enter file name: <input type="text" name="filename" size="30">
# <input type="submit" value="send" name="submit">
# </form>

def main(argv=sys.argv[1:]):

    no_expect_header = (len(argv) >= 1 and argv[0] == "noexpectheader")
    url: str = argv[1] if len(argv) >= 2 else "https://example.com/examplepost.cgi"

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        # Create the form post
        formpost = ct.POINTER(lcurl.httppost)()
        lastptr  = ct.POINTER(lcurl.httppost)()

        # Fill in the file upload field. This makes libcurl load data
        # from the given file name when libcurl.easy_perform() is called.
        fields1 = (lcurl.forms * 3)()
        fields1[0].option = lcurl.CURLFORM_COPYNAME
        fields1[0].value  = b"sendfile"
        fields1[1].option = lcurl.CURLFORM_FILE
        fields1[1].value  = b"postit2-formadd.py"
        fields1[2].option = lcurl.CURLFORM_END
        lcurl.formadd(ct.byref(formpost), ct.byref(lastptr), fields1)

        # Fill in the filename field
        fields2 = (lcurl.forms * 3)()
        fields2[0].option = lcurl.CURLFORM_COPYNAME
        fields2[0].value  = b"filename"
        fields2[1].option = lcurl.CURLFORM_COPYCONTENTS
        fields2[1].value  = b"postit2-formadd.py"
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

        # Perform the request, res will get the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

        # then cleanup the formpost chain
        lcurl.formfree(formpost)
        # free slist
        lcurl.slist_free_all(headerlist)

    return 0


sys.exit(main())
