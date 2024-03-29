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
A multi threaded application that uses a progress bar to show status.
It uses Gtk+ to make a smooth pulse.
"""

import sys
import threading
from threading import RLock
import ctypes as ct
import tkinter as tk
from tkinter import ttk
#include <gtk/gtk.h>
#include <glib.h>

import libcurl as lcurl
from curltestutils import *  # noqa


# Written by Jud Bishop after studying the other examples provided with
# libcurl.

NUMT = 4

uris = [
    "90022",
    "90023",
    "90024",
    "90025",
    "90026",
    "90027",
    "90028",
    "90029",
    "90030",
]


@lcurl.write_callback
def write_function(buffer, size, nitems, stream):
    file = lcurl.from_oid(stream)
    buffer_size = size * nitems
    if buffer_size == 0: return 0
    bwritten = bytes(buffer[:buffer_size])
    nwritten = file.write(bwritten)
    return nwritten


lock = RLock()
j: int = 0


def run_one(http: str, j: int):
    global j

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    with curl_guard(False, curl) \
         open(uris[j], "wb") as outfile:
        if not curl: return -1

        print("j = %d", j)

        # Set the URL and transfer type
        lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, http.encode("utf-8"))
        # Write to the file
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEFUNCTION, write_function)
        lcurl.easy_setopt(curl, lcurl.CURLOPT_WRITEDATA, id(outfile))

        lcurl.easy_perform(curl)


def pull_one_url():
    global j
    # protect the reading and increasing of 'j' with a mutex
    with lock:
        while j < len(uris):
            i: int = j
            j += 1
            lock.release()
            try:
                http = g_strdup_printf("https://example.com/%s", uris[i]);
                if http:
                    run_one(http, i)
                    g_free(http);
            finally:
                lock.acquire()


gboolean pulse_bar(gpointer data):

    gdk_threads_enter();
    gtk_progress_bar_pulse(GTK_PROGRESS_BAR (data));
    gdk_threads_leave();

    # Return true so the function will be called again;
    # returning false removes this timeout function.
    return TRUE;


def create_thread(progress_bar):

    threads = []
    # Make sure I do not create more threads than uris.
    for i in range(min(NUMT, len(uris))):
        uri = uris[i]
        try: # &tid[i]
            thread = threading.Thread(target=pull_one_url)
            thread.start()
        except Exception as exc:
            print("Couldn't run thread number %d, error %s" % (i, exc),
                  file=sys.stderr);
        else:
            threads.append(thread)
            print("Thread %d, gets %s" % (i, uri), file=sys.stderr)

    # Wait for all threads to terminate.
    for i, thread in enumerate(threads):
        thread.join()
        print("Thread %d terminated" % i, file=sys.stderr)

    # This stops the pulsing if you have it turned on in the progress bar
    # section
    g_source_remove(GPOINTER_TO_INT(g_object_get_data(G_OBJECT(progress_bar),
                                                      "pulse_id")));
    # This destroys the progress bar
    gtk_widget_destroy(progress_bar);

    # [Un]Comment this out to kill the program rather than pushing close.
    # gtk_main_quit()


static gboolean on_quit(GtkWidget *window, gpointer data):
    gtk_main_quit();
    return FALSE;


def main(argv=sys.argv[1:]):

    # Must initialize libcurl before any threads are started
    lcurl.global_init(lcurl.CURL_GLOBAL_ALL)

    with curl_guard(True):

        # Base window
        top_window = tk.Tk()

        # Frame
        outside_frame = tk.Frame(top_window)
        gtk_frame_set_shadow_type(GTK_FRAME(outside_frame), GTK_SHADOW_OUT);

        # Frame
        inside_frame = tk.Frame(outside_frame)
        gtk_frame_set_shadow_type(GTK_FRAME(inside_frame), GTK_SHADOW_IN);
        gtk_container_set_border_width(GTK_CONTAINER(inside_frame), 5);

        # Progress bar
        progress_bar = ttk.Progressbar(inside_frame, name="progress_bar",
                                       orient="horizontal", length=280,
                                       mode="determinate")
        gtk_progress_bar_pulse(GTK_PROGRESS_BAR (progress_bar));
        # Make uniform pulsing
        gint pulse_ref = g_timeout_add(300, pulse_bar, progress_bar);
        g_object_set_data(G_OBJECT(progress_bar), "pulse_id",
                          GINT_TO_POINTER(pulse_ref));

        gtk_widget_show_all(top_window);
        print("gtk_widget_show_all")

        g_signal_connect(G_OBJECT (top_window), "delete-event",
                         G_CALLBACK(on_quit), NULL);

        if(!g_thread_create(&create_thread, progress_bar, FALSE, NULL) != 0):
            g_warning("cannot create the thread");

        gtk_main();
        gdk_threads_leave();
        print("gdk_threads_leave")

    return 0


sys.exit(main())
