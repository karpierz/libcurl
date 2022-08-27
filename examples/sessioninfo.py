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
Uses the CURLINFO_TLS_SESSION data.
"""

import sys
import ctypes as ct
#include <gnutls/gnutls.h>
#include <gnutls/x509.h>

import libcurl as lcurl
from curltestutils import *  # noqa


# Note that this example currently requires curl to be linked against
# GnuTLS (and this program must also be linked against -lgnutls).

CURL_SSL_BACKEND_NAMES = {
    lcurl.CURLSSLBACKEND_NONE:            "(none)",
    lcurl.CURLSSLBACKEND_OPENSSL:         "OpenSSL",
    lcurl.CURLSSLBACKEND_GNUTLS:          "GnuTLS",
    lcurl.CURLSSLBACKEND_NSS:             "NSS",
    lcurl.CURLSSLBACKEND_OBSOLETE4:       "QSOSSL",
    lcurl.CURLSSLBACKEND_GSKIT:           "GSKit",
    lcurl.CURLSSLBACKEND_POLARSSL:        "PolarSSL",
    lcurl.CURLSSLBACKEND_WOLFSSL:         "wolfSSL",
    lcurl.CURLSSLBACKEND_SCHANNEL:        "SChannel",
    lcurl.CURLSSLBACKEND_SECURETRANSPORT: "Secure Transport",
    lcurl.CURLSSLBACKEND_AXTLS:           "axTLS",
    lcurl.CURLSSLBACKEND_MBEDTLS:         "Mbed TLS",
    lcurl.CURLSSLBACKEND_MESALINK:        "MesaLink",
    lcurl.CURLSSLBACKEND_BEARSSL:         "BearSSL",
    lcurl.CURLSSLBACKEND_RUSTLS:          "Rustls",
}

@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    curl = ct.cast(stream, ct.POINTER(lcurl.CURL)).contents

    info = ct.POINTER(lcurl.tlssessioninfo)()
    res: lcurl.CURLcode = lcurl.easy_getinfo(curl, lcurl.CURLINFO_TLS_SESSION,
                                             ct.byref(info))
    if res != lcurl.CURLE_OK or not info:
        return size * nitems
    info = info.contents

    print("Curl's SLL backend:",
          CURL_SSL_BACKEND_NAMES.get(info.backend, "(unknown)"),
          file=sys.stderr)

    def SSL_backend_not_supported(backend):
        print("Certificate info for this SSL backend is not supported.",
              file=sys.stderr)

    if info.backend == lcurl.CURLSSLBACKEND_OPENSSL:
        SSL_backend_not_supported(info.backend)
    elif info.backend == lcurl.CURLSSLBACKEND_GNUTLS:
        SSL_backend_not_supported(info.backend)
        """
        unsigned int cert_list_size;
        const gnutls_datum_t *chainp;

        # info.internals is now the gnutls_session_t
        chainp = gnutls_certificate_get_peers(info.internals, &cert_list_size);
        if((chainp) && (cert_list_size)) {
          unsigned int i;

          for(i = 0; i < cert_list_size; i++) {
            gnutls_x509_crt_t cert;
            gnutls_datum_t dn;

            if(GNUTLS_E_SUCCESS == gnutls_x509_crt_init(&cert)) {
              if(GNUTLS_E_SUCCESS ==
                 gnutls_x509_crt_import(cert, &chainp[i], GNUTLS_X509_FMT_DER)) {
                if(GNUTLS_E_SUCCESS ==
                   gnutls_x509_crt_print(cert, GNUTLS_CRT_PRINT_FULL, &dn)) {
                  fprintf(stderr, "Certificate #%u: %.*s", i, dn.size, dn.data);

                  gnutls_free(dn.data);
                }
              }

              gnutls_x509_crt_deinit(cert);
            }
          }
        }
        """
    elif info.backend != lcurl.CURLSSLBACKEND_NONE:
        SSL_backend_not_supported(info.backend)

    return size * nitems


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, curl)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 0)

        # Perform the custom request
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)

    return 0


sys.exit(main())
