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
An example of curl_easy_send() and curl_easy_recv() usage.
"""

import sys
import socket
import ctypes as ct

import libcurl as lcurl
from curltestutils import *  # noqa


def wait_on_socket_recv(sock, timeout_ms: int) -> int:
    return wait_on_socket(sock, True, timeout_ms)

def wait_on_socket_send(sock, timeout_ms: int) -> int:
    return wait_on_socket(sock, False, timeout_ms)

def wait_on_socket(sock, for_recv: bool, timeout_ms: int) -> int:
    # Auxiliary function that waits on the socket.

    infd  = [sock] if for_recv else []
    outfd = [] if for_recv else [sock]
    errfd = [sock]  # always check for error

    # select() returns the number of signalled sockets or -1 on error
    try:
        infd, outfd, errfd = select(infd, outfd, errfd, timeout_ms / 1000)
    except:
        return -1 
    return len(infd) + len(outfd) + len(errfd)


def main(argv=sys.argv[1:]):

    url:   str = argv[0] if len(argv) >= 1 else "http://example.com"
    chost: str = ".".join(url.rstrip("/").rpartition("//")[2].rsplit(".", 2)[-2:])

    # Minimalistic http request
    request: bytes = b"GET / HTTP/1.0\r\nHost: %s\r\n\r\n" % chost.encode("utf-8")
    request_len = len(request)

    # A general note of caution here: if you are using curl_easy_recv() or
    # curl_easy_send() to implement HTTP or _any_ other protocol libcurl
    # supports "natively", you are doing it wrong and you should stop.
    #
    # This example uses HTTP only to show how to use this API, it does not
    # suggest that writing an application doing this is sensible.

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return 1

        res: lcurl.CURLcode = lcurl.CURLE_OK

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # Do not do the transfer - only connect to host
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CONNECT_ONLY, 1)

        res = lcurl.easy_perform(curl)
        if res != lcurl.CURLE_OK:
            print("Error: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"))
            return 1

        # Extract the socket from the curl handle - we will need it
        # for waiting.
        sock_fd = lcurl.socket_t()
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_ACTIVESOCKET,
                                 ct.byref(sock_fd))
        if res != lcurl.CURLE_OK:
            print("Error: %s" %
                  lcurl.easy_strerror(res).decode("utf-8"))
            return 1
        sock = socket.socket(fileno=sock_fd.value)

        print("Sending request.")

        nsent_total = 0
        while nsent_total < request_len:
            # Warning: This example program may loop indefinitely.
            # A production-quality program must define a timeout and exit
            # this loop as soon as the timeout has expired.
            while True:
                nsent = ct.c_size_t(0)
                data = request[nsent_total:]
                res = lcurl.easy_send(curl, data, len(data),
                                      ct.byref(nsent))
                nsent = nsent.value
                nsent_total += nsent
                if res != lcurl.CURLE_AGAIN: break

                if wait_on_socket_send(sock, 60 * 1000) == 0:
                    print("Error: timeout.")
                    return 1

            if res != lcurl.CURLE_OK:
                print("Error: %s" %
                      lcurl.easy_strerror(res).decode("utf-8"))
                return 1

            print("Sent:", data)
            print("Sent %u bytes." % nsent)

        print("Reading response.")

        while True:
            # Warning:
            # This example program may loop indefinitely (see above).
            buf = (ct.c_ubyte * 2048)()
            while True:
                nread = ct.c_size_t(0)
                res = lcurl.easy_recv(curl, buf, ct.sizeof(buf),
                                      ct.byref(nread))
                nread = nread.value
                if res != lcurl.CURLE_AGAIN: break

                if wait_on_socket_recv(sock, 60 * 1000) == 0:
                    print("Error: timeout.")
                    return 1

            if res != lcurl.CURLE_OK:
                print("Error: %s" %
                      lcurl.easy_strerror(res).decode("utf-8"))
                return 1  # <AK> fix: was: break

            if nread == 0:
                # end of the response
                break

            print("Response:", bytes(buf[:nread]))
            print("Received %u bytes." % nread)

    return 0


sys.exit(main())
