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
Multi_socket API using libuv
"""

import sys
import ctypes as ct
#include <uv.h>

import libcurl as lcurl
from curltestutils import *  # noqa


# Example application using the multi socket interface to download multiple
# files in parallel, powered by libuv.
#
# Requires libuv and (of course) libcurl.
#
# See https://nikhilm.github.io/uvbook/ for more information on libuv.


uv_loop_t *loop;
CURLM * mcurl;
uv_timer_t timeout;


typedef struct curl_context_s {
    uv_poll_t poll_handle;
    curl_socket_t sockfd;
} curl_context_t;


static curl_context_t * create_curl_context(curl_socket_t sockfd):

    context = (curl_context_t *) malloc(sizeof(*context));
    context->sockfd = sockfd

    uv_poll_init_socket(loop, &context->poll_handle, sockfd);
    context->poll_handle.data = context;

    return context;


static void curl_close_cb(uv_handle_t *handle)

    curl_context_t * context = (curl_context_t *) handle->data;
    free(context);


static void destroy_curl_context(curl_context_t *context):

    uv_close((uv_handle_t *) &context->poll_handle, curl_close_cb);


static void add_download(const char *url, int num)

    char filename[50];
    FILE * file;
    CURL * handle;

    snprintf(filename, 50, "%d.download", num);

    file = fopen(filename, "wb")
    if ! file:
        fprintf(stderr, "Error opening %s\n", filename);
        return

    handle = lcurl.easy_init()

    curl_easy_setopt(handle, CURLOPT_WRITEDATA, file)
    curl_easy_setopt(handle, CURLOPT_PRIVATE,   file)
    curl_easy_setopt(handle, CURLOPT_URL, url);
    lcurl.multi_add_handle(mcurl, handle)

    fprintf(stderr, "Added download %s -> %s\n", url, filename);


static void check_multi_info(void):

    char *done_url;
    CURLMsg *message;
    int pending;
    CURL *easy_handle;
    FILE *file;

    while((message = curl_multi_info_read(mcurl, &pending))) {
      switch(message->msg) {
      case CURLMSG_DONE:
        /* Do not use message data after calling libcurl.multi_remove_handle() and
           libcurl.easy_cleanup(). As per curl_multi_info_read() docs:
           "WARNING: The data the returned pointer points to will not survive
           calling curl_multi_cleanup, curl_multi_remove_handle or
           curl_easy_cleanup." */
        easy_handle = message->easy_handle;

        lcurl.easy_getinfo(easy_handle, CURLINFO_EFFECTIVE_URL, &done_url);
        lcurl.easy_getinfo(easy_handle, CURLINFO_PRIVATE, &file);
        printf("%s DONE\n", done_url);

        lcurl.multi_remove_handle(mcurl, easy_handle)
        lcurl.easy_cleanup(easy_handle)
        if(file) {
          fclose(file);
        }
        break;

      default:
        fprintf(stderr, "CURLMSG default\n");
        break;
      }
    }


static void curl_perform(uv_poll_t *req, int status, int events)

    int running_handles;
    int flags = 0;
    curl_context_t *context;

    if (events & UV_READABLE):
        flags |= CURL_CSELECT_IN
    if (events & UV_WRITABLE):
        flags |= CURL_CSELECT_OUT

    context = (curl_context_t *) req->data;

    curl_multi_socket_action(mcurl, context->sockfd, flags,
                             &running_handles);

    check_multi_info()


static void on_timeout(uv_timer_t *req)

    int running_handles;
    curl_multi_socket_action(mcurl, CURL_SOCKET_TIMEOUT, 0,
                             &running_handles)
    check_multi_info()


static int start_timeout(CURLM *multi, long timeout_ms, void *userp)

    if timeout_ms < 0:
        uv_timer_stop(&timeout)
    else:
        if timeout_ms == 0:
            timeout_ms = 1  # 0 means directly call socket_action,
                            # but we will do it in a bit
        uv_timer_start(&timeout, on_timeout, timeout_ms, 0)

    return 0


int handle_socket(CURL *easy, curl_socket_t s, int action, void *userp, void *socketp):

    curl_context_t *curl_context;
    int events = 0;

    switch(action) {
    case CURL_POLL_IN:
    case CURL_POLL_OUT:
    case CURL_POLL_INOUT:
      curl_context = socketp ?
        (curl_context_t *) socketp : create_curl_context(s);

      curl_multi_assign(mcurl, s, (void *) curl_context);

      if(action != CURL_POLL_IN)
        events |= UV_WRITABLE;
      if(action != CURL_POLL_OUT)
        events |= UV_READABLE;

      uv_poll_start(&curl_context->poll_handle, events, curl_perform);
      break;
    case CURL_POLL_REMOVE:
      if(socketp) {
        uv_poll_stop(&((curl_context_t*)socketp)->poll_handle);
        destroy_curl_context((curl_context_t*) socketp);
        curl_multi_assign(mcurl, s, NULL);
      }
      break;
    default:
      abort();
    }

    return 0


int main(int argc, char **argv):

    loop = uv_default_loop()

    if (argc <= 1):
        return 0

    if curl_global_init(CURL_GLOBAL_ALL):
        print(stderr, "Could not init curl")
        return 1
    mcurl = lcurl.multi_init()

    uv_timer_init(loop, &timeout);

    lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_SOCKETFUNCTION, handle_socket)
    lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_TIMERFUNCTION,  start_timeout)

    while (argc-- > 1):
        add_download(argv[argc], argc)

    uv_run(loop, UV_RUN_DEFAULT);
    lcurl.multi_cleanup(mcurl)

    return 0


sys.exit(main())