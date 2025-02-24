# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

import sys
import os
import ctypes as ct

raise NotImplementedError("This OS is not supported yet!")

this_dir = os.path.dirname(os.path.abspath(__file__))
is_32bit = (sys.maxsize <= 2**32)
arch     = "x86" if is_32bit else "x64"
arch_dir = os.path.join(this_dir, arch)

def macos_version():
    import platform
    return tuple(int(x) for x in platform.mac_ver()[0].split("."))[:2]

if is_32bit:
    raise NotImplementedError("This OS is not supported in 32 bit!")

try:
    from ...__config__ import config
    DLL_PATH = config.get("LIBCURL", None)
    del config
    if DLL_PATH is None or DLL_PATH in ("", "None"):
        raise ImportError()
except ImportError:
    version = macos_version()
    if version < (10, 9) or version >= (11, 6) or version >= (10, 16):
        raise NotImplementedError("This OS version ({}) is not supported!"
                                  .format(".".join(str(x) for x in version)))
    ver_dir = "10.9"
    DLL_PATH = os.path.join(arch_dir, ver_dir, "libcurl-1.0.0.dylib")

from ctypes  import CDLL as DLL         # noqa: E402
from _ctypes import dlclose             # noqa: E402
from ctypes  import CFUNCTYPE as CFUNC  # noqa: E402

# X32 kernel interface is 64-bit.
if False:  # if defined __x86_64__ && defined __ILP32__
    # quad_t is also 64 bits.
    time_t = suseconds_t = ct.c_longlong
else:
    time_t = suseconds_t = ct.c_long
# endif

# Taken from the file <sys/time.h>
# #include <time.h>
#
# struct timeval {
#     time_t      tv_sec;   /* Seconds. */
#     suseconds_t tv_usec;  /* Microseconds. */
# };

class timeval(ct.Structure):
    _fields_ = [
    ("tv_sec",  time_t),       # seconds
    ("tv_usec", suseconds_t),  # microseconds
]

# Taken from the file libpcap's "socket.h"

# Some minor differences between sockets on various platforms.
# We include whatever sockets are needed for Internet-protocol
# socket access.

# In UN*X, a socket handle is a file descriptor, and therefore
# a signed integer.
SOCKET = ct.c_int

# In UN*X, the error return if socket() fails is -1.
INVALID_SOCKET = SOCKET(-1).value

class sockaddr(ct.Structure):
    _fields_ = [
    ("sa_family", ct.c_short),
    ("__pad1",    ct.c_ushort),
    ("ipv4_addr", ct.c_byte * 4),
    ("ipv6_addr", ct.c_byte * 16),
    ("__pad2",    ct.c_ulong),
]

# POSIX.1g specifies this type name for the `sa_family' member.
sa_family_t = ct.c_ushort

# Type to represent a port.
in_port_t = ct.c_uint16

# IPv4 AF_INET sockets:

class in_addr(ct.Structure):
    _fields_ = [
    ("s_addr", ct.c_uint32),
]

class sockaddr_in(ct.Structure):
    _fields_ = [
    ("sin_family", sa_family_t),  # e.g. AF_INET, AF_INET6
    ("sin_port",   in_port_t),    # Port number.
    ("sin_addr",   in_addr),      # Internet address.
    ("sin_zero",   (ct.c_ubyte    # Pad to size of `struct sockaddr'.
                    * (ct.sizeof(sockaddr)
                       - ct.sizeof(sa_family_t)
                       - ct.sizeof(in_port_t)
                       - ct.sizeof(in_addr)))),
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
    ("sin6_port",     in_port_t),    # Transport layer port #
    ("sin6_flowinfo", ct.c_uint32),  # IPv6 flow information
    ("sin6_addr",     in6_addr),     # IPv6 address
    ("sin6_scope_id", ct.c_uint32),  # IPv6 scope-id
]

# From <sys/select.h>

# The fd_set member
fd_mask = ct.c_long
NFDBITS = 8 * ct.sizeof(fd_mask)

# Maximum number of file descriptors in `fd_set'.
FD_SETSIZE = 1024

class fd_set(ct.Structure):
    _fields_ = [
    ("fds_bits", fd_mask * (FD_SETSIZE // NFDBITS)),
]

@CFUNC(None, ct.POINTER(fd_set))
def FD_ZERO(fdsetp):
    ct.memset(fdsetp, 0, ct.sizeof(fdsetp))

@CFUNC(ct.c_int, ct.c_int, ct.POINTER(fd_set))
def FD_ISSET(fd, fdsetp):
    fdset = fdsetp.contents
    return int(fdset.fds_bits[fd // NFDBITS] & (1 << (fd % NFDBITS)))

@CFUNC(None, ct.c_int, ct.POINTER(fd_set))
def FD_SET(fd, fdsetp):
    fdset = fdsetp.contents
    fdset.fds_bits[fd // NFDBITS] |= (1 << (fd % NFDBITS))

@CFUNC(None, ct.c_int, ct.POINTER(fd_set))
def FD_CLR(fd, fdsetp):
    fdset = fdsetp.contents
    fdset.fds_bits[fd // NFDBITS] &= ~(1 << (fd % NFDBITS))
