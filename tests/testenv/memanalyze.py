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

from typing import Dict
import argparse
import sys
import re
from pathlib import Path

# Example input:
#
# MEM mprintf.c:1094 malloc(32) = e5718
# MEM mprintf.c:1103 realloc(e5718, 64) = e6118
# MEM sendf.c:232 free(f6520)


class MemAnalyze:

    MEMLIMIT_regex          = re.compile(r"^LIMIT.*memlimit$")
    LIMIT_regex             = re.compile(r"^LIMIT ([^ ]*):(\d*) (.*)")
    LIMIT_reached_regex     = re.compile(r"([^ ]*) reached memlimit")
    MEM_regex               = re.compile(r"^MEM ([^ ]*):(\d*) (.*)")
    MEM_free_regex          = re.compile(r"free\((\(nil\)|0x([0-9a-f]*))")
    MEM_malloc_regex        = re.compile(r"malloc\((\d*)\) = 0x([0-9a-f]*)")
    MEM_calloc_regex        = re.compile(r"calloc\((\d*),(\d*)\) = 0x([0-9a-f]*)")
    MEM_realloc_regex       = re.compile(r"realloc\((\(nil\)|0x([0-9a-f]*)), (\d*)\) = "
                                         r"0x([0-9a-f]*)")
    MEM_strdup_regex        = re.compile(r"strdup\(0x([0-9a-f]*)\) \((\d*)\) = "
                                         r"0x([0-9a-f]*)")
    MEM_wcsdup_regex        = re.compile(r"wcsdup\(0x([0-9a-f]*)\) \((\d*)\) = "
                                         r"0x([0-9a-f]*)")
    FD_regex                = re.compile(r"^FD ([^ ]*):(\d*) (.*)")
    FD_socket_regex         = re.compile(r"socket\(\) = (\d*)")
    FD_socketpair_regex     = re.compile(r"socketpair\(\) = (\d*) (\d*)")
    FD_accept_regex         = re.compile(r"accept\(\) = (\d*)")
    FD_sclose_regex         = re.compile(r"sclose\((\d*)\)")
    FILE_regex              = re.compile(r"^FILE ([^ ]*):(\d*) (.*)")
    FILE_fopen_regex        = re.compile(r'f[d]*open\(\"(.*)\",\"([^\"]*)\"\) = '
                                         r'(\(nil\)|0x([0-9a-f]*))')
    FILE_fclose_regex       = re.compile(r"fclose\(0x([0-9a-f]*)\)")
    GETNAME_regex           = re.compile(r"^GETNAME ([^ ]*):(\d*) (.*)")
    SEND_regex              = re.compile(r"^SEND ([^ ]*):(\d*) (.*)")
    RECV_regex              = re.compile(r"^RECV ([^ ]*):(\d*) (.*)")
    ADDR_regex              = re.compile(r"^ADDR ([^ ]*):(\d*) (.*)")
    ADDR_getaddrinfo_regex  = re.compile(r"getaddrinfo\(\) = (\(nil\)|0x([0-9a-f]*))")
    ADDR_freeaddrinfo_regex = re.compile(r"freeaddrinfo\(0x([0-9a-f]*)\)")

    def __init__(self):

        self.mallocs:  int = 0
        self.callocs:  int = 0
        self.reallocs: int = 0
        self.strdups:  int = 0
        self.wcsdups:  int = 0
        self.frees:    int = 0
        self.sends:    int = 0
        self.recvs:    int = 0
        self.sockets:  int = 0

        self.max_mem:  int = 0  # the high water mark
        self.mem_sum:  int = 0  # the total number of memory allocated over the lifetime

        self.total_mem: int = 0

        self.size_at_addr: Dict[int] = {}
        self.memop_file: Dict[str] = {}

        self.openfiles: int = 0
        self.openf: Dict[bool] = {}
        self.open_file: Dict[str] = {}

        self.fopens: int = 0
        self.fopen: Dict[bool] = {}
        self.fopen_file: Dict[str] = {}

        self.addr_infos: int = 0
        self.addr_info: Dict[bool] = {}
        self.addr_info_file: Dict[str] = {}

        self.verbose: int = 0
        self.trace:   int = 0

    def memlimit(self, dump_file: Path):

        self.__init__()

        with dump_file.open("rt") as fh:
            for file_lnum, line in enumerate(fh):
                if (match := self.MEMLIMIT_regex.search(line.rstrip())):
                    print(line, end="")
                    break

    def analyze(self, dump_file: Path):

        self.__init__()

        with dump_file.open("rt") as fh:
            for file_lnum, line in enumerate(fh):
                line = line.rstrip("\n")
                #print(file_lnum, line, end="")
                if (match := self.LIMIT_regex.search(line)):
                    # new memory limit test prefix

                    source   = match.group(1)
                    line_num = match.group(2)
                    info     = match.group(3)

                    if self.trace and (match := self.LIMIT_reached_regex.search(info)):
                        function = match.group(1)
                        print(f"LIMIT: {function} returned error at {source}:{line_num}")

                elif (match := self.MEM_regex.search(line)):
                    # generic match for the filename+linenumber

                    source   = match.group(1)
                    line_num = match.group(2)
                    function = match.group(3)

                    if (match := self.MEM_free_regex.search(function)):

                        nil_or_addr = match.group(1)
                        addr        = match.group(2)

                        if nil_or_addr == "(nil)":
                            pass  # do nothing when free(NULL)
                        elif addr not in self.size_at_addr:
                            print(f"FREE ERROR: No memory allocated: {line}")
                        elif self.size_at_addr[addr] == -1:
                            print(f"FREE ERROR: Memory freed twice: {line}")
                            print(f"FREE ERROR: Previously freed at: {self.memop_file[addr]}")
                        else:
                            self.total_mem -= self.size_at_addr[addr]

                            if self.trace:
                                print(f"FREE: malloc at {self.memop_file[addr]} is freed "
                                      f"again at {source}:{line_num}")
                                print(f"FREE: {self.size_at_addr[addr]} bytes freed, left "
                                      f"allocated: {self.total_mem} bytes")

                            self.new_total(self.total_mem)
                            self.frees += 1

                            self.size_at_addr[addr] =- 1  # set -1 to mark as freed
                            self.memop_file[addr] = f"{source}:{line_num}"

                    elif (match := self.MEM_malloc_regex.search(function)):

                        size = int(match.group(1))
                        addr = match.group(2)

                        if self.size_at_addr.get(addr, 0) > 0:
                            # this means weeeeeirdo
                            print(f"Mixed debug compile ({source}:{line_num} at line "
                                  f"{file_lnum}), rebuild curl now")
                            print(f"We think {self.size_at_addr[addr]} bytes are already "
                                  f"allocated at that memory address: {addr}!")

                        self.size_at_addr[addr] = size
                        self.total_mem += size
                        self.mem_sum   += size

                        if self.trace:
                            print(f"MALLOC: malloc({size}) at {source}:{line_num}"
                                  f" makes totally {self.total_mem} bytes")

                        self.new_total(self.total_mem)
                        self.mallocs += 1

                        self.memop_file[addr] = f"{source}:{line_num}"

                    elif (match := self.MEM_calloc_regex.search(function)):

                        mnum  = match.group(1)
                        msize = int(match.group(2))
                        addr  = match.group(3)

                        size = mnum * msize

                        if self.size_at_addr.get(addr, 0) > 0:
                            # this means weeeeeirdo
                            print("Mixed debug compile, rebuild curl now")

                        self.size_at_addr[addr] = size
                        self.total_mem += size
                        self.mem_sum   += size

                        if self.trace:
                            print(f"CALLOC: calloc({mnum},{msize}) at {source}:{line_num}",
                                  f" makes totally {self.total_mem} bytes")

                        self.new_total(self.total_mem)
                        self.callocs += 1

                        self.memop_file[addr] = f"{source}:{line_num}"

                    elif (match := self.MEM_realloc_regex.search(function)):

                        old_addr = match.group(2)
                        new_size = int(match.group(3))
                        new_addr = match.group(4)

                        self.total_mem -= self.size_at_addr[old_addr]

                        if self.trace:
                            print(f"REALLOC: {self.size_at_addr[old_addr]} less bytes and ",
                                  end="")

                        self.size_at_addr[old_addr] = 0

                        self.total_mem += new_size
                        self.mem_sum   += new_size  # <AK> fix: was: size
                        self.size_at_addr[new_addr] = new_size

                        if self.trace:
                            print(f"{new_size} more bytes ({source}:{line_num})")

                        self.new_total(self.total_mem)
                        self.reallocs += 1

                        self.memop_file[old_addr] = ""
                        self.memop_file[new_addr] = f"{source}:{line_num}"

                    elif (match := self.MEM_strdup_regex.search(function)):
                        # strdup(a5b50) (8) = df7c0

                        dup  = match.group(1)
                        size = int(match.group(2))
                        addr = match.group(3)

                        self.size_at_addr[addr] = size
                        self.memop_file[addr] = f"{source}:{line_num}"

                        self.total_mem += size
                        self.mem_sum   += size

                        if self.trace:
                            print(f"STRDUP: {size} bytes at {self.memop_file[addr]}, "
                                  f"makes totally: {self.total_mem} bytes")

                        self.new_total(self.total_mem)
                        self.strdups += 1

                    elif (match := self.MEM_wcsdup_regex.search(function)):
                        # wcsdup(a5b50) (8) = df7c0

                        dup  = match.group(1)
                        size = int(match.group(2))
                        addr = match.group(3)

                        self.size_at_addr[addr] = size
                        self.memop_file[addr] = f"{source}:{line_num}"

                        self.total_mem += size
                        self.mem_sum   += size

                        if self.trace:
                            print(f"WCSDUP: {size} bytes at {self.memop_file[addr]}, "
                                  f"makes totally: {self.total_mem} bytes")

                        self.new_total(self.total_mem)
                        self.wcsdups += 1

                    else:
                        print(f"Not recognized input line: {function}")

                # FD url.c:1282 socket() = 5
                elif (match := self.FD_regex.search(line)):
                    # generic match for the filename+linenumber

                    source   = match.group(1)
                    line_num = match.group(2)
                    function = match.group(3)

                    if (match := self.FD_socket_regex.search(function)):

                        fd = match.group(1)

                        self.openf[fd] = True
                        self.open_file[fd] = f"{source}:{line_num}"
                        self.openfiles += 1
                        self.sockets += 1  # number of socket() calls

                    elif (match := self.FD_socketpair_regex.search(function)):

                        fd1 = match.group(1)
                        fd2 = match.group(2)

                        self.openf[fd1] = True
                        self.open_file[fd1] = f"{source}:{line_num}"
                        self.openfiles += 1
                        self.openf[fd2] = True
                        self.open_file[fd2] = f"{source}:{line_num}"
                        self.openfiles += 1

                    elif (match := self.FD_accept_regex.search(function)):

                        fd = match.group(1)

                        self.openf[fd] = True
                        self.open_file[fd] = f"{source}:{line_num}"
                        self.openfiles += 1

                    elif (match := self.FD_sclose_regex.search(function)):

                        fd = match.group(1)

                        if not self.openf.get(fd, False):
                            print("Close without open: {line}")
                        else:
                            self.openf[fd1] = False  # closed now
                            self.openfiles -= 1

                # FILE url.c:1282 fopen("blabla") = 0x5ddd
                elif (match := self.FILE_regex.search(line)):
                    # generic match for the filename+linenumber

                    source   = match.group(1)
                    line_num = match.group(2)
                    function = match.group(3)

                    if (match := self.FILE_fopen_regex.search(function)):

                        nil_or_addr = match.group(3)

                        if nil_or_addr == "(nil)":
                            pass  # do nothing when addr is NULL
                        else:
                            addr = match.group(4)

                            self.fopen[addr] = True
                            self.fopen_file[addr] = f"{source}:{line_num}"
                            self.fopens += 1

                    # fclose(0x1026c8)
                    elif (match := self.FILE_fclose_regex.search(function)):

                        addr = match.group(1)

                        if not self.fopen.get(addr, False):
                            print(f"fclose() without fopen(): {line}")
                        else:
                            self.fopen[addr] = False
                            self.fopens -= 1

                # GETNAME url.c:1901 getnameinfo()
                elif (match := self.GETNAME_regex.search(line)):

                    # not much to do
                    pass

                # SEND url.c:1901 send(83) = 83
                elif (match := self.SEND_regex.search(line)):

                    self.sends += 1

                # RECV url.c:1901 recv(102400) = 256
                elif (match := self.RECV_regex.search(line)):

                    self.recvs += 1

                # ADDR url.c:1282 getaddrinfo() = 0x5ddd
                elif (match := self.ADDR_regex.search(line)):
                    # generic match for the filename+linenumber

                    source   = match.group(1)
                    line_num = match.group(2)
                    function = match.group(3)

                    if (match := self.ADDR_getaddrinfo_regex.search(function)):

                        addr = match.group(2)

                        if addr == "(nil)":
                            pass  # do nothing when addr is NULL
                        else:
                            self.addr_info[addr] = True
                            self.addr_info_file[addr] = f"{source}:{line_num}"
                            self.addr_infos += 1

                        if self.trace:
                            print(f"GETADDRINFO ({source}:{line_num})")

                    # fclose(0x1026c8)
                    elif (match := self.ADDR_freeaddrinfo_regex.search(function)):

                        addr = match.group(1)

                        if not self.addr_info[addr]:
                            print(f"freeaddrinfo() without getaddrinfo(): {line}")
                        else:
                            self.addr_info[addr] = False
                            self.addr_infos -= 1
                        if self.trace:
                            print(f"FREEADDRINFO ({source}:{line_num})")

                else:
                    print(f"Not recognized prefix line: {line}")

    def new_total(self, total_mem: int):
        # count a max here
        if total_mem > self.max_mem:
            self.max_mem = total_mem

    def print_summary(self):

        if self.total_mem:
            print(f"Leak detected: memory still allocated: {self.total_mem} bytes")
            for addr, size in self.size_at_addr.items():
                if size > 0:
                    print(f"At {addr}, there's {size} bytes.")
                    print(f" allocated by {self.memop_file[addr]}")

        if self.openfiles:
            for fd in self.openf:
                if self.openf[fd]:
                    print(f"Open file descriptor created at {self.open_file[fd]}")

        if self.fopens:
            print("Open FILE handles left at:")
            for addr in self.fopen:
                if self.fopen[addr]:
                    print(f"fopen() called at {self.fopen_file[addr]}")

        if self.addr_infos:
            print("IPv6-style name resolve data left at:")
            for addr in self.addr_info_file:
                if self.addr_info[addr]:
                    print(f"getaddrinfo() called at {self.addr_info_file[addr]}")

        if self.verbose:
            self.print_verbose()

    def print_verbose(self):

        allocations = (self.mallocs + self.callocs + self.reallocs +
                       self.strdups + self.wcsdups)
        operations = allocations + self.sends + self.recvs + self.sockets

        print(f"""\
            Mallocs: {self.mallocs}
            Reallocs: {self.reallocs}
            Callocs: {self.callocs}
            Strdups:  {self.strdups}
            Wcsdups:  {self.wcsdups}
            Frees: {self.frees}
            Sends: {self.sends}
            Recvs: {self.recvs}
            Sockets: {self.sockets}
            Allocations: {allocations}
            Operations: {operations}""")

        print(f"Maximum allocated: {self.max_mem}")
        print(f"Total allocated: {self.mem_sum}")


def get_options(argv=sys.argv[1:]):
    """Process command line options"""
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    parser = argparse.ArgumentParser(prog=f"python {app_name}")

    parser.add_argument("-l", "--showlimit", action="store_true",
                        default=False, help="memlimit failure displayed")
    parser.add_argument("-v", "--verbose", action="store", type=int, default=0,
                        help="Verbose")
    parser.add_argument("-t", "--trace", action="store", type=int, default=0,
                        help="Trace")
    parser.add_argument("dump_file", type=Path, help="dump file")

    options = parser.parse_args(argv)
    options._app_name   = app_name
    options._arg_parser = parser

    return options


def main(argv=sys.argv[1:]) -> int:

    # Get the options from the user.
    options = get_options(argv)

    if not options.dump_file.is_file():
        options._arg_parser.print_help()
        return 2

    mem_analyze = MemAnalyze()
    mem_analyze.verbose = options.verbose
    mem_analyze.trace   = options.trace

    if options.showlimit:
        mem_analyze.memlimit(options.dump_file)
    else:
        mem_analyze.analyze(options.dump_file)
        mem_analyze.print_summary()


if __name__ == "__main__":
    sys.exit(main())
