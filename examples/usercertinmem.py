#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 2013 - 2022, Daniel Stenberg, <daniel@haxx.se>, et al.
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
Use an in-memory user certificate and RSA key and retrieve an https page.
"""

import sys
import ctypes as ct
#include <openssl/ssl.h>
#include <openssl/x509.h>
#include <openssl/pem.h>

import libcurl as lcurl
from curltestutils import *  # noqa


# Written by Ishan SinghLevett, based on Theo Borm's cacertinmem.c.
# Note that to maintain simplicity this example does not use a CA certificate
# for peer verification.  However, some form of peer verification
# must be used in real circumstances when a secure connection is required.

@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten.decode("utf-8"))
    return nwritten


my_pem: bytes = (  # www.cacert.org
    b"-----BEGIN CERTIFICATE-----\n"
    b"MIIHPTCCBSWgAwIBAgIBADANBgkqhkiG9w0BAQQFADB5MRAwDgYDVQQKEwdSb290\n"
    b"IENBMR4wHAYDVQQLExVodHRwOi8vd3d3LmNhY2VydC5vcmcxIjAgBgNVBAMTGUNB\n"
    b"IENlcnQgU2lnbmluZyBBdXRob3JpdHkxITAfBgkqhkiG9w0BCQEWEnN1cHBvcnRA\n"
    b"Y2FjZXJ0Lm9yZzAeFw0wMzAzMzAxMjI5NDlaFw0zMzAzMjkxMjI5NDlaMHkxEDAO\n"
    b"BgNVBAoTB1Jvb3QgQ0ExHjAcBgNVBAsTFWh0dHA6Ly93d3cuY2FjZXJ0Lm9yZzEi\n"
    b"MCAGA1UEAxMZQ0EgQ2VydCBTaWduaW5nIEF1dGhvcml0eTEhMB8GCSqGSIb3DQEJ\n"
    b"ARYSc3VwcG9ydEBjYWNlcnQub3JnMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIIC\n"
    b"CgKCAgEAziLA4kZ97DYoB1CW8qAzQIxL8TtmPzHlawI229Z89vGIj053NgVBlfkJ\n"
    b"8BLPRoZzYLdufujAWGSuzbCtRRcMY/pnCujW0r8+55jE8Ez64AO7NV1sId6eINm6\n"
    b"zWYyN3L69wj1x81YyY7nDl7qPv4coRQKFWyGhFtkZip6qUtTefWIonvuLwphK42y\n"
    b"fk1WpRPs6tqSnqxEQR5YYGUFZvjARL3LlPdCfgv3ZWiYUQXw8wWRBB0bF4LsyFe7\n"
    b"w2t6iPGwcswlWyCR7BYCEo8y6RcYSNDHBS4CMEK4JZwFaz+qOqfrU0j36NK2B5jc\n"
    b"G8Y0f3/JHIJ6BVgrCFvzOKKrF11myZjXnhCLotLddJr3cQxyYN/Nb5gznZY0dj4k\n"
    b"epKwDpUeb+agRThHqtdB7Uq3EvbXG4OKDy7YCbZZ16oE/9KTfWgu3YtLq1i6L43q\n"
    b"laegw1SJpfvbi1EinbLDvhG+LJGGi5Z4rSDTii8aP8bQUWWHIbEZAWV/RRyH9XzQ\n"
    b"QUxPKZgh/TMfdQwEUfoZd9vUFBzugcMd9Zi3aQaRIt0AUMyBMawSB3s42mhb5ivU\n"
    b"fslfrejrckzzAeVLIL+aplfKkQABi6F1ITe1Yw1nPkZPcCBnzsXWWdsC4PDSy826\n"
    b"YreQQejdIOQpvGQpQsgi3Hia/0PsmBsJUUtaWsJx8cTLc6nloQsCAwEAAaOCAc4w\n"
    b"ggHKMB0GA1UdDgQWBBQWtTIb1Mfz4OaO873SsDrusjkY0TCBowYDVR0jBIGbMIGY\n"
    b"gBQWtTIb1Mfz4OaO873SsDrusjkY0aF9pHsweTEQMA4GA1UEChMHUm9vdCBDQTEe\n"
    b"MBwGA1UECxMVaHR0cDovL3d3dy5jYWNlcnQub3JnMSIwIAYDVQQDExlDQSBDZXJ0\n"
    b"IFNpZ25pbmcgQXV0aG9yaXR5MSEwHwYJKoZIhvcNAQkBFhJzdXBwb3J0QGNhY2Vy\n"
    b"dC5vcmeCAQAwDwYDVR0TAQH/BAUwAwEB/zAyBgNVHR8EKzApMCegJaAjhiFodHRw\n"
    b"czovL3d3dy5jYWNlcnQub3JnL3Jldm9rZS5jcmwwMAYJYIZIAYb4QgEEBCMWIWh0\n"
    b"dHBzOi8vd3d3LmNhY2VydC5vcmcvcmV2b2tlLmNybDA0BglghkgBhvhCAQgEJxYl\n"
    b"aHR0cDovL3d3dy5jYWNlcnQub3JnL2luZGV4LnBocD9pZD0xMDBWBglghkgBhvhC\n"
    b"AQ0ESRZHVG8gZ2V0IHlvdXIgb3duIGNlcnRpZmljYXRlIGZvciBGUkVFIGhlYWQg\n"
    b"b3ZlciB0byBodHRwOi8vd3d3LmNhY2VydC5vcmcwDQYJKoZIhvcNAQEEBQADggIB\n"
    b"ACjH7pyCArpcgBLKNQodgW+JapnM8mgPf6fhjViVPr3yBsOQWqy1YPaZQwGjiHCc\n"
    b"nWKdpIevZ1gNMDY75q1I08t0AoZxPuIrA2jxNGJARjtT6ij0rPtmlVOKTV39O9lg\n"
    b"18p5aTuxZZKmxoGCXJzN600BiqXfEVWqFcofN8CCmHBh22p8lqOOLlQ+TyGpkO/c\n"
    b"gr/c6EWtTZBzCDyUZbAEmXZ/4rzCahWqlwQ3JNgelE5tDlG+1sSPypZt90Pf6DBl\n"
    b"Jzt7u0NDY8RD97LsaMzhGY4i+5jhe1o+ATc7iwiwovOVThrLm82asduycPAtStvY\n"
    b"sONvRUgzEv/+PDIqVPfE94rwiCPCR/5kenHA0R6mY7AHfqQv0wGP3J8rtsYIqQ+T\n"
    b"SCX8Ev2fQtzzxD72V7DX3WnRBnc0CkvSyqD/HMaMyRa+xMwyN2hzXwj7UfdJUzYF\n"
    b"CpUCTPJ5GhD22Dp1nPMd8aINcGeGG7MW9S/lpOt5hvk9C8JzC6WZrG/8Z7jlLwum\n"
    b"GCSNe9FINSkYQKyTYOGWhlC0elnYjyELn8+CkcY7v2vcB5G5l1YjqrZslMZIBjzk\n"
    b"zk6q5PYvCdxTby78dOs6Y5nCpqyJvKeyRKANihDjbPIky/qbn3BHLt4Ui9SyIAmW\n"
    b"omTxJBzcoTWcFbLUvFUufQb1nA5V9FrWk9p2rSVzTMVD\n"
    b"-----END CERTIFICATE-----\n"
)

  # replace the XXX with the actual RSA key
my_key: bytes = (
    b"-----BEGIN RSA PRIVATE KEY-----\n"\
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n"
    b"-----END RSA PRIVATE KEY-----\n"
)


@lcurl.ssl_ctx_callback
def sslctx_function(curl, ssl_ctx, userptr):
    """
    ret: int = 0

    # get a BIO
    bio: BIO* = BIO_new_mem_buf(my_pem, -1)

    if not bio:
        print("BIO_new_mem_buf failed")

    # use it to read the PEM formatted certificate from memory into
    # an X509 structure that SSL can use
    cert: X509* = PEM_read_bio_X509(bio, NULL, 0, NULL)
    if not cert:
        print("PEM_read_bio_X509 failed...")

    # tell SSL to use the X509 certificate
    ret = SSL_CTX_use_certificate((SSL_CTX*)ssl_ctx, cert)
    if ret != 1:
        print("Use certificate failed")

    # create a bio for the RSA key
    kbio: BIO* = BIO_new_mem_buf(my_key, -1)
    if not kbio:
        print("BIO_new_mem_buf failed")

    # read the key bio into an RSA object
    rsa: RSA* = PEM_read_bio_RSAPrivateKey(kbio, NULL, 0, NULL)
    if not rsa:
        print("Failed to create key bio")

    # tell SSL to use the RSA key from memory
    ret = SSL_CTX_use_RSAPrivateKey((SSL_CTX*)ssl_ctx, rsa)
    if ret != 1:
        print("Use Key failed")

    # free resources that have been allocated by openssl functions
    if bio:  BIO_free(bio)
    if kbio: BIO_free(kbio)
    if rsa:  RSA_free(rsa)
    if cert: X509_free(cert)
    """
    # all set to go
    return lcurl.CURLE_OK


def main(argv=sys.argv[1:]):

    url: str = argv[0] if len(argv) >= 1 else "https://www.example.com/"

    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        res: lcurl.CURLcode = lcurl.CURLE_OK

        lcurl.easy_setopt(curl, lcurl.CURLOPT_VERBOSE, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_NOSIGNAL, 1)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(sys.stdout))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_HEADERDATA, id(sys.stderr))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLCERTTYPE, b"PEM")
        # both VERIFYPEER and VERIFYHOST are set to 0 in this case because
        # there is no CA certificate
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYHOST, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSLKEYTYPE, b"PEM")

        # first try: retrieve page without user certificate and key -> will fail
        res = lcurl.easy_perform(curl)
        if res == lcurl.CURLE_OK:
            print("*** transfer succeeded ***")
        else:
            print("*** transfer failed ***")

        # second try: retrieve page using user certificate and key -> will succeed
        # load the certificate and key by installing a function doing the necessary
        # "modifications" to the SSL CONTEXT just before link init
        lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_CTX_FUNCTION, sslctx_function)

        res = lcurl.easy_perform(curl)
        if res == lcurl.CURLE_OK:
            print("*** transfer succeeded ***")
        else:
            print("*** transfer failed ***")

    return res


sys.exit(main())
