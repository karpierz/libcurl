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
HTTP/2 server push
"""

import sys
import ctypes as ct

import libcurl as lcurl
from curl_utils import *  # noqa
from utils import dump

#ifndef lcurl.CURLPIPE_MULTIPLEX
#error "too old libcurl, cannot do HTTP/2 server push!"
#endif


int my_trace(CURL *handle, type: lcurl.infotype,
             char *data, size_t size,
             void *userp):
    if type == lcurl.CURLINFO_TEXT:
        print("== Info: %s" % data, end="", file=sys.stderr)
        return 0
    elif type == lcurl.CURLINFO_HEADER_OUT:   text = "=> Send header"
    elif type == lcurl.CURLINFO_DATA_OUT:     text = "=> Send data"
    elif type == lcurl.CURLINFO_SSL_DATA_OUT: text = "=> Send SSL data"
    elif type == lcurl.CURLINFO_HEADER_IN:    text = "<= Recv header"
    elif type == lcurl.CURLINFO_DATA_IN:      text = "<= Recv data"
    elif type == lcurl.CURLINFO_SSL_DATA_IN:  text = "<= Recv SSL data"
    else: return 0  # in case a new one is introduced to shock us
    dump(text, (unsigned char *)data, size, 1)

    return 0


OUTPUTFILE = "download_0.data"


def setup(easy: CURL *, url: str) -> int:

    try:
        FILE * out = open(OUTPUTFILE, "wb")
    except:
        # failed
        return 1

    lcurl.easy_setopt(easy, lcurl.CURLOPT_URL, url.encode("utf-8"))
    lcurl.easy_setopt(easy, lcurl.CURLOPT_HTTP_VERSION,
                            lcurl.CURL_HTTP_VERSION_2_0)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_WRITEDATA, out);
    # please be verbose
    lcurl.easy_setopt(easy, lcurl.CURLOPT_VERBOSE, 1)
    lcurl.easy_setopt(easy, lcurl.CURLOPT_DEBUGFUNCTION, my_trace)

    if lcurl.CURLPIPE_MULTIPLEX > 0:
        # wait for pipe connection to confirm
        lcurl.easy_setopt(easy, lcurl.CURLOPT_PIPEWAIT, 1)

    return 0  # all is good


count: int = 0

# called when there's an incoming push
def server_push_callback(CURL *parent,
                         CURL *easy,
                         size_t num_headers,
                         struct curl_pushheaders *headers,
                         void *userp) -> int:

    transfersp = ct.cast(userp, ct.POINTER(ct.c_int))

    global count

    filename: str = "push%u" % count
    count += 1

    # here's a new stream, save it in a new file for each new push
    try:
        FILE * out = open(filename, "wb")
    except:
        # if we cannot save it, deny it
        print("Failed to create output file for push", file=sys.stderr)
        return lcurl.CURL_PUSH_DENY

    # write to this file
    lcurl.easy_setopt(easy, lcurl.CURLOPT_WRITEDATA, out);

    print("**** push callback approves stream %u, got %u headers!" %
          (count, num_headers), file=sys.stderr)

    for i in range(num_headers):
        headp = lcurl.pushheader_bynum(headers, i)
        print("**** header %u: %s" % (i, headp.encode("utf-8")),
              file=sys.stderr)

    headp = lcurl.pushheader_byname(headers, b":path")
    if headp:
        print("**** The PATH is %s" % headp.encode("utf-8"),  # skip :path + colon
              file=sys.stderr)

    transfersp.contents += 1  # one more

    return lcurl.CURL_PUSH_OK


#
# Download a file over HTTP/2, take care of server push.
#

def main(argv=sys.argv[1:]) -> int:

    struct CURLMsg *m;

    if len(argv) != 1:
        print("need URL as argument", file=sys.stderr)
        return 2

    url: str = argv[0]

    int transfers = 1;  # we start with one

    multi_handle: CURLM * = lcurl.multi_init()
    lcurl.multi_setopt(multi_handle, lcurl.CURLMOPT_PIPELINING,
                                     lcurl.CURLPIPE_MULTIPLEX)
    lcurl.multi_setopt(multi_handle, lcurl.CURLMOPT_PUSHFUNCTION,
                                     server_push_callback)
    lcurl.multi_setopt(multi_handle, lcurl.CURLMOPT_PUSHDATA,
                                     &transfers)

    easy: lcurl.POINTER(lcurl.CURL) = lcurl.easy_init()
    if setup(easy, url):
        print("failed", file=sys.stderr)
        return 1

    lcurl.multi_add_handle(multi_handle, easy)
    while transfers.value:  # as long as we have transfers going

        still_running = ct.c_int()  # keep number of running handles
        mc: lcurl.CURLMcode = lcurl.multi_perform(multi_handle, ct.byref(still_running))
        # wait for activity, timeout or "nothing"
        if still_running.value: mc = lcurl.multi_poll(multi_handle, None, 0, 1000, None)
        if mc:
            break

        # A little caution when doing server push is that libcurl itself has
        # created and added one or more easy handles but we need to clean them up
        # when we are done.
        while True:
            msgq = ct.c_int(0)
            m = curl_multi_info_read(multi_handle, ct.byref(msgq))
            if not m: break

            if m->msg == CURLMSG_DONE:
                CURL *e = m->easy_handle;
                transfers.value -= 1
                lcurl.multi_remove_handle(multi_handle, e)
                lcurl.easy_cleanup(e)

    lcurl.multi_cleanup(multi_handle)

    return 0


sys.exit(main())
