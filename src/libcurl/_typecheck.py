# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

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

import ctypes as ct

from ._curl import (CURLOPTTYPE_OFF_T, CURLOPTTYPE_OBJECTPOINT, CURLOPTTYPE_BLOB)
from ._curl import (CURLOPT_ABSTRACT_UNIX_SOCKET, CURLOPT_ACCEPT_ENCODING,
    CURLOPT_ALTSVC, CURLOPT_CAINFO, CURLOPT_CAPATH, CURLOPT_COOKIE, CURLOPT_COOKIEFILE,
    CURLOPT_COOKIEJAR, CURLOPT_COOKIELIST, CURLOPT_CRLFILE, CURLOPT_CUSTOMREQUEST,
    CURLOPT_DEFAULT_PROTOCOL, CURLOPT_DNS_INTERFACE, CURLOPT_DNS_LOCAL_IP4,
    CURLOPT_DNS_LOCAL_IP6, CURLOPT_DNS_SERVERS, CURLOPT_DOH_URL, CURLOPT_ECH,
    CURLOPT_EGDSOCKET, CURLOPT_FTP_ACCOUNT, CURLOPT_FTP_ALTERNATIVE_TO_USER,
    CURLOPT_FTPPORT, CURLOPT_HSTS, CURLOPT_HAPROXY_CLIENT_IP, CURLOPT_INTERFACE,
    CURLOPT_ISSUERCERT, CURLOPT_KEYPASSWD, CURLOPT_KRBLEVEL, CURLOPT_LOGIN_OPTIONS,
    CURLOPT_MAIL_AUTH, CURLOPT_MAIL_FROM, CURLOPT_NETRC_FILE, CURLOPT_NOPROXY,
    CURLOPT_PASSWORD, CURLOPT_PINNEDPUBLICKEY, CURLOPT_PRE_PROXY, CURLOPT_PROTOCOLS_STR,
    CURLOPT_PROXY, CURLOPT_PROXY_CAINFO, CURLOPT_PROXY_CAPATH, CURLOPT_PROXY_CRLFILE,
    CURLOPT_PROXY_ISSUERCERT, CURLOPT_PROXY_KEYPASSWD, CURLOPT_PROXY_PINNEDPUBLICKEY,
    CURLOPT_PROXY_SERVICE_NAME, CURLOPT_PROXY_SSL_CIPHER_LIST, CURLOPT_PROXY_SSLCERT,
    CURLOPT_PROXY_SSLCERTTYPE, CURLOPT_PROXY_SSLKEY, CURLOPT_PROXY_SSLKEYTYPE,
    CURLOPT_PROXY_TLS13_CIPHERS, CURLOPT_PROXY_TLSAUTH_PASSWORD, CURLOPT_PROXY_TLSAUTH_TYPE,
    CURLOPT_PROXY_TLSAUTH_USERNAME, CURLOPT_PROXYPASSWORD, CURLOPT_PROXYUSERNAME,
    CURLOPT_PROXYUSERPWD, CURLOPT_RANDOM_FILE, CURLOPT_RANGE,
    CURLOPT_REDIR_PROTOCOLS_STR, CURLOPT_REFERER, CURLOPT_REQUEST_TARGET,
    CURLOPT_RTSP_SESSION_ID, CURLOPT_RTSP_STREAM_URI, CURLOPT_RTSP_TRANSPORT,
    CURLOPT_SASL_AUTHZID, CURLOPT_SERVICE_NAME, CURLOPT_SOCKS5_GSSAPI_SERVICE,
    CURLOPT_SSH_HOST_PUBLIC_KEY_MD5, CURLOPT_SSH_HOST_PUBLIC_KEY_SHA256,
    CURLOPT_SSH_KNOWNHOSTS, CURLOPT_SSH_PRIVATE_KEYFILE, CURLOPT_SSH_PUBLIC_KEYFILE,
    CURLOPT_SSLCERT, CURLOPT_SSLCERTTYPE, CURLOPT_SSLENGINE, CURLOPT_SSLKEY,
    CURLOPT_SSLKEYTYPE, CURLOPT_SSL_CIPHER_LIST, CURLOPT_TLS13_CIPHERS,
    CURLOPT_TLSAUTH_PASSWORD, CURLOPT_TLSAUTH_TYPE, CURLOPT_TLSAUTH_USERNAME,
    CURLOPT_UNIX_SOCKET_PATH, CURLOPT_URL, CURLOPT_USERAGENT, CURLOPT_USERNAME,
    CURLOPT_AWS_SIGV4, CURLOPT_USERPWD, CURLOPT_XOAUTH2_BEARER, CURLOPT_SSL_EC_CURVES,
    CURLOPT_HEADERFUNCTION, CURLOPT_WRITEFUNCTION, CURLOPT_CONV_TO_NETWORK_FUNCTION,
    CURLOPT_CONV_FROM_NETWORK_FUNCTION, CURLOPT_CONV_FROM_UTF8_FUNCTION,
    CURLOPT_CHUNK_DATA, CURLOPT_CLOSESOCKETDATA, CURLOPT_DEBUGDATA,
    CURLOPT_FNMATCH_DATA, CURLOPT_HEADERDATA, CURLOPT_HSTSREADDATA,
    CURLOPT_HSTSWRITEDATA, CURLOPT_INTERLEAVEDATA, CURLOPT_IOCTLDATA,
    CURLOPT_OPENSOCKETDATA, CURLOPT_PREREQDATA, CURLOPT_PROGRESSDATA, CURLOPT_READDATA,
    CURLOPT_SEEKDATA, CURLOPT_SOCKOPTDATA, CURLOPT_SSH_KEYDATA, CURLOPT_SSL_CTX_DATA,
    CURLOPT_WRITEDATA, CURLOPT_RESOLVER_START_DATA, CURLOPT_TRAILERDATA,
    CURLOPT_SSH_HOSTKEYDATA, CURLOPT_POSTFIELDS, CURLOPT_COPYPOSTFIELDS,
    CURLOPT_HTTP200ALIASES, CURLOPT_HTTPHEADER, CURLOPT_MAIL_RCPT, CURLOPT_POSTQUOTE,
    CURLOPT_PREQUOTE, CURLOPT_PROXYHEADER, CURLOPT_QUOTE, CURLOPT_RESOLVE,
    CURLOPT_TELNETOPTIONS, CURLOPT_CONNECT_TO)
