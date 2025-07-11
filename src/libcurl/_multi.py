# flake8-in-file-ignores: noqa: E305,E722,F401

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

#  This is an "external" header file. Do not give away any internals here!
#
#  GOALS
#
#  o Enable a "pull" interface. The application that uses libcurl decides where
#    and when to ask libcurl to get/send data.
#
#  o Enable multiple simultaneous transfers in the same thread without making it
#    complicated for the application.
#
#  o Enable the application to select() on its own file descriptors and curl's
#    file descriptors simultaneous easily.

# This header file should not really need to include "curl.h" since curl.h
# itself includes this file and we expect user applications to do #include
# <curl/curl.h> without the need for especially including multi.h.
#
# For some reason we added this include here at one point, and rather than to
# break existing (wrongly written) libcurl applications, we leave it as-is
# but with this warning attached.

# include "curl.h"

import ctypes as ct
import time as _time
from select import select as _py_select

from ._platform import CFUNC, defined, is_windows
from ._platform import FD_ISSET as _FD_ISSET, select as _select
from ._dll      import dll
from ._curl     import timeval
from ._curl     import CURL, CURLcode, socket_t, fd_set, CURL_SOCKET_BAD
from ._curl     import (CURLOPTTYPE_LONG,
                        CURLOPTTYPE_OBJECTPOINT, CURLOPTTYPE_FUNCTIONPOINT,
                        CURLOPTTYPE_OFF_T, CURLOPTTYPE_BLOB)

# typedef void CURLM;
CURLM = None  # void

CURLMcode = ct.c_int
(
    CURLM_CALL_MULTI_PERFORM,     # please call curl_multi_perform() or
                                  # curl_multi_socket*() soon
    CURLM_OK,
    CURLM_BAD_HANDLE,             # the passed-in handle is not a valid CURLM handle
    CURLM_BAD_EASY_HANDLE,        # an easy handle was not good/valid
    CURLM_OUT_OF_MEMORY,          # if you ever get this, you are in deep sh*t
    CURLM_INTERNAL_ERROR,         # this is a libcurl bug
    CURLM_BAD_SOCKET,             # the passed in socket argument did not match
    CURLM_UNKNOWN_OPTION,         # curl_multi_setopt() with unsupported option
    CURLM_ADDED_ALREADY,          # an easy handle already added to a multi handle was
                                  # attempted to get added - again
    CURLM_RECURSIVE_API_CALL,     # an api function was called from inside a
                                  # callback
    CURLM_WAKEUP_FAILURE,         # wakeup is unavailable or failed
    CURLM_BAD_FUNCTION_ARGUMENT,  # function called with a bad parameter
    CURLM_ABORTED_BY_CALLBACK,
    CURLM_UNRECOVERABLE_POLL,
    CURLM_LAST

) = range(-1, 14)

# just to make code nicer when using curl_multi_socket() you can now check
# for CURLM_CALL_MULTI_SOCKET too in the same style it works for
# curl_multi_perform() and CURLM_CALL_MULTI_PERFORM
CURLM_CALL_MULTI_SOCKET = CURLM_CALL_MULTI_PERFORM

# bitmask bits for CURLMOPT_PIPELINING
CURLPIPE_NOTHING   = ct.c_long(0).value
CURLPIPE_HTTP1     = ct.c_long(1).value
CURLPIPE_MULTIPLEX = ct.c_long(2).value

CURLMSG = ct.c_int
(
    CURLMSG_NONE,  # first, not used
    CURLMSG_DONE,  # This easy handle has completed. 'result' contains
                   # the CURLcode of the transfer
    CURLMSG_LAST   # last, not used

) = range(3)

class _CURLMsgData(ct.Union):
    _fields_ = [
    ("whatever", ct.c_void_p),  # message-specific data
    ("result",   CURLcode),     # return code for transfer
]

class CURLMsg(ct.Structure):
    _fields_ = [
    ("msg",         CURLMSG),           # what this message means
    ("easy_handle", ct.POINTER(CURL)),  # the handle it concerns
    ("data",        _CURLMsgData),
]
# typedef struct CURLMsg CURLMsg;

