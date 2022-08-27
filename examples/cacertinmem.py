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
CA cert in memory with OpenSSL to get a HTTPS page.
"""

import sys
import ctypes as ct
#include <openssl/err.h>
#include <openssl/ssl.h>

import libcurl as lcurl
from curltestutils import *  # noqa


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten.decode("utf-8"))
    return nwritten


#** This example uses two (fake) certificates **#
my_pem: bytes = (
    b"-----BEGIN CERTIFICATE-----\n"
    b"MIIH0zCCBbugAwIBAgIIXsO3pkN/pOAwDQYJKoZIhvcNAQEFBQAwQjESMBAGA1UE\n"
    b"AwwJQUNDVlJBSVoxMRAwDgYDVQQLDAdQS0lBQ0NWMQ0wCwYDVQQKDARBQ0NWMQsw\n"
    b"CQYDVQQGEwJFUzAeFw0xMTA1MDUwOTM3MzdaFw0zMDEyMzEwOTM3MzdaMEIxEjAQ\n"
    b"BgNVBAMMCUFDQ1ZSQUlaMTEQMA4GA1UECwwHUEtJQUNDVjENMAsGA1UECgwEQUND\n"
    b"VjELMAkGA1UEBhMCRVMwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQCb\n"
    b"qau/YUqXry+XZpp0X9DZlv3P4uRm7x8fRzPCRKPfmt4ftVTdFXxpNRFvu8gMjmoY\n"
    b"HtiP2Ra8EEg2XPBjs5BaXCQ316PWywlxufEBcoSwfdtNgM3802/J+Nq2DoLSRYWo\n"
    b"G2ioPej0RGy9ocLLA76MPhMAhN9KSMDjIgro6TenGEyxCQ0jVn8ETdkXhBilyNpA\n"
    b"0KIV9VMJcRz/RROE5iZe+OCIHAr8Fraocwa48GOEAqDGWuzndN9wrqODJerWx5eH\n"
    b"k6fGioozl2A3ED6XPm4pFdahD9GILBKfb6qkxkLrQaLjlUPTAYVtjrs78yM2x/47\n"
    b"JyCpZET/LtZ1qmxNYEAZSUNUY9rizLpm5U9EelvZaoErQNV/+QEnWCzI7UiRfD+m\n"
    b"AM/EKXMRNt6GGT6d7hmKG9Ww7Y49nCrADdg9ZuM8Db3VlFzi4qc1GwQA9j9ajepD\n"
    b"vV+JHanBsMyZ4k0ACtrJJ1vnE5Bc5PUzolVt3OAJTS+xJlsndQAJxGJ3KQhfnlms\n"
    b"tn6tn1QwIgPBHnFk/vk4CpYY3QIUrCPLBhwepH2NDd4nQeit2hW3sCPdK6jT2iWH\n"
    b"7ehVRE2I9DZ+hJp4rPcOVkkO1jMl1oRQQmwgEh0q1b688nCBpHBgvgW1m54ERL5h\n"
    b"I6zppSSMEYCUWqKiuUnSwdzRp+0xESyeGabu4VXhwOrPDYTkF7eifKXeVSUG7szA\n"
    b"h1xA2syVP1XgNce4hL60Xc16gwFy7ofmXx2utYXGJt/mwZrpHgJHnyqobalbz+xF\n"
    b"d3+YJ5oyXSrjhO7FmGYvliAd3djDJ9ew+f7Zfc3Qn48LFFhRny+Lwzgt3uiP1o2H\n"
    b"pPVWQxaZLPSkVrQ0uGE3ycJYgBugl6H8WY3pEfbRD0tVNEYqi4Y7\n"
    b"-----END CERTIFICATE-----\n"
    b"-----BEGIN CERTIFICATE-----\n"
    b"MIIFtTCCA52gAwIBAgIIYY3HhjsBggUwDQYJKoZIhvcNAQEFBQAwRDEWMBQGA1UE\n"
    b"AwwNQUNFRElDT00gUm9vdDEMMAoGA1UECwwDUEtJMQ8wDQYDVQQKDAZFRElDT00x\n"
    b"CzAJBgNVBAYTAkVTMB4XDTA4MDQxODE2MjQyMloXDTI4MDQxMzE2MjQyMlowRDEW\n"
    b"MBQGA1UEAwwNQUNFRElDT00gUm9vdDEMMAoGA1UECwwDUEtJMQ8wDQYDVQQKDAZF\n"
    b"RElDT00xCzAJBgNVBAYTAkVTMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKC\n"
    b"AgEA/5KV4WgGdrQsyFhIyv2AVClVYyT/kGWbEHV7w2rbYgIB8hiGtXxaOLHkWLn7\n"
    b"09gtn70yN78sFW2+tfQh0hOR2QetAQXW8713zl9CgQr5auODAKgrLlUTY4HKRxx7\n"
    b"XBZXehuDYAQ6PmXDzQHe3qTWDLqO3tkE7hdWIpuPY/1NFgu3e3eM+SW10W2ZEi5P\n"
    b"gvoFNTPhNahXwOf9jU8/kzJPeGYDdwdY6ZXIfj7QeQCM8htRM5u8lOk6e25SLTKe\n"
    b"I6RF+7YuE7CLGLHdztUdp0J/Vb77W7tH1PwkzQSulgUV1qzOMPPKC8W64iLgpq0i\n"
    b"5ALudBF/TP94HTXa5gI06xgSYXcGCRZj6hitoocf8seACQl1ThCojz2GuHURwCRi\n"
    b"ipZ7SkXp7FnFvmuD5uHorLUwHv4FB4D54SMNUI8FmP8sX+g7tq3PgbUhh8oIKiMn\n"
    b"MCArz+2UW6yyetLHKKGKC5tNSixthT8Jcjxn4tncB7rrZXtaAWPWkFtPF2Y9fwsZ\n"
    b"o5NjEFIqnxQWWOLcpfShFosOkYuByptZ+thrkQdlVV9SH686+5DdaaVbnG0OLLb6\n"
    b"zqylfDJKZ0DcMDQj3dcEI2bw/FWAp/tmGYI1Z2JwOV5vx+qQQEQIHriy1tvuWacN\n"
    b"GHk0vFQYXlPKNFHtRQrmjseCNj6nOGOpMCwXEGCSn1WHElkQwg9naRHMTh5+Spqt\n"
    b"r0CodaxWkHS4oJyleW/c6RrIaQXpuvoDs3zk4E7Czp3otkYNbn5XOmeUwssfnHdK\n"
    b"Z05phkOTOPu220+DkdRgfks+KzgHVZhepA==\n"
    b"-----END CERTIFICATE-----\n"
)


@lcurl.ssl_ctx_callback
def sslctx_function(curl, ssl_ctx, userptr):
    """
    cts:  X509_STORE* = SSL_CTX_get_cert_store((SSL_CTX *)ssl_ctx)
    cbio: BIO*        = BIO_new_mem_buf(my_pem, len(my_pem))
    if not cts or not cbio:
        return lcurl.CURLE_ABORTED_BY_CALLBACK

    inf: STACK_OF(X509_INFO)* = PEM_X509_INFO_read_bio(cbio, NULL, NULL, NULL)
    if not inf:
        BIO_free(cbio)
        return lcurl.CURLE_ABORTED_BY_CALLBACK

    for i in range(sk_X509_INFO_num(inf)):
        itmp: X509_INFO* = sk_X509_INFO_value(inf, i)
        if itmp->x509:
            X509_STORE_add_cert(cts, itmp->x509)
        if itmp->crl:
            X509_STORE_add_crl(cts, itmp->crl)

    sk_X509_INFO_pop_free(inf, X509_INFO_free)
    BIO_free(cbio)
    """
    return lcurl.CURLE_OK


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    res: lcurl.CURLcode = lcurl.CURLE_OK

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOSIGNAL, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sys.stdout))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, id(sys.stderr))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLCERTTYPE, b"PEM")
        #lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        # Turn off the default CA locations, otherwise libcurl will load CA
        # certificates from the locations that were detected/specified at
        # build-time
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CAINFO, None)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_CAPATH, None)

        # first try: retrieve page without ca certificates -> should fail
        # unless libcurl was built --with-ca-fallback enabled at build-time
        res = lcurl.easy_perform(curl)
        if res == lcurl.CURLE_OK:
            print("*** transfer succeeded ***")
        else:
            print("*** transfer failed ***")

        # use a fresh connection (optional)
        # this option seriously impacts performance of multiple transfers but
        # it is necessary order to demonstrate this example. recall that the
        # ssl ctx callback is only called _before_ an SSL connection is
        # established, therefore it will not affect existing verified SSL
        # connections already in the connection cache associated with this
        # handle. normally you would set the ssl ctx function before making
        # any transfers, and not use this option.
        lcurl.easy_setopt(curl, lcurl.CURLOPT_FRESH_CONNECT, 1)
        # second try: retrieve page using cacerts' certificate -> will succeed
        # load the certificate by installing a function doing the necessary
        # "modifications" to the SSL CONTEXT just before link init
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_CTX_FUNCTION, sslctx_function)

        res = lcurl.easy_perform(curl)
        if res == lcurl.CURLE_OK:
            print("*** transfer succeeded ***")
        else:
            print("*** transfer failed ***")

    return res


sys.exit(main())