from ._curl import (CURLINFO_STRING, CURLINFO_LONG, CURLINFO_DOUBLE, CURLINFO_SOCKET,
    CURLINFO_OFF_T, CURLINFO_SLIST, CURLINFO_COOKIELIST, CURLINFO_SSL_ENGINES,
    CURLINFO_TLS_SSL_PTR, CURLINFO_TLS_SESSION, CURLINFO_CERTINFO, CURLINFO_PRIVATE)

__all__ = ('check_long_option', 'check_off_t_option', 'check_string_option',
           'check_write_cb_option', 'check_conv_cb_option', 'check_cb_data_option',
           'check_postfields_option', 'check_slist_option', 'check_string_info',
           'check_long_info', 'check_double_info', 'check_slist_info',
           'check_tlssessioninfo_info', 'check_certinfo_info', 'check_socket_info',
           'check_off_t_info')

# groups of curl_easy_setops options that take the same type of argument

# To add a new option to one of the groups, just add
#   (option) == CURLOPT_SOMETHING
# to the or-expression. If the option takes a long or curl_off_t, you do not
# have to do anything

# evaluates to true if option takes a long argument
def check_long_option(option):
    return (0 < option and option < CURLOPTTYPE_OBJECTPOINT)

def check_off_t_option(option):
    return ((option > CURLOPTTYPE_OFF_T) and (option < CURLOPTTYPE_BLOB))