# Based on poll(2) structure and values.
# We do not use pollfd and POLL* constants explicitly
# to cover platforms without poll().
CURL_WAIT_POLLIN  = 0x0001
CURL_WAIT_POLLPRI = 0x0002
CURL_WAIT_POLLOUT = 0x0004

class waitfd(ct.Structure):
    _fields_ = [
    ("fd",      socket_t),
    ("events",  ct.c_short),
    ("revents", ct.c_short),
]

# Name:    curl_multi_init()
#
# Desc:    initialize multi-style curl usage
#
# Returns: a new CURLM handle to use in all 'curl_multi' functions.
#
multi_init = CFUNC(ct.POINTER(CURLM))(
    ("curl_multi_init", dll),)

# Name:    curl_multi_add_handle()
#
# Desc:    add a standard curl handle to the multi stack
#
# Returns: CURLMcode type, general multi error code.
#
multi_add_handle = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    ct.POINTER(CURL))(
    ("curl_multi_add_handle", dll), (
    (1, "multi_handle"),
    (1, "curl_handle"),))

# Name:    curl_multi_remove_handle()
#
# Desc:    removes a curl handle from the multi stack again
#
# Returns: CURLMcode type, general multi error code.
#
multi_remove_handle = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    ct.POINTER(CURL))(
    ("curl_multi_remove_handle", dll), (
    (1, "multi_handle"),
    (1, "curl_handle"),))

# Name:    curl_multi_fdset()
#
# Desc:    Ask curl for its fd_set sets. The app can use these to select() or
#          poll() on. We want curl_multi_perform() called as soon as one of
#          them are ready.
#
# Returns: CURLMcode type, general multi error code.
#
multi_fdset = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    ct.POINTER(fd_set),
    ct.POINTER(fd_set),
    ct.POINTER(fd_set),
    ct.POINTER(ct.c_int))(
    ("curl_multi_fdset", dll), (
    (1, "multi_handle"),
    (1, "read_fd_set"),
    (1, "write_fd_set"),
    (1, "exc_fd_set"),
    (1, "max_fd"),))

# Name:     curl_multi_wait()
#
# Desc:     Poll on all fds within a CURLM set as well as any
#           additional fds passed to the function.
#
# Returns:  CURLMcode type, general multi error code.
#
multi_wait = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    ct.POINTER(waitfd),
    ct.c_uint,
    ct.c_int,
    ct.POINTER(ct.c_int))(
    ("curl_multi_wait", dll), (
    (1, "multi_handle"),
    (1, "extra_fds"),
    (1, "extra_nfds"),
    (1, "timeout_ms"),
    (1, "ret"),))

# Name:     curl_multi_poll()
#
# Desc:     Poll on all fds within a CURLM set as well as any
#           additional fds passed to the function.
#
# Returns:  CURLMcode type, general multi error code.
#
multi_poll = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    ct.POINTER(waitfd),
    ct.c_uint,
    ct.c_int,
    ct.POINTER(ct.c_int))(
    ("curl_multi_poll", dll), (
    (1, "multi_handle"),
    (1, "extra_fds"),
    (1, "extra_nfds"),
    (1, "timeout_ms"),
    (1, "ret"),))

# Name:     curl_multi_wakeup()
#
# Desc:     wakes up a sleeping curl_multi_poll call.
#
# Returns:  CURLMcode type, general multi error code.
#
multi_wakeup = CFUNC(CURLMcode,
    ct.POINTER(CURLM))(
    ("curl_multi_wakeup", dll), (
    (1, "multi_handle"),))

