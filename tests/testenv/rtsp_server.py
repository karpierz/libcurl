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

import argparse
import sys
import os
from pathlib import Path

import serverhelp
from pathhelp import exe_ext

curr_dir: Path = Path(".")


def get_options(argv=sys.argv[1:]):
    """Process command line options"""
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    parser = argparse.ArgumentParser(prog=f"python {app_name}")

    parser.add_argument("--port", action="store", type=int, default=8990,
                        help="port to listen on")
    parser.add_argument("--id", action="store", type=int, default=1,
                        help="server ID")
    parser.add_argument("--ipv4", action="store_true", default=False,
                        help="IPv4 flag")
    parser.add_argument("--ipv6", action="store_true", default=False,
                        help="IPv6 flag")
    parser.add_argument("--pidfile", action="store", type=Path,
                        help="file name for the PID")
    parser.add_argument("--portfile", action="store", type=Path,
                        help="file name for the PID")
    parser.add_argument("--logfile", action="store", type=Path,
                        help="file name for the log")
    parser.add_argument("--logdir", action="store", type=Path, default=str(curr_dir/"log"),
                        help="logs directory")
    parser.add_argument("--srcdir", action="store", type=Path,
                        help="test directory")
    parser.add_argument("--verbose", action="store", type=int, default=0,
                        help="verbose output")

    options = parser.parse_args(argv)
    options._app_name   = app_name
    options._arg_parser = parser

    return options


def main(argv=sys.argv[1:]) -> int:

    # Get the options from the user.
    options = get_options(argv)

    proto:     str  = "rtsp"  # protocol the rtsp server speaks
    port:      int  = options.port
    id_num:    int  = options.id if options.id > 0 else 1
    ip_vnum:   int  = 6 if options.ipv6 else 4 if options.ipv4 else 4
    pid_file:  Path = options.pidfile
    port_file: Path = options.portfile
    log_file:  Path = options.logfile
    log_dir:   Path = options.logdir
    src_dir:   Path = options.srcdir
    verbose:   int  = options.verbose

    # Initialize command line option dependent variables

    if not pid_file:  pid_file  = serverhelp.server_pid_file(curr_dir, proto, ip_vnum, id_num)
    if not port_file: port_file = serverhelp.server_port_file(pid_dir, proto, ip_vnum, id_num)  # <AK>: added
    if not log_file:  log_file  = serverhelp.server_log_file(log_dir,  proto, ip_vnum, id_num)
    if not src_dir:   src_dir   = Path(os.environ.get("srcdir", "."))

    flags  = f'--pidfile "{pid_file}" '
    flags += f'--portfile "{port_file}" '
    flags += f'--logfile "{log_file}" '
    flags += f'--logdir "{log_dir}" '

    flags += f"--ipv{ip_vnum} "
    flags += f"--port {port} "
    flags += f'--srcdir "{src_dir}"'

    exe = f"server/rtspd{exe_ext('SRV')}"
    if verbose: print(f"RUN: {exe} {flags}", file=sys.stderr)
    sys.stdout.reconfigure(line_buffering=False)
    sys.stderr.reconfigure(line_buffering=False)
    exec(f"exec {exe} {flags}")


if __name__ == "__main__":
    sys.exit(main())