# evaluates to true if option takes a char* argument
def check_string_option(option):
    return (option == CURLOPT_ABSTRACT_UNIX_SOCKET
            or option == CURLOPT_ACCEPT_ENCODING
            or option == CURLOPT_ALTSVC
            or option == CURLOPT_CAINFO
            or option == CURLOPT_CAPATH
            or option == CURLOPT_COOKIE
            or option == CURLOPT_COOKIEFILE
            or option == CURLOPT_COOKIEJAR
            or option == CURLOPT_COOKIELIST
            or option == CURLOPT_CRLFILE
            or option == CURLOPT_CUSTOMREQUEST
            or option == CURLOPT_DEFAULT_PROTOCOL
            or option == CURLOPT_DNS_INTERFACE
            or option == CURLOPT_DNS_LOCAL_IP4
            or option == CURLOPT_DNS_LOCAL_IP6
            or option == CURLOPT_DNS_SERVERS
            or option == CURLOPT_DOH_URL
            or option == CURLOPT_ECH
            or option == CURLOPT_EGDSOCKET
            or option == CURLOPT_FTP_ACCOUNT
            or option == CURLOPT_FTP_ALTERNATIVE_TO_USER
            or option == CURLOPT_FTPPORT
            or option == CURLOPT_HSTS
            or option == CURLOPT_HAPROXY_CLIENT_IP
            or option == CURLOPT_INTERFACE
            or option == CURLOPT_ISSUERCERT
            or option == CURLOPT_KEYPASSWD
            or option == CURLOPT_KRBLEVEL
            or option == CURLOPT_LOGIN_OPTIONS
            or option == CURLOPT_MAIL_AUTH
            or option == CURLOPT_MAIL_FROM
            or option == CURLOPT_NETRC_FILE
            or option == CURLOPT_NOPROXY
            or option == CURLOPT_PASSWORD
            or option == CURLOPT_PINNEDPUBLICKEY
            or option == CURLOPT_PRE_PROXY
            or option == CURLOPT_PROTOCOLS_STR
            or option == CURLOPT_PROXY
            or option == CURLOPT_PROXY_CAINFO
            or option == CURLOPT_PROXY_CAPATH
            or option == CURLOPT_PROXY_CRLFILE
            or option == CURLOPT_PROXY_ISSUERCERT
            or option == CURLOPT_PROXY_KEYPASSWD
            or option == CURLOPT_PROXY_PINNEDPUBLICKEY
            or option == CURLOPT_PROXY_SERVICE_NAME
            or option == CURLOPT_PROXY_SSL_CIPHER_LIST
            or option == CURLOPT_PROXY_SSLCERT
            or option == CURLOPT_PROXY_SSLCERTTYPE
            or option == CURLOPT_PROXY_SSLKEY
            or option == CURLOPT_PROXY_SSLKEYTYPE
            or option == CURLOPT_PROXY_TLS13_CIPHERS
            or option == CURLOPT_PROXY_TLSAUTH_PASSWORD
            or option == CURLOPT_PROXY_TLSAUTH_TYPE
            or option == CURLOPT_PROXY_TLSAUTH_USERNAME
            or option == CURLOPT_PROXYPASSWORD
            or option == CURLOPT_PROXYUSERNAME
            or option == CURLOPT_PROXYUSERPWD
            or option == CURLOPT_RANDOM_FILE
            or option == CURLOPT_RANGE
            or option == CURLOPT_REDIR_PROTOCOLS_STR
            or option == CURLOPT_REFERER
            or option == CURLOPT_REQUEST_TARGET
            or option == CURLOPT_RTSP_SESSION_ID
            or option == CURLOPT_RTSP_STREAM_URI
            or option == CURLOPT_RTSP_TRANSPORT
            or option == CURLOPT_SASL_AUTHZID
            or option == CURLOPT_SERVICE_NAME
            or option == CURLOPT_SOCKS5_GSSAPI_SERVICE
            or option == CURLOPT_SSH_HOST_PUBLIC_KEY_MD5
            or option == CURLOPT_SSH_HOST_PUBLIC_KEY_SHA256
            or option == CURLOPT_SSH_KNOWNHOSTS
            or option == CURLOPT_SSH_PRIVATE_KEYFILE
            or option == CURLOPT_SSH_PUBLIC_KEYFILE
            or option == CURLOPT_SSLCERT
            or option == CURLOPT_SSLCERTTYPE
            or option == CURLOPT_SSLENGINE
            or option == CURLOPT_SSLKEY
            or option == CURLOPT_SSLKEYTYPE
            or option == CURLOPT_SSL_CIPHER_LIST
            or option == CURLOPT_TLS13_CIPHERS
            or option == CURLOPT_TLSAUTH_PASSWORD
            or option == CURLOPT_TLSAUTH_TYPE
            or option == CURLOPT_TLSAUTH_USERNAME
            or option == CURLOPT_UNIX_SOCKET_PATH
            or option == CURLOPT_URL
            or option == CURLOPT_USERAGENT
            or option == CURLOPT_USERNAME
            or option == CURLOPT_AWS_SIGV4
            or option == CURLOPT_USERPWD
            or option == CURLOPT_XOAUTH2_BEARER
            or option == CURLOPT_SSL_EC_CURVES
            or 0)

