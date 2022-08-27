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
Shows HTTPS usage with client certs and optional ssl engine use.
"""

import sys
import ctypes as ct
from pathlib import Path

import libcurl as lcurl
from curltestutils import *  # noqa

if not lcurl.CURL_AT_LEAST_VERSION(7, 9, 3):
    print("This example requires curl 7.9.3 or later", file=sys.stderr)
    sys.exit(-1)

here = Path(__file__).resolve().parent


HEADER_FILE = here/"output/dumpit"

# some requirements for this to work:
#   1.   set CertFile to the file with the client certificate
#   2.   if the key is passphrase protected, set Passphrase to the
#        passphrase you use
#   3.   if you are using a crypto engine:
#   3.1. set a #define USE_ENGINE
#   3.2. set Engine to the name of the crypto engine you use
#   3.3. set KeyName to the key identifier you want to use
#   4.   if you do not use a crypto engine:
#   4.1. set KeyName to the file name of your client key
#   4.2. if the format of the key file is DER, set KeyType to "DER"
#
#   !! verify of the server certificate is not implemented here !!

Passphrase  = None
CertFile    = "testcert.pem"
CACertFile  = "cacert.pem"
if defined("USE_ENGINE"):
    KeyName = "rsa_test"
    KeyType = "ENG"
    Engine  = "chil"  # for nChiper HSM...
else:
    KeyName = "testkey.pem"
    KeyType = "PEM"
    Engine  = None


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten)
    return nwritten


def main(argv=sys.argv[1:]):

    url: str = (argv[0] if len(argv) >= 1 else
                "HTTPS://your.favourite.ssl.site")

    header_file = HEADER_FILE.open("wb")

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with header_file, curl_guard(True, curl):
        if not curl: return 1

        # what call to write:
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, id(header_file))
        if Engine:
            # use crypto engine
            if lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLENGINE,
                                       Engine.encode("utf-8")) != CURLE_OK:
                # load the crypto engine
                print("cannot set crypto engine", file=sys.stderr)
                return 0  #??? maybe 1 or other > 0 ?
            if lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLENGINE_DEFAULT,
                                       1) != CURLE_OK:
                # set the crypto engine as default
                # only needed for the first time you load
                # a engine in a curl object...
                print("cannot set crypto engine as default", file=sys.stderr)
                return 0  #??? maybe 1 or other > 0 ?
        # cert is stored PEM coded in file...
        # since PEM is default, we needn't set it for PEM
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLCERTTYPE, b"PEM")
        # set the cert for client authentication
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLCERT, CertFile.encode("utf-8"))
        # sorry, for engine we must set the passphrase
        # (if the key has one...)
        if Passphrase:
            curl_easy_setopt(curl, CURLOPT_KEYPASSWD, Passphrase.encode("utf-8"))
        # if we use a key stored in a crypto engine,
        # we must set the key type to "ENG"
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLKEYTYPE, KeyType.encode("utf-8"))
        # set the private key (file or ID in engine)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLKEY, KeyName.encode("utf-8"))
        # set the file with the certs vaildating the server
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CAINFO, CACertFile.encode("utf-8"))
        # disconnect if we cannot validate server's cert
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 1)

        # Perform the request, res will get the return code
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