# Name:    curl_multi_perform()
#
# Desc:    When the app thinks there is data available for curl it calls this
#          function to read/write whatever there is right now. This returns
#          as soon as the reads and writes are done. This function does not
#          require that there actually is data available for reading or that
#          data can be written, it can be called just in case. It returns
#          the number of handles that still transfer data in the second
#          argument's integer-pointer.
#
# Returns: CURLMcode type, general multi error code. *NOTE* that this only
#          returns errors etc regarding the whole multi stack. There might
#          still have occurred problems on individual transfers even when
#          this returns OK.
#
multi_perform = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    ct.POINTER(ct.c_int))(
    ("curl_multi_perform", dll), (
    (1, "multi_handle"),
    (1, "running_handles"),))

# Name:    curl_multi_cleanup()
#
# Desc:    Cleans up and removes a whole multi stack. It does not free or
#          touch any individual easy handles in any way. We need to define
#          in what state those handles will be if this function is called
#          in the middle of a transfer.
#
# Returns: CURLMcode type, general multi error code.
#
multi_cleanup = CFUNC(CURLMcode,
    ct.POINTER(CURLM))(
    ("curl_multi_cleanup", dll), (
    (1, "multi_handle"),))

# Name:    curl_multi_info_read()
#
# Desc:    Ask the multi handle if there is any messages/informationals from
#          the individual transfers. Messages include informationals such as
#          error code from the transfer or just the fact that a transfer is
#          completed. More details on these should be written down as well.
#
#          Repeated calls to this function will return a new struct each
#          time, until a special "end of msgs" struct is returned as a signal
#          that there is no more to get at this point.
#
#          The data the returned pointer points to will not survive calling
#          curl_multi_cleanup().
#
#          The 'CURLMsg' struct is meant to be simple and only contain basic
#          information. If more involved information is wanted, we will
#          provide the particular "transfer handle" in that struct and that
#          should/could/would be used in subsequent curl_easy_getinfo() calls
#          (or similar). The point being that we must never expose complex
#          structs to applications, as then we will undoubtably get backwards
#          compatibility problems in the future.
#
# Returns: A pointer to a filled-in struct, or NULL if it failed or ran out
#          of structs. It also writes the number of messages left in the
#          queue (after this read) in the integer the second argument points
#          to.
#
multi_info_read = CFUNC(ct.POINTER(CURLMsg),
    ct.POINTER(CURLM),
    ct.POINTER(ct.c_int))(
    ("curl_multi_info_read", dll), (
    (1, "multi_handle"),
    (1, "msgs_in_queue"),))

# Name:    curl_multi_strerror()
#
# Desc:    The curl_multi_strerror function may be used to turn a CURLMcode
#          value into the equivalent human readable error string. This is
#          useful for printing meaningful error messages.
#
# Returns: A pointer to a null-terminated error message.
#
multi_strerror = CFUNC(ct.c_char_p,
    CURLMcode)(
    ("curl_multi_strerror", dll), (
    (1, "code"),))

# Name:    curl_multi_socket() and
#          curl_multi_socket_all()
#
# Desc:    An alternative version of curl_multi_perform() that allows the
#          application to pass in one of the file descriptors that have been
#          detected to have "action" on them and let libcurl perform.
#          See manpage for details.

CURL_POLL_NONE   = 0
CURL_POLL_IN     = 1
CURL_POLL_OUT    = 2
CURL_POLL_INOUT  = 3
CURL_POLL_REMOVE = 4

CURL_SOCKET_TIMEOUT = CURL_SOCKET_BAD

CURL_CSELECT_IN  = 0x01
CURL_CSELECT_OUT = 0x02
CURL_CSELECT_ERR = 0x04

socket_callback = CFUNC(ct.c_int,
    ct.POINTER(CURL),  # easy    # easy handle
    socket_t,          # s       # socket
    ct.c_int,          # what    # what # see above
    ct.c_void_p,       # userp   # private callback pointer
    ct.c_void_p)       # socketp # private socket pointer