# evaluates to true if option takes a curl_write_callback argument
def check_write_cb_option(option):
    return (option == CURLOPT_HEADERFUNCTION
            or option == CURLOPT_WRITEFUNCTION)

# evaluates to true if option takes a curl_conv_callback argument
def check_conv_cb_option(option):
    return (option == CURLOPT_CONV_TO_NETWORK_FUNCTION
            or option == CURLOPT_CONV_FROM_NETWORK_FUNCTION
            or option == CURLOPT_CONV_FROM_UTF8_FUNCTION)

# evaluates to true if option takes a data argument to pass to a callback
def check_cb_data_option(option):
    return (option == CURLOPT_CHUNK_DATA
            or option == CURLOPT_CLOSESOCKETDATA
            or option == CURLOPT_DEBUGDATA
            or option == CURLOPT_FNMATCH_DATA
            or option == CURLOPT_HEADERDATA
            or option == CURLOPT_HSTSREADDATA
            or option == CURLOPT_HSTSWRITEDATA
            or option == CURLOPT_INTERLEAVEDATA
            or option == CURLOPT_IOCTLDATA
            or option == CURLOPT_OPENSOCKETDATA
            or option == CURLOPT_PREREQDATA
            or option == CURLOPT_PROGRESSDATA
            or option == CURLOPT_READDATA
            or option == CURLOPT_SEEKDATA
            or option == CURLOPT_SOCKOPTDATA
            or option == CURLOPT_SSH_KEYDATA
            or option == CURLOPT_SSL_CTX_DATA
            or option == CURLOPT_WRITEDATA
            or option == CURLOPT_RESOLVER_START_DATA
            or option == CURLOPT_TRAILERDATA
            or option == CURLOPT_SSH_HOSTKEYDATA
            or 0)

# evaluates to true if option takes a POST data argument (void* or char*)
def check_postfields_option(option):
    return (option == CURLOPT_POSTFIELDS
            or option == CURLOPT_COPYPOSTFIELDS
            or 0)

# evaluates to true if option takes a struct curl_slist * argument
def check_slist_option(option):
    return (option == CURLOPT_HTTP200ALIASES
            or option == CURLOPT_HTTPHEADER
            or option == CURLOPT_MAIL_RCPT
            or option == CURLOPT_POSTQUOTE
            or option == CURLOPT_PREQUOTE
            or option == CURLOPT_PROXYHEADER
            or option == CURLOPT_QUOTE
            or option == CURLOPT_RESOLVE
            or option == CURLOPT_TELNETOPTIONS
            or option == CURLOPT_CONNECT_TO
            or 0)

# groups of curl_easy_getinfo infos that take the same type of argument

# evaluates to true if info expects a pointer to char * argument
def check_string_info(info):
    return (CURLINFO_STRING < info and info < CURLINFO_LONG
            and info != CURLINFO_PRIVATE)

# evaluates to true if info expects a pointer to long argument
def check_long_info(info):
    return (CURLINFO_LONG < info and info < CURLINFO_DOUBLE)

# evaluates to true if info expects a pointer to double argument
def check_double_info(info):
    return (CURLINFO_DOUBLE < info and info < CURLINFO_SLIST)

# true if info expects a pointer to struct curl_slist * argument
def check_slist_info(info):
    return ((info == CURLINFO_SSL_ENGINES) or (info == CURLINFO_COOKIELIST))

# true if info expects a pointer to struct curl_tlssessioninfo * argument
def check_tlssessioninfo_info(info):
    return ((info == CURLINFO_TLS_SSL_PTR) or (info == CURLINFO_TLS_SESSION))

# true if info expects a pointer to struct curl_certinfo * argument
def check_certinfo_info(info):
    return (info == CURLINFO_CERTINFO)

# true if info expects a pointer to struct curl_socket_t argument
def check_socket_info(info):
    return (CURLINFO_SOCKET < info and info < CURLINFO_OFF_T)

# true if info expects a pointer to curl_off_t argument
def check_off_t_info(info):
    return (CURLINFO_OFF_T < info)

# typecheck helpers -- check whether given expression has requested type

# For pointers, you can use the curlcheck_ptr/curlcheck_arr macros,
# otherwise define a new macro. Search for __builtin_types_compatible_p
# in the GCC manual.
# NOTE: these macros MUST NOT EVALUATE their arguments! The argument is
# the actual expression passed to the curl_easy_setopt macro. This
# means that you can only apply the sizeof and __typeof__ operators, no
# == or whatsoever.

