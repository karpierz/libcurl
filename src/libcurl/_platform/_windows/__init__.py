# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

import sys
import os
import ctypes as ct
from ctypes import windll

this_dir = os.path.dirname(os.path.abspath(__file__))
is_32bit = (sys.maxsize <= 2**32)
arch     = "x86" if is_32bit else "x64"
arch_dir = os.path.join(this_dir, arch)

try:
    from ...__config__ import config
    DLL_PATH = config.get("LIBCURL", None)
    del config
    if DLL_PATH is None or DLL_PATH in ("", "None"):
        raise ImportError()
except ImportError:
    DLL_PATH = os.path.join(arch_dir,
                            "libcurl.dll" if is_32bit else "libcurl-x64.dll")

from ctypes import WinDLL as DLL  # noqa: E402,N814
try:
    from _ctypes import FreeLibrary as dlclose  # noqa: E402,N813
except ImportError:
    dlclose = lambda handle: 0
from ctypes import WINFUNCTYPE as CFUNC  # noqa: E402

time_t = ct.c_uint64

# Winsock doesn't have this POSIX type; it's used for the
# tv_usec value of struct timeval.
suseconds_t = ct.c_long

# Taken from the file <winsock.h>
#
# struct timeval {
#     long tv_sec;   /* seconds */
#     long tv_usec;  /* and microseconds */
# };

class timeval(ct.Structure):
    _fields_ = [
    ("tv_sec",  ct.c_long),    # seconds
    ("tv_usec", suseconds_t),  # microseconds
]

# Taken from the file libpcap's "socket.h"

# Some minor differences between sockets on various platforms.
# We include whatever sockets are needed for Internet-protocol
# socket access.

# In Winsock, a socket handle is of type SOCKET.
SOCKET = ct.c_uint

# In Winsock, the error return if socket() fails is INVALID_SOCKET.
INVALID_SOCKET = SOCKET(-1).value

# Winsock doesn't have this UN*X type; it's used in the UN*X
# sockets API.
socklen_t = ct.c_int

class sockaddr(ct.Structure):
    _fields_ = [
    ("sa_family", ct.c_short),
    ("__pad1",    ct.c_ushort),
    ("ipv4_addr", ct.c_byte * 4),
    ("ipv6_addr", ct.c_byte * 16),
    ("__pad2",    ct.c_ulong),
]

# POSIX.1g specifies this type name for the `sa_family' member.
sa_family_t = ct.c_short

# Type to represent a port.
in_port_t = ct.c_ushort

# IPv4 AF_INET sockets:

class in_addr(ct.Union):
    _fields_ = [
    ("s_addr", ct.c_uint32),  # ct.c_ulong
]

class sockaddr_in(ct.Structure):
    _fields_ = [
    ("sin_family", sa_family_t),      # e.g. AF_INET, AF_INET6
    ("sin_port",   in_port_t),        # e.g. htons(3490)
    ("sin_addr",   in_addr),          # see struct in_addr, above
    ("sin_zero",   (ct.c_char * 8)),  # padding, zero this if you want to
]

# IPv6 AF_INET6 sockets:

class in6_addr(ct.Union):
    _fields_ = [
    ("s6_addr",   (ct.c_uint8 * 16)),
    ("s6_addr16", (ct.c_uint16 * 8)),
    ("s6_addr32", (ct.c_uint32 * 4)),
]

class sockaddr_in6(ct.Structure):
    _fields_ = [
    ("sin6_family",   sa_family_t),  # address family, AF_INET6
    ("sin6_port",     in_port_t),    # port number, Network Byte Order
    ("sin6_flowinfo", ct.c_ulong),   # IPv6 flow information
    ("sin6_addr",     in6_addr),     # IPv6 address
    ("sin6_scope_id", ct.c_ulong),   # Scope ID
]

# From <sys/select.h>

# Maximum number of file descriptors in `fd_set'.
FD_SETSIZE = 1024

class fd_set(ct.Structure):
    _fields_ = [
    ("fd_count", ct.c_uint),
    ("fd_array", SOCKET * FD_SETSIZE),
]

@CFUNC(None, ct.POINTER(fd_set))
def FD_ZERO(fdsetp):
    ct.memset(fdsetp, 0, ct.sizeof(fdsetp))

@CFUNC(ct.c_int, ct.c_int, ct.POINTER(fd_set))
def FD_ISSET(fd, fdsetp):
    fdset = fdsetp.contents
    for i in range(fdset.fd_count):
        if fdset.fd_array[i] == fd:
            return 1
    return 0

@CFUNC(None, ct.c_int, ct.POINTER(fd_set))
def FD_SET(fd, fdsetp):
    fdset = fdsetp.contents
    if fdset.fd_count < FD_SETSIZE:
        fdset.fd_array[fdset.fd_count] = fd
        fdset.fd_count += 1

@CFUNC(None, ct.c_int, ct.POINTER(fd_set))
def FD_CLR(fd, fdsetp):
    fdset = fdsetp.contents
    for i in range(fdset.fd_count):
        if fdset.fd_array[i] == fd:
            for j in range(i, fdset.fd_count - 1):
                fdset.fd_array[j] = fdset.fd_array[j + 1]
            fdset.fd_array[fdset.fd_count - 1] = 0
            fdset.fd_count -= 1
            break

select = windll.Ws2_32.select
select.restype  = ct.c_int
select.argtypes = [ct.c_int,
                   ct.POINTER(fd_set), ct.POINTER(fd_set), ct.POINTER(fd_set),
                   ct.POINTER(timeval)]

del windll