# Name:    curl_multi_timer_callback
#
# Desc:    Called by libcurl whenever the library detects a change in the
#          maximum number of milliseconds the app is allowed to wait before
#          curl_multi_socket() or curl_multi_perform() must be called
#          (to allow libcurl's timed events to take place).
#
# Returns: The callback should return zero.
#
multi_timer_callback = CFUNC(ct.c_int,
    ct.POINTER(CURLM),  # multi      # multi handle
    ct.c_long,          # timeout_ms # timeout_ms # see above
    ct.c_void_p)        # userp      # private callback pointer

if 0:  # deprecated from 7.19.5, Use curl_multi_socket_action()
    multi_socket = CFUNC(CURLMcode,
        ct.POINTER(CURLM),
        socket_t,
        ct.POINTER(ct.c_int))(
        ("curl_multi_socket", dll), (
        (1, "multi_handle"),
        (1, "s"),
        (1, "running_handles"),))

    multi_socket_all = CFUNC(CURLMcode,
        ct.POINTER(CURLM),
        ct.POINTER(ct.c_int))(
        ("curl_multi_socket_all", dll), (
        (1, "multi_handle"),
        (1, "running_handles"),))

multi_socket_action = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    socket_t,
    ct.c_int,
    ct.POINTER(ct.c_int))(
    ("curl_multi_socket_action", dll), (
    (1, "multi_handle"),
    (1, "s"),
    (1, "ev_bitmask"),
    (1, "running_handles"),))

# ifndef CURL_ALLOW_OLD_MULTI_SOCKET
# This macro below was added in 7.16.3 to push users who recompile to use
# the new curl_multi_socket_action() instead of the old curl_multi_socket()
# define curl_multi_socket(x,y,z) curl_multi_socket_action(x,y,0,z)
#
# def curl_multi_socket(x, y, z): return multi_socket_action(x, y, 0, z)
# endif

# Name:    curl_multi_timeout()
#
# Desc:    Returns the maximum number of milliseconds the app is allowed to
#          wait before curl_multi_socket() or curl_multi_perform() must be
#          called (to allow libcurl's timed events to take place).
#
# Returns: CURLM error code.
#
multi_timeout = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    ct.POINTER(ct.c_long))(
    ("curl_multi_timeout", dll), (
    (1, "multi_handle"),
    (1, "milliseconds"),))

CURLMoption = ct.c_int
if 1:  # enum
    # This is the socket callback function pointer
    CURLMOPT_SOCKETFUNCTION = CURLOPTTYPE_FUNCTIONPOINT + 1

    # This is the argument passed to the socket callback
    CURLMOPT_SOCKETDATA = CURLOPTTYPE_OBJECTPOINT + 2

    # set to 1 to enable pipelining for this multi handle
    CURLMOPT_PIPELINING = CURLOPTTYPE_LONG + 3

    # This is the timer callback function pointer
    CURLMOPT_TIMERFUNCTION = CURLOPTTYPE_FUNCTIONPOINT + 4

    # This is the argument passed to the timer callback
    CURLMOPT_TIMERDATA = CURLOPTTYPE_OBJECTPOINT + 5

    # maximum number of entries in the connection cache
    CURLMOPT_MAXCONNECTS = CURLOPTTYPE_LONG + 6

    # maximum number of (pipelining) connections to one host
    CURLMOPT_MAX_HOST_CONNECTIONS = CURLOPTTYPE_LONG + 7

    # maximum number of requests in a pipeline
    CURLMOPT_MAX_PIPELINE_LENGTH = CURLOPTTYPE_LONG + 8

    # a connection with a content-length longer than this
    # will not be considered for pipelining
    CURLMOPT_CONTENT_LENGTH_PENALTY_SIZE = CURLOPTTYPE_OFF_T + 9

    # a connection with a chunk length longer than this
    # will not be considered for pipelining
    CURLMOPT_CHUNK_LENGTH_PENALTY_SIZE = CURLOPTTYPE_OFF_T + 10

    # a list of site names(+port) that are blocked from pipelining
    CURLMOPT_PIPELINING_SITE_BL = CURLOPTTYPE_OBJECTPOINT + 11

    # a list of server types that are blocked from pipelining
    CURLMOPT_PIPELINING_SERVER_BL = CURLOPTTYPE_OBJECTPOINT + 12

    # maximum number of open connections in total
    CURLMOPT_MAX_TOTAL_CONNECTIONS = CURLOPTTYPE_LONG + 13

    # This is the server push callback function pointer
    CURLMOPT_PUSHFUNCTION = CURLOPTTYPE_FUNCTIONPOINT + 14

    # This is the argument passed to the server push callback
    CURLMOPT_PUSHDATA = CURLOPTTYPE_OBJECTPOINT + 15

    # maximum number of concurrent streams to support on a connection
    CURLMOPT_MAX_CONCURRENT_STREAMS = CURLOPTTYPE_LONG + 16

    CURLMOPT_LASTENTRY = CURLMOPT_MAX_CONCURRENT_STREAMS + 1  # the last unused