# XXX: should evaluate to true if expr is a pointer
def check_any_ptr(expr):
    return (ct.sizeof(expr) == ct.sizeof(ct.c_void_p))


"""
# evaluates to true if expr is NULL
# XXX: must not evaluate expr, so this check is not accurate
def check_NULL(expr):
    return (__builtin_types_compatible_p(__typeof__(expr), __typeof__(NULL)))

# evaluates to true if expr is type*, const type* or NULL
def check_ptr(expr, type)                                       \
    return (check_NULL(expr) or
            __builtin_types_compatible_p(__typeof__(expr), type *) or
            __builtin_types_compatible_p(__typeof__(expr), const type *))

# evaluates to true if expr is one of type[], type*, NULL or const type*
def check_arr(expr, type)                                       \
    return (check_ptr((expr), type) or
            __builtin_types_compatible_p(__typeof__(expr), type []))

# evaluates to true if expr is a string
def check_string(expr):
    return (check_arr((expr), char) or
            check_arr((expr), signed char) or
            check_arr((expr), unsigned char))

# evaluates to true if expr is a long (no matter the signedness)
# XXX: for now, int is also accepted (and therefore short and char, which
# are promoted to int when passed to a variadic function)
def check_long(expr):
    return (__builtin_types_compatible_p(__typeof__(expr), long) or
            __builtin_types_compatible_p(__typeof__(expr), signed long) or
            __builtin_types_compatible_p(__typeof__(expr), unsigned long) or
            __builtin_types_compatible_p(__typeof__(expr), int) or
            __builtin_types_compatible_p(__typeof__(expr), signed int) or
            __builtin_types_compatible_p(__typeof__(expr), unsigned int) or
            __builtin_types_compatible_p(__typeof__(expr), short) or
            __builtin_types_compatible_p(__typeof__(expr), signed short) or
            __builtin_types_compatible_p(__typeof__(expr), unsigned short) or
            __builtin_types_compatible_p(__typeof__(expr), char) or
            __builtin_types_compatible_p(__typeof__(expr), signed char) or
            __builtin_types_compatible_p(__typeof__(expr), unsigned char))

# evaluates to true if expr is of type curl_off_t
def check_off_t(expr):
    return (__builtin_types_compatible_p(__typeof__(expr), curl_off_t))

# evaluates to true if expr is abuffer suitable for CURLOPT_ERRORBUFFER
# XXX: also check size of an char[] array?
def check_error_buffer(expr):
    return (check_NULL(expr) or
            __builtin_types_compatible_p(__typeof__(expr), char *) or
            __builtin_types_compatible_p(__typeof__(expr), char[]))

# evaluates to true if expr is of type (const) void* or (const) FILE*
#if 0
def check_cb_data(expr):
    return (check_ptr((expr), void) or
            check_ptr((expr), FILE))
#else # be less strict
def check_cb_data(expr):
    return check_any_ptr(expr)
#endif

# evaluates to true if expr is of type FILE*
def check_FILE(expr):
    return (check_NULL(expr) or
            (__builtin_types_compatible_p(__typeof__(expr), FILE *)))

# evaluates to true if expr can be passed as POST data (void* or char*)
def check_postfields(expr):
    return (check_ptr((expr), void) or
            check_arr((expr), char) or
            check_arr((expr), unsigned char))

# helper: __builtin_types_compatible_p distinguishes between functions and
# function pointers, hide it
def check_cb_compatible(func, type)                             \
    return (__builtin_types_compatible_p(__typeof__(func), type) or
            __builtin_types_compatible_p(__typeof__(func) *, type))

# evaluates to true if expr is of type curl_resolver_start_callback
def check_resolver_start_callback(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_resolver_start_callback))

# evaluates to true if expr is of type curl_read_callback or "similar"
def check_read_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), __typeof__(fread) *) or
            check_cb_compatible((expr), curl_read_callback) or
            check_cb_compatible((expr), _curl_read_callback1) or
            check_cb_compatible((expr), _curl_read_callback2) or
            check_cb_compatible((expr), _curl_read_callback3) or
            check_cb_compatible((expr), _curl_read_callback4) or
            check_cb_compatible((expr), _curl_read_callback5) or
            check_cb_compatible((expr), _curl_read_callback6))
typedef size_t (*_curl_read_callback1)(char *, size_t, size_t, void *);
typedef size_t (*_curl_read_callback2)(char *, size_t, size_t, const void *);
typedef size_t (*_curl_read_callback3)(char *, size_t, size_t, FILE *);
typedef size_t (*_curl_read_callback4)(void *, size_t, size_t, void *);
typedef size_t (*_curl_read_callback5)(void *, size_t, size_t, const void *);
typedef size_t (*_curl_read_callback6)(void *, size_t, size_t, FILE *);

# evaluates to true if expr is of type curl_write_callback or "similar"
def check_write_cb(expr):
    return (check_read_cb(expr) or
            check_cb_compatible((expr), __typeof__(fwrite) *) or
            check_cb_compatible((expr), curl_write_callback) or
            check_cb_compatible((expr), _curl_write_callback1) or
            check_cb_compatible((expr), _curl_write_callback2) or
            check_cb_compatible((expr), _curl_write_callback3) or
            check_cb_compatible((expr), _curl_write_callback4) or
            check_cb_compatible((expr), _curl_write_callback5) or
            check_cb_compatible((expr), _curl_write_callback6))
typedef size_t (*_curl_write_callback1)(const char *, size_t, size_t, void *);
typedef size_t (*_curl_write_callback2)(const char *, size_t, size_t,
                                       const void *);
typedef size_t (*_curl_write_callback3)(const char *, size_t, size_t, FILE *);
typedef size_t (*_curl_write_callback4)(const void *, size_t, size_t, void *);
typedef size_t (*_curl_write_callback5)(const void *, size_t, size_t,
                                       const void *);
typedef size_t (*_curl_write_callback6)(const void *, size_t, size_t, FILE *);

# evaluates to true if expr is of type curl_ioctl_callback or "similar"
def check_ioctl_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_ioctl_callback) or
            check_cb_compatible((expr), _curl_ioctl_callback1) or
            check_cb_compatible((expr), _curl_ioctl_callback2) or
            check_cb_compatible((expr), _curl_ioctl_callback3) or
            check_cb_compatible((expr), _curl_ioctl_callback4))
typedef curlioerr (*_curl_ioctl_callback1)(CURL *, int, void *);
typedef curlioerr (*_curl_ioctl_callback2)(CURL *, int, const void *);
typedef curlioerr (*_curl_ioctl_callback3)(CURL *, curliocmd, void *);
typedef curlioerr (*_curl_ioctl_callback4)(CURL *, curliocmd, const void *);

# evaluates to true if expr is of type curl_sockopt_callback or "similar"
def check_sockopt_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_sockopt_callback) or
            check_cb_compatible((expr), _curl_sockopt_callback1) or
            check_cb_compatible((expr), _curl_sockopt_callback2))
typedef int (*_curl_sockopt_callback1)(void *, curl_socket_t, curlsocktype);
typedef int (*_curl_sockopt_callback2)(const void *, curl_socket_t,
                                      curlsocktype);

# evaluates to true if expr is of type curl_opensocket_callback or "similar"
def check_opensocket_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_opensocket_callback) or
            check_cb_compatible((expr), _curl_opensocket_callback1) or
            check_cb_compatible((expr), _curl_opensocket_callback2) or
            check_cb_compatible((expr), _curl_opensocket_callback3) or
            check_cb_compatible((expr), _curl_opensocket_callback4))
typedef curl_socket_t (*_curl_opensocket_callback1)
  (void *, curlsocktype, struct curl_sockaddr *);
typedef curl_socket_t (*_curl_opensocket_callback2)
  (void *, curlsocktype, const struct curl_sockaddr *);
typedef curl_socket_t (*_curl_opensocket_callback3)
  (const void *, curlsocktype, struct curl_sockaddr *);
typedef curl_socket_t (*_curl_opensocket_callback4)
  (const void *, curlsocktype, const struct curl_sockaddr *);

# evaluates to true if expr is of type curl_progress_callback or "similar"
def check_progress_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_progress_callback) or
            check_cb_compatible((expr), _curl_progress_callback1) or
            check_cb_compatible((expr), _curl_progress_callback2))
typedef int (*_curl_progress_callback1)(void *,
    double, double, double, double);
typedef int (*_curl_progress_callback2)(const void *,
    double, double, double, double);

# evaluates to true if expr is of type curl_debug_callback or "similar"
def check_debug_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_debug_callback) or
            check_cb_compatible((expr), _curl_debug_callback1) or
            check_cb_compatible((expr), _curl_debug_callback2) or
            check_cb_compatible((expr), _curl_debug_callback3) or
            check_cb_compatible((expr), _curl_debug_callback4) or
            check_cb_compatible((expr), _curl_debug_callback5) or
            check_cb_compatible((expr), _curl_debug_callback6) or
            check_cb_compatible((expr), _curl_debug_callback7) or
            check_cb_compatible((expr), _curl_debug_callback8))
typedef int (*_curl_debug_callback1) (CURL *,
    curl_infotype, char *, size_t, void *);
typedef int (*_curl_debug_callback2) (CURL *,
    curl_infotype, char *, size_t, const void *);
typedef int (*_curl_debug_callback3) (CURL *,
    curl_infotype, const char *, size_t, void *);
typedef int (*_curl_debug_callback4) (CURL *,
    curl_infotype, const char *, size_t, const void *);
typedef int (*_curl_debug_callback5) (CURL *,
    curl_infotype, unsigned char *, size_t, void *);
typedef int (*_curl_debug_callback6) (CURL *,
    curl_infotype, unsigned char *, size_t, const void *);
typedef int (*_curl_debug_callback7) (CURL *,
    curl_infotype, const unsigned char *, size_t, void *);
typedef int (*_curl_debug_callback8) (CURL *,
    curl_infotype, const unsigned char *, size_t, const void *);

# evaluates to true if expr is of type curl_ssl_ctx_callback or "similar"
# this is getting even messier...
def check_ssl_ctx_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_ssl_ctx_callback) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback1) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback2) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback3) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback4) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback5) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback6) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback7) or
            check_cb_compatible((expr), _curl_ssl_ctx_callback8))
typedef CURLcode (*_curl_ssl_ctx_callback1)(CURL *, void *, void *);
typedef CURLcode (*_curl_ssl_ctx_callback2)(CURL *, void *, const void *);
typedef CURLcode (*_curl_ssl_ctx_callback3)(CURL *, const void *, void *);
typedef CURLcode (*_curl_ssl_ctx_callback4)(CURL *, const void *,
                                            const void *);
#ifdef HEADER_SSL_H

# hack: if we included OpenSSL's ssl.h, we know about SSL_CTX
# this will of course break if we are included before OpenSSL headers...
typedef CURLcode (*_curl_ssl_ctx_callback5)(CURL *, SSL_CTX *, void *);
typedef CURLcode (*_curl_ssl_ctx_callback6)(CURL *, SSL_CTX *, const void *);
typedef CURLcode (*_curl_ssl_ctx_callback7)(CURL *, const SSL_CTX *, void *);
typedef CURLcode (*_curl_ssl_ctx_callback8)(CURL *, const SSL_CTX *,
                                            const void *);
#else

typedef _curl_ssl_ctx_callback1 _curl_ssl_ctx_callback5;
typedef _curl_ssl_ctx_callback1 _curl_ssl_ctx_callback6;
typedef _curl_ssl_ctx_callback1 _curl_ssl_ctx_callback7;
typedef _curl_ssl_ctx_callback1 _curl_ssl_ctx_callback8;

#endif

# evaluates to true if expr is of type curl_conv_callback or "similar"
def check_conv_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_conv_callback) or
            check_cb_compatible((expr), _curl_conv_callback1) or
            check_cb_compatible((expr), _curl_conv_callback2) or
            check_cb_compatible((expr), _curl_conv_callback3) or
            check_cb_compatible((expr), _curl_conv_callback4))
typedef CURLcode (*_curl_conv_callback1)(char *, size_t length);
typedef CURLcode (*_curl_conv_callback2)(const char *, size_t length);
typedef CURLcode (*_curl_conv_callback3)(void *, size_t length);
typedef CURLcode (*_curl_conv_callback4)(const void *, size_t length);

# evaluates to true if expr is of type curl_seek_callback or "similar"
def check_seek_cb(expr):
    return (check_NULL(expr) or
            check_cb_compatible((expr), curl_seek_callback) or
            check_cb_compatible((expr), _curl_seek_callback1) or
            check_cb_compatible((expr), _curl_seek_callback2))
typedef CURLcode (*_curl_seek_callback1)(void *, curl_off_t, int);
typedef CURLcode (*_curl_seek_callback2)(const void *, curl_off_t, int);
"""
# eof
