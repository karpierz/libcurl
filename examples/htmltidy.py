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
Download a document and use libtidy to parse the HTML.
"""

import sys
import ctypes as ct

import libtidy as tidy
from libtidy import TidyDoc, TidyNode, TidyBuffer

import libcurl as lcurl
from curl_utils import *  # noqa


# LibTidy        => https://www.html-tidy.org/
# Python wrapper => https://pypi.org/project/libtidy/

def dumpNode(tdoc: TidyDoc, tnode: TidyNode, indent: int) -> bool:
    # Traverse the document tree
    ind = indent + 1
    child: TidyNode = tidy.GetChild(tnode)
    while child:
        node_name: ctmbstr = tidy.NodeGetName(child)

        if node_name:
            # if it has a name, then it's an HTML tag ...
            print("%*.*s%s" % (ind, ind, "<",
                  node_name.decode("utf-8")), end="")
            # walk the attribute list
            attr: TidyAttr = tidy.AttrFirst(child)
            while attr:
                attr_name  = tidy.AttrName(attr)
                attr_value = tidy.AttrValue(attr)
                print(" %s" % attr_name.decode("utf-8"), end="")
                if attr_value:
                    print('="%s"' % attr_value.decode("utf-8"), end="")
                attr = tidy.AttrNext(attr)
            print(">")
        else:
            # If it does not have a name, then it's probably
            # text, cdata, etc...
            buf = TidyBuffer()
            tidy.BufInit(ct.byref(buf))
            tidy.NodeGetText(tdoc, child, ct.byref(buf))
            node_text = (bytes(buf.bp[:buf.size]).decode("utf-8")
                         if buf.bp else "")
            print("%*.*s%s" % (ind, ind, "", node_text))
            tidy.BufFree(ct.byref(buf))

        dumpNode(tdoc, child, indent + 4)  # recursive

        if node_name:
            # end of HTML tag ...
            print("%*.*s%s>" % (ind + 1, ind + 1, "</",
                  node_name.decode("utf-8")))

        child = tidy.GetNext(child)

# libcurl variables for error strings and returned data
#
error_buffer = (ct.c_char * lcurl.CURL_ERROR_SIZE)()


@lcurl.write_callback
def write_function(buffer, size, nitems, userp):
    # curl write callback, to fill tidy's input buffer...
    tidy_docbuf = ct.cast(userp, ct.POINTER(TidyBuffer)).contents
    buffer_size = nitems * size
    tidy.BufAppend(ct.byref(tidy_docbuf), buffer, buffer_size)
    return buffer_size


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 1:
        print("Usage: python %s <URL>" % app_name)
        return 1

    url: str = argv[0]

    tidy_docbuf = TidyBuffer(None)
    tidy_errbuf = TidyBuffer(None)
    tidy_tdoc: TidyDoc = tidy.Create()
    tidy.OptSetBool(tidy_tdoc,tidy.TidyForceOutput, True)  # try harder
    tidy.OptSetInt(tidy_tdoc, tidy.TidyWrapLen, 4096)
    tidy.SetErrorBuffer(tidy_tdoc, ct.byref(tidy_errbuf))
    tidy.BufInit(ct.byref(tidy_docbuf))

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) as guard:

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_ERRORBUFFER, error_buffer)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, ct.byref(tidy_docbuf))

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            print("%s", error_buffer.raw.decode("utf-8"), file=sys.stderr)
            raise guard.Break

        err: int = tidy.ParseBuffer(tidy_tdoc, ct.byref(tidy_docbuf))  # parse the input
        if err >= 0:
            err = tidy.CleanAndRepair(tidy_tdoc)  # fix any problems
        if err >= 0:
            err = tidy.RunDiagnostics(tidy_tdoc)  # load tidy error buffer
        if err >= 0:
            dumpNode(tidy_tdoc, tidy.GetRoot(tidy_tdoc), 0)  # walk the tree
            err_info = bytes(tidy_errbuf.bp[:tidy_errbuf.size]).decode("utf-8")
            print("%s" % err_info, file=sys.stderr)  # show errors

    # clean-up
    tidy.BufFree(ct.byref(tidy_docbuf))
    tidy.BufFree(ct.byref(tidy_errbuf))
    tidy.Release(tidy_tdoc)

    return err


sys.exit(main())
