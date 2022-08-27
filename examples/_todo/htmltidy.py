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
Download a document and use libtidy to parse the HTML.
"""

import sys
import ctypes as ct
#include <tidy/tidy.h>
#include <tidy/tidybuffio.h>
TidyDoc    = str  # !!!
TidyNode   = str  # !!!
TidyNode   = str  # !!!
TidyBuffer = str  # !!!

import libcurl as lcurl
from curltestutils import *  # noqa


#
# LibTidy => https://www.html-tidy.org/
#

def dumpNode(tdoc: TidyDoc, tnode: TidyNode, indent: int):
    # Traverse the document tree
    child: TidyNode = tidyGetChild(tnode)
    while child:
        name: ctmbstr = tidyNodeGetName(child)

        if name:
            # if it has a name, then it's an HTML tag ...
            print("%*.*s%s " % (indent, indent, "<", name), end="")
            # walk the attribute list
            attr: TidyAttr = tidyAttrFirst(child)
            while attr:
                attr_name  = tidyAttrName(attr)
                attr_value = tidyAttrValue(attr)
                print("%s" % attr_name, end="")
                if attr_value:
                    print('="%s" ' % attr_value, end="")
                else:
                    print(" ", end="")
                attr = tidyAttrNext(attr)
            print(">")
        else:
            # if it does not have a name, then it's probably text, cdata, etc...
            buf = TidyBuffer()
            tidyBufInit(cy.byref(buf))
            tidyNodeGetText(tdoc, child, cy.byref(buf))
            print("%*.*s" % (indent, indent, buf.bp or "")) # (char *)buf.bp
            tidyBufFree(cy.byref(buf))

        dumpNode(tdoc, child, indent + 4)  # recursive
        child = tidyGetNext(child)


#
# libcurl variables for error strings and returned data

error_buffer = (ct.c_char * lcurl.CURL_ERROR_SIZE)()


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    # curl write callback, to fill tidy's input buffer...
    tidy_docbuf = lcurl.from_oid(stream)
    buffer_size = size * nitems
    tidyBufAppend(cy.byref(tidy_docbuf), buffer, buffer_size)
    return buffer_size


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 1:
        print("Usage: %s <URL>" % app_name)
        return 1

    url: str = argv[0]

    tidy_docbuf = TidyBuffer(0)
    tidy_errbuf = TidyBuffer(0)
    tidy_tdoc: TidyDoc = tidyCreate()
    tidyOptSetBool(tidy_tdoc, TidyForceOutput, yes)  # try harder
    tidyOptSetInt(tidy_tdoc, TidyWrapLen, 4096)
    tidySetErrorBuffer(tidy_tdoc, cy.byref(tidy_errbuf))
    tidyBufInit(cy.byref(tidy_docbuf))

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_ERRORBUFFER, error_buffer)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(tidy_docbuf))

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            print("%s", error_buffer.raw.decode("utf-8"), file=sys.stderr)
        else:
            err: int = tidyParseBuffer(tidy_tdoc, cy.byref(tidy_docbuf))  # parse the input
            if err >= 0:
                err = tidyCleanAndRepair(tidy_tdoc)  # fix any problems
            if err >= 0:
                err = tidyRunDiagnostics(tidy_tdoc)  # load tidy error buffer
            if err >= 0:
                dumpNode(tidy_tdoc, tidyGetRoot(tidy_tdoc), 0)  # walk the tree
                print("%s" % tidy_errbuf.bp, file=sys.stderr)  # show errors

    # clean-up
    tidyBufFree(cy.byref(tidy_docbuf))
    tidyBufFree(cy.byref(tidy_errbuf))
    tidyRelease(tidy_tdoc)

    return err


sys.exit(main())
