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
Stream-parse a document using the streaming Expat parser.
"""

# Written by David Strauss
#
# Expat   => https://libexpat.github.io/
# PyExpat => https://docs.python.org/3/library/pyexpat.html

import sys
import ctypes as ct
from xml.parsers import expat

import libcurl as lcurl
from curltestutils import *  # noqa


class MemoryStruct(ct.Structure):
    _fields_ = [
    ("memory", ct.c_void_p),  # ??? char *
    ("size",   ct.c_size_t),
]

def init_memory(chunk: MemoryStruct):
    chunk.memory = None
    chunk.size   = 0


class ParserStruct(ct.Structure):
    _fields_ = [
    ("ok",    ct.c_bool),
    ("tags",  ct.c_size_t),
    ("depth", ct.c_size_t),
    ("characters", MemoryStruct),
]


def start_element(name, attrs):
    global state

    state.tags  += 1
    state.depth += 1

    # Get a clean slate for reading in character data.
    libc.free(state.characters.memory)
    init_memory(state.characters)


def end_element(name):
    global state

    state.depth -= 1
    print("%5u   %10u   %s" % (state.depth, state.characters.size, name))


def character_data(data):
    global state

    chunk = state.characters
    data_size = len(data)

    memory = libc.realloc(chunk.memory, chunk.size + data_size + 1)
    if not memory:
        # Out of memory.
        print("Not enough memory (realloc returned NULL).",
              file=sys.stderr)
        state.ok = False
        return;

    chunk.memory = memory
    ct.memmove(chunk.memory + chunk.size, data, data_size)
    chunk.size += data_size
    ct.memset(chunk.memory + chunk.size, 0, 1)


@lcurl.write_callback
def parse_stream_callback(buffer, size, nitems, stream):
    parser = lcurl.from_oid(stream)
    buffer_size = size * nitems

    global state

    # Only parse if we are not already in a failure state.
    if not state.ok:
        return buffer_size

    try:
        parser.Parse(bytes(buffer[:buffer_size]), False)
    except expat.ExpatError as exc:
        print("Parsing response buffer of length %u failed with "
              "error code %d (%s)." %
              (buffer_size, exc.code, expat.ErrorString(exc.code)),
              file=sys.stderr)
        state.ok = False

    return buffer_size


def main(argv=sys.argv[1:]):

    url: str = (argv[0] if len(argv) >= 1 else
                "https://www.w3schools.com/xml/simple.xml")

    global state
    state = ParserStruct()
    # Initialize the state structure for parsing.
    ct.memset(ct.byref(state), 0, ct.sizeof(state))
    state.ok = True
    init_memory(state.characters)

    # Initialize a namespace-aware parser.
    parser = expat.ParserCreate(namespace_separator="")
    parser.StartElementHandler  = start_element
    parser.EndElementHandler    = end_element
    parser.CharacterDataHandler = character_data

    # Initialize a libcurl handle.
    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(True, curl):
        if not curl: return 1

        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
        if defined("SKIP_PEER_VERIFICATION"):
            lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, parse_stream_callback)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(parser))

        print("Depth   Characters   Closing Tag")

        # Perform the request and any follow-up parsing.
        res: int = lcurl.easy_perform(curl)

        # Check for errors
        if res != lcurl.CURLE_OK:
            handle_easy_perform_error(res)
        elif state.ok:
            # Expat requires one final call to finalize parsing.
            try:
                parser.Parse(b"", True)
            except expat.ExpatError as exc:
                print("Finalizing parsing failed with error code %d (%s)." %
                      (exc.code, expat.ErrorString(exc.code)),
                      file=sys.stderr)
            else:
                print("                     --------------")
                print("                     %u tags total" % state.tags)

    # Clean up.
    del parser
    libc.free(state.characters.memory)

    return 0


sys.exit(main())
