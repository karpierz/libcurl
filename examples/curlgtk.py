#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (c) 2000 - 2022 David Odin (aka DindinX) for MandrakeSoft
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
Use the libcurl in a tkinter-threaded application
"""

import sys
import threading
import ctypes as ct
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import libcurl as lcurl
from curltestutils import *  # noqa

here = Path(__file__).resolve().parent


OUT_FILE = here/"output/test.curl"
gui = None


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten)
    return nwritten


@lcurl.read_callback
def read_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    bread = file.read(size * nitems)
    if not bread: return 0
    nread = len(bread)
    ct.memmove(buffer, bread, nread)
    return nread


@lcurl.progress_callback
def progress_function(clientp, dltotal, dlnow, ultotal, ulnow):
    root = lcurl.from_oid(clientp)
    progress_bar = root.nametowidget(".progress_bar")
    value_label  = root.nametowidget(".value_label")
    value = min(int(dlnow * 100.0 / dltotal) if dltotal else 0, 100)
    progress_bar["value"] = value
    if value < 100:
        value_label["text"] = f"Current Progress: {progress_bar['value']}%"
    else:
        value_label["text"] = "The progress completed!"
    return 0


def my_thread(url: str):
    global OUT_FILE, gui

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl):
        if not curl: return

        with OUT_FILE.open("wb") as out_file:

            lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))
            if defined("SKIP_PEER_VERIFICATION"):
                lcurl.easy_setopt(curl, lcurl.CURLOPT_SSL_VERIFYPEER, 0)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(out_file))
            lcurl.easy_setopt(curl, lcurl.CURLOPT_READFUNCTION,  read_function)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_NOPROGRESS, 0)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_PROGRESSFUNCTION, progress_function)
            lcurl.easy_setopt(curl, lcurl.CURLOPT_PROGRESSDATA, id(gui))

            # Perform the custom request
            res: int = lcurl.easy_perform(curl)

            # Check for errors
            if res != lcurl.CURLE_OK:
                print("%s" % lcurl.easy_strerror(res).decode("utf-8"),
                      file=sys.stderr)


def main(argv=sys.argv[1:]):
    app_name = sys.argv[0].rpartition("/")[2].rpartition("\\")[2]

    if len(argv) < 1:
        print("Usage: %s <URL>" % app_name)
        return 1

    url: str = argv[0]
    global gui

    # Must initialize libcurl before any threads are started
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    with curl_guard(True):

        # root window
        gui = root = tk.Tk()
        root.geometry("300x120")
        root.title("libcurl's Progressbar Demo")

        # progressbar
        progress_bar = ttk.Progressbar(root, name="progress_bar",
                                       orient="horizontal", length=280,
                                       mode="determinate")
        # label
        value_label = ttk.Label(root, name="value_label")

        # place the progressbar and label
        progress_bar.grid(column=0, row=0, columnspan=2, padx=10, pady=20)
        value_label.grid(column=0, row=1, columnspan=2)

        def start():
            # Init thread
            try:
                thread = threading.Thread(target=gui_thread, args=(url,))
                thread.start()
            except Exception as exc:
                print("Cannot create the thread", file=sys.stderr)
                return 1

        def gui_thread(url):
            start_button.config(state="disable")
            reset_button.config(state="disable")
            try:
                reset()
                return my_thread(url)
            finally:
                start_button.config(state="enable")
                reset_button.config(state="enable")

        def reset():
            progress_function(id(root), 0, 0, 0, 0)
            progress_bar.stop()

        # start button
        start_button = ttk.Button(root, text="Start", command=start)
        start_button.grid(column=0, row=2, padx=10, pady=10, sticky=tk.E)

        # reset button
        reset_button = ttk.Button(root, text="Reset", command=reset)
        reset_button.grid(column=1, row=2, padx=10, pady=10, sticky=tk.W)

        reset()
        root.mainloop()

    return 0


sys.exit(main())