# end enum CURLMoption

# Name:    curl_multi_setopt()
#
# Desc:    Sets options for the multi handle.
#
# Returns: CURLM error code.
#
multi_setopt = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    CURLMoption,
    ct.c_void_p)(
    ("curl_multi_setopt", dll), (
    (1, "multi_handle"),
    (1, "option"),
    (1, "value"),))

# Name:    curl_multi_assign()
#
# Desc:    This function sets an association in the multi handle between the
#          given socket and a private pointer of the application. This is
#          (only) useful for curl_multi_socket uses.
#
# Returns: CURLM error code.
#
multi_assign = CFUNC(CURLMcode,
    ct.POINTER(CURLM),
    socket_t,
    ct.c_void_p)(
    ("curl_multi_assign", dll), (
    (1, "multi_handle"),
    (1, "sockfd"),
    (1, "sockp"),))

# Name:    curl_multi_get_handles()
#
# Desc:    Returns an allocated array holding all handles currently added to
#          the multi handle. Marks the final entry with a NULL pointer. If
#          there is no easy handle added to the multi handle, this function
#          returns an array with the first entry as a NULL pointer.
#
# Returns: NULL on failure, otherwise a CURL **array pointer
#
try:  # libcurl >= ?.?.?
    multi_get_handles = CFUNC(ct.POINTER(ct.POINTER(CURL)),
        ct.POINTER(CURLM))(
        ("curl_multi_get_handles", dll), (
        (1, "multi_handle"),))
except: pass  # pragma: no cover

# Name: curl_push_callback
#
# Desc: This callback gets called when a new stream is being pushed by the
#       server. It approves or denies the new stream. It can also decide
#       to completely fail the connection.
#
# Returns: CURL_PUSH_OK, CURL_PUSH_DENY or CURL_PUSH_ERROROUT

CURL_PUSH_OK       = 0
CURL_PUSH_DENY     = 1
CURL_PUSH_ERROROUT = 2  # added in 7.72.0

# forward declaration only
class pushheaders(ct.Structure): pass

pushheader_bynum = CFUNC(ct.c_char_p,
    ct.POINTER(pushheaders),
    ct.c_size_t)(
    ("curl_pushheader_bynum", dll), (
    (1, "h"),
    (1, "num"),))

pushheader_byname = CFUNC(ct.c_char_p,
    ct.POINTER(pushheaders),
    ct.c_char_p)(
    ("curl_pushheader_byname", dll), (
    (1, "h"),
    (1, "name"),))

push_callback = CFUNC(ct.c_int,
    ct.POINTER(CURL),         # parent
    ct.POINTER(CURL),         # easy
    ct.c_size_t,              # num_headers
    ct.POINTER(pushheaders),  # headers
    ct.c_void_p)              # userp

# Name:    curl_multi_waitfds()
#
# Desc:    Ask curl for fds for polling. The app can use these to poll on.
#          We want curl_multi_perform() called as soon as one of them are
#          ready. Passing zero size allows to get just a number of fds.
#
# Returns: CURLMcode type, general multi error code.
#
try:  # libcurl >= ?.?.?
    multi_waitfds = CFUNC(CURLMcode,
        ct.POINTER(CURLM),
        ct.POINTER(waitfd),
        ct.c_uint,
        ct.POINTER(ct.c_uint))(
        ("curl_multi_waitfds", dll), (
        (1, "multi"),
        (1, "ufds"),
        (1, "size"),
        (1, "fd_count"),))
