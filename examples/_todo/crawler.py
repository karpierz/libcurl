#***************************************************************************
#                                  _   _ ____  _
#  Project                     ___| | | |  _ \| |
#                             / __| | | | |_) | |
#                            | (__| |_| |  _ <| |___
#                             \___|\___/|_| \_\_____|
#
# Copyright (C) 2018 - 2022 Jeroen Ooms <jeroenooms@gmail.com>
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
Web crawler based on curl and libxml2 to stress-test curl with
hundreds of concurrent connections to various servers.
"""

import sys
import ctypes as ct
#include <libxml/HTMLparser.h>
#include <libxml/xpath.h>
#include <libxml/uri.h>

import libcurl as lcurl


# Parameters
int max_con               = 200
int max_total             = 20000
int max_requests          = 500
int max_link_per_page     = 5
int follow_relative_links = 0

char *start_page = b"https://www.reuters.com"


pending_interrupt = False

void sighandler(int dummy)
    global pending_interrupt
    pending_interrupt = True


# resizable buffer
typedef struct {
    char *buf;
    size_t size;
} memory;


size_t grow_buffer(void *contents, size_t sz, size_t nmemb, void *ctx):

    size_t realsize = sz * nmemb;
    memory *mem = (memory*) ctx;

    char *ptr = realloc(mem->buf, mem->size + realsize);
    if not ptr:
        # out of memory
        print("not enough memory (realloc returned NULL)")
        return 0

    mem->buf = ptr;
    memcpy(&(mem->buf[mem->size]), contents, realsize);
    mem->size += realsize;
    return realsize;


def make_handle(url: str)-> ct.POINTER(lcurl.CURL):

    curl: ct.POINTER(lcurl.CURL) = lcurl.easy_init()

    # Important: use HTTP2 over HTTPS
    lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTP_VERSION,
                            lcurl.CURL_HTTP_VERSION_2TLS)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_URL, url.encode("utf-8"))

    # buffer body
    memory* mem = malloc(sizeof(memory))
    mem->size = 0;
    mem->buf  = malloc(1)

    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, grow_buffer)
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, mem)
    curl_easy_setopt(curl, CURLOPT_PRIVATE,   mem)

    # For completeness
    lcurl.easy_setopt(curl, lcurl.CURLOPT_ACCEPT_ENCODING, b"")
    lcurl.easy_setopt(curl, lcurl.CURLOPT_TIMEOUT, 5)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_FOLLOWLOCATION, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_MAXREDIRS, 10)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_CONNECTTIMEOUT, 2)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_COOKIEFILE, b"")
    lcurl.easy_setopt(curl, lcurl.CURLOPT_FILETIME, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_USERAGENT, b"mini crawler")
    lcurl.easy_setopt(curl, lcurl.CURLOPT_HTTPAUTH, lcurl.CURLAUTH_ANY)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_UNRESTRICTED_AUTH, 1)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_PROXYAUTH, lcurl.CURLAUTH_ANY)
    lcurl.easy_setopt(curl, lcurl.CURLOPT_EXPECT_100_TIMEOUT_MS, 0)

    return curl


# HREF finder implemented in libxml2 but could be any HTML parser
size_t follow_links(CURLM * mcurl, memory *mem, char *url):

    int opts = (HTML_PARSE_NOBLANKS  | HTML_PARSE_NOERROR |
                HTML_PARSE_NOWARNING | HTML_PARSE_NONET)

    htmlDocPtr doc = htmlReadMemory(mem->buf, mem->size, url, NULL, opts);
    if !doc:
        return 0

    xmlChar *xpath = (xmlChar*) "//a/@href";
    xmlXPathContextPtr context = xmlXPathNewContext(doc);
    xmlXPathObjectPtr result = xmlXPathEvalExpression(xpath, context);
    xmlXPathFreeContext(context);
    if !result:
        return 0

    xmlNodeSetPtr nodeset = result->nodesetval;
    if xmlXPathNodeSetIsEmpty(nodeset):
        xmlXPathFreeObject(result);
        return 0

    size_t count = 0;
    for ( int i = 0; i < nodeset->nodeNr; i++ ):

        double r = rand();
        int x = r * nodeset->nodeNr / RAND_MAX;
        const xmlNode *node = nodeset->nodeTab[x]->xmlChildrenNode;
        xmlChar *href = xmlNodeListGetString(doc, node, 1);
        if(follow_relative_links):
            xmlChar *orig = href;
            href = xmlBuildURI(href, (xmlChar *) url);
            xmlFree(orig);

        char *link = (char *) href;
        if (!link || len(link) < 20):
            continue;
        if !strncmp(link, "http://", 7) || !strncmp(link, "https://", 8):
            lcurl.multi_add_handle(mcurl, make_handle(link))
            if(count++ == max_link_per_page)
                break;
         xmlFree(link);

    xmlXPathFreeObject(result)

    return count


def is_html(char *ctype) -> bool:
    return ctype and len(ctype) > 10 and strstr(ctype, "text/html")


def main(argv=sys.argv[1:]):

    signal(SIGINT, sighandler);
    LIBXML_TEST_VERSION;

    lcurl.global_init(lcurl.CURL_GLOBAL_DEFAULT)
    mcurl: ct.POINTER(lcurl.CURLM) = lcurl.multi_init()

    lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_MAX_TOTAL_CONNECTIONS, max_con)
    lcurl.multi_setopt(mcurl, lcurl.CURLMOPT_MAX_HOST_CONNECTIONS, 6)

    # enables http/2 if available
    lcurl.multi_setopt(mcurl,
                       lcurl.CURLMOPT_PIPELINING, lcurl.CURLPIPE_MULTIPLEX)

    # sets html start page
    lcurl.multi_add_handle(mcurl, make_handle(start_page))

    int msgs_left;

    pending  = 0
    complete = 0
    still_running = ct.c_int(1)
    while still_running.value and not pending_interrupt:

        int numfds;
        lcurl.multi_wait(mcurl, NULL, 0, 1000, &numfds)
        lcurl.multi_perform(mcurl, ct.byref(still_running))

        # See how the transfers went
        CURLMsg *m = NULL;
        while((m = curl_multi_info_read(mcurl, &msgs_left)))
            if (m->msg != CURLMSG_DONE): continue

            CURL *handle = m->easy_handle;
            char *url;
            memory *mem;
            lcurl.easy_getinfo(handle, CURLINFO_PRIVATE, &mem);
            lcurl.easy_getinfo(handle, CURLINFO_EFFECTIVE_URL, &url);
            if m->data.result == CURLE_OK:
                res_status = ct.c_long()
                lcurl.easy_getinfo(handle, CURLINFO_RESPONSE_CODE, ct.byref(res_status))
                if res_status.value == 200:
                    char *ctype;
                    lcurl.easy_getinfo(handle, CURLINFO_CONTENT_TYPE, &ctype);
                    print("[%d] HTTP 200 (%s): %s" % (complete, ctype, url))
                    if is_html(ctype) and mem->size > 100:
                        if pending < max_requests and (complete + pending) < max_total:
                            pending += follow_links(mcurl, mem, url)
                            still_running.value = 1
                else:
                    print("[%d] HTTP %d: %s" % (complete, res_status.value, url))
            else:
                print("[%d] Connection failure: %s" % (complete, url))

            lcurl.multi_remove_handle(mcurl, handle)
            lcurl.easy_cleanup(handle)
            libc.free(mem->buf)
            libc.free(mem)

            complete += 1
            pending  -= 1

    lcurl.multi_cleanup(mcurl)
    lcurl.global_cleanup()

    return 0


sys.exit(main())
