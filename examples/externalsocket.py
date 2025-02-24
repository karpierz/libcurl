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
Pass in a custom socket for libcurl to use.
"""

import sys
import ctypes as ct
import socket

import libcurl as lcurl
from curl_utils import *  # noqa

if is_windows:
    if not defined("_WINSOCK_DEPRECATED_NO_WARNINGS"):
        _WINSOCK_DEPRECATED_NO_WARNINGS = 1  # for inet_addr()

# The IP address and port number to connect to
IPADDR  = "127.0.0.1"
PORTNUM = 80


@lcurl.opensocket_callback
def open_socket(clientp, purpose, address):
    sock = lcurl.from_oid(clientp)
    # the actual externally set socket is passed in via
    # the OPENSOCKETDATA option
    return sock.fileno()


@lcurl.closesocket_callback
def close_socket(clientp, item):
    sock = lcurl.from_oid(clientp)
    print("libcurl wants to close %d now" % item)
    return 0


@lcurl.sockopt_callback
def sockopt_function(clientp, curlfd, purpose):
    sock = lcurl.from_oid(clientp)
    # This return code was added in libcurl 7.21.5
    return lcurl.CURL_SOCKOPT_ALREADY_CONNECTED


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "http://99.99.99.99:9999"

    # Create the socket "manually"
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    except OSError as exc:
        print("Error creating listening socket.")
        return 3

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with sock, curl_guard(False, curl) as guard:
        if not curl: return 1

        try:
            sock.connect((IPADDR, PORTNUM))
        except OSError as exc:
            print("client error: connect: %s" % exc)
            return 1

        # Note that libcurl internally thinks that you connect to the host and
        # port that you specify in the URL option.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION") and SKIP_PEER_VERIFICATION:
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # no progress meter please
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        # send all data to this function
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, lcurl.write_to_socket)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sock))
        # call this function to get a socket
        lcurl.easy_setopt(curl, lcurl.CURLOPT_OPENSOCKETFUNCTION, open_socket)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_OPENSOCKETDATA, id(sock))
        # call this function to close sockets
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CLOSESOCKETFUNCTION, close_socket)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CLOSESOCKETDATA, id(sock))
        # call this function to set options for the socket
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SOCKOPTFUNCTION, sockopt_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SOCKOPTDATA, id(sock))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 1)

        # Perform the request, res will get the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            print("libcurl error: %d" % res)
            return 4

    return int(res)


sys.exit(main())
