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

import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa


def is_chain_in_order(cert_info: lcurl.certinfo) -> bool:
    # Verify correct order of certificates in the chain by comparing the
    # subject and issuer attributes of each certificate.

    # Chains with only a single certificate are always in order
    if cert_info.num_of_certs <= 1:
        return True

    subject_prefix = b"Subject:"
    issuer_prefix  = b"Issuer:"

    # Enumerate each certificate in the chain
    last_issuer = None
    for cert in range(cert_info.num_of_certs):

        # Find the certificate issuer and subject by enumerating each field
        subject = None
        issuer  = None
        slist: ct.POINTER(lcurl.slist) = cert_info.certinfo[cert]
        while slist and not (subject and issuer):
            slist = slist.contents
            data = slist.data
            if data.startswith(subject_prefix):
                subject = data[len(subject_prefix):]
            if data.startswith(issuer_prefix):
                issuer = data[len(issuer_prefix):]
            slist = slist.next

        if subject and issuer:
            print("cert %d" % cert)
            print("  subject: %s" % subject.decode("utf-8"))
            print("  issuer: %s" % issuer.decode("utf-8"))
            if last_issuer:
                # If the last certificate's issuer matches the current certificate's
                # subject, then the chain is in order
                if last_issuer != subject:
                    print("cert %d issuer does not match cert %d subject" %
                          (cert - 1, cert), file=sys.stderr)
                    print("certificate chain is not in order", file=sys.stderr)
                    return False

        last_issuer = issuer

    print("certificate chain is in order")

    return True


@lcurl.write_callback
def wrfu(buffer, size, nitems, userp):
    return size * nitems


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    res: lcurl.CURLcode = lcurl.CURLE_OK

    if global_init(lcurl.CURL_GLOBAL_ALL) != lcurl.CURLE_OK:
        return TEST_ERR_MAJOR_BAD

    curl: ct.POINTER(lcurl.CURL) = easy_init()

    with curl_guard(True, curl) as guard:
        if not curl: return TEST_ERR_EASY_INIT

        # Set the HTTPS url to retrieve.
        test_setopt(curl, lcurl.CURLOPT_URL, URL.encode("utf-8"))
        # Capture certificate information
        test_setopt(curl, lcurl.CURLOPT_CERTINFO, 1)
        # Ignore output
        test_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, wrfu)
        # No peer verify
        test_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        test_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)

        # Perform the request, res will get the return code
        res = lcurl.easy_perform(curl)
        if (res != lcurl.CURLE_OK and
            res != lcurl.CURLE_GOT_NOTHING): raise guard.Break

        cert_info = ct.POINTER(lcurl.certinfo)()
        # Get the certificate information
        res = lcurl.easy_getinfo(curl, lcurl.CURLINFO_CERTINFO, ct.byref(cert_info))
        if res != lcurl.CURLE_OK: raise guard.Break

        # Check to see if the certificate chain is ordered correctly
        if not is_chain_in_order(cert_info.contents):
            res = TEST_ERR_FAILURE

    return res