except: pass  # pragma: no cover

# Name:    select()
#
# Desc:    Allows a program to monitor multiple file descriptors,
#          waiting until one or more of the file descriptors become "ready"
#          for some class of I/O operation (e.g., input possible).  A file
#          descriptor is considered ready if it is possible to perform a
#          corresponding I/O operation (e.g., read(2), or a sufficiently
#          small write(2)) without blocking.
#
# Returns: On success, return the number of file descriptors contained in the
#          three returned descriptor sets (that is, the total number of bits
#          that are set in readfds, writefds, exceptfds).  The return value
#          may be zero if the timeout expired before any file descriptors
#          became ready. On error, -1 is returned, and the file descriptor
#          sets are unmodified.
#
@CFUNC(ct.c_int, ct.c_int,
       ct.POINTER(fd_set), ct.POINTER(fd_set), ct.POINTER(fd_set),
       ct.POINTER(timeval))
def select(nfds, readfds, writefds, exceptfds, timeout):

    if nfds < 0:
        # SET_SOCKERRNO(SOCKEINVAL) # !!!
        return -1

    if is_windows and (nfds == 0
       or ((not readfds   or readfds.contents.fd_count   == 0)
       and (not writefds  or writefds.contents.fd_count  == 0)
       and (not exceptfds or exceptfds.contents.fd_count == 0))):
        # Winsock select() requires that at least one of the three fd_set
        # pointers is not NULL and points to a non-empty fdset. IOW Winsock
        # select() can not be used to sleep without a single fd_set.
        if not timeout:
            timeout_sec = None
        else:
            timeout_sec = (timeout.contents.tv_sec
                           + timeout.contents.tv_usec / 1_000_000)
        _time.sleep(timeout_sec or 0)
        return 0

    return _select(nfds, readfds, writefds, exceptfds, timeout)

@CFUNC(ct.c_int, ct.c_int,
       ct.POINTER(fd_set), ct.POINTER(fd_set), ct.POINTER(fd_set),
       ct.POINTER(timeval))
def py_select(nfds, readfds, writefds, exceptfds, timeout):

    if nfds < 0:
        # SET_SOCKERRNO(SOCKEINVAL) # !!!
        return -1

    if not timeout:
        timeout = None
    else:
        timeout = timeout.contents
        timeout = timeout.tv_sec + timeout.tv_usec / 1_000_000

    if is_windows and (nfds == 0
       or ((not readfds   or readfds.contents.fd_count   == 0)
       and (not writefds  or writefds.contents.fd_count  == 0)
       and (not exceptfds or exceptfds.contents.fd_count == 0))):
        # Winsock select() requires that at least one of the three fd_set
        # pointers is not NULL and points to a non-empty fdset. IOW Winsock
        # select() can not be used to sleep without a single fd_set.
        _time.sleep(timeout or 0)
        return 0

    try:
        infd, outfd, errfd = _py_select(_extract_sockets_from_fd_set(readfds),
                                        _extract_sockets_from_fd_set(writefds),
                                        _extract_sockets_from_fd_set(exceptfds),
                                        timeout)
    except OSError:
        return -1
    return len(infd) + len(outfd) + len(errfd)

if is_windows:
    def _extract_sockets_from_fd_set(fdsetp):
        if not fdsetp: return []
        fdset = fdsetp.contents
        return [fdset.fd_array[i] for i in range(fdset.fd_count)]
else:
    def _extract_sockets_from_fd_set(fdsetp):
        if not fdsetp: return []
        fdset = fdsetp.contents
        max_fd = ct.sizeof(fdset.fds_bits) * 8
        return [fd for fd in range(max_fd) if _FD_ISSET(fd, fdsetp)]

# eof
