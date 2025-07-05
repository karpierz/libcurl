# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

import unittest
import threading
import runpy
import sys, pathlib
test_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(test_dir.parent/"examples"))

from natsort import natsorted

import libcurl as lcurl

inp_dir = test_dir/"inp_dir"
out_dir = test_dir/"out_dir"
log_dir = test_dir/"log_dir"

examples = {
    "10-at-a-time": {"args": []},
    "address-scope": {"args": []},
    "altsvc": {"args": []},
    "anyauthput": {"args": []},
    #"block_ip.nok": {"args": []},
    "cacertinmem": {"args": []},
    "certinfo": {"args": []},
    "chkspeed": {"args": []},
    "connect-to": {"args": []},
    "cookie_interface": {"args": []},
    #"crawler.nok": {"args": []},
    "debug": {"args": []},
    "default-scheme": {"args": []},
    #"ephiperfifo".nok: {"args": []},
    #"evhiperfifo".nok: {"args": []},
    "externalsocket": {"args": []},
    "fileupload": {"args": []},
    "ftp-wildcard": {"args": []},
    "ftpget": {"args": []},
    "ftpgetinfo": {"args": []},
    "ftpgetresp": {"args": []},
    "ftpsget": {"args": []},
    "ftpupload": {"args": []},
    "ftpuploadfrommem": {"args": []},
    "ftpuploadresume": {"args": []},
    "getinfo": {"args": []},
    "getinmemory": {"args": []},
    "getredirect": {"args": []},
    "getreferrer": {"args": []},
    #"ghiper.nok": {"args": []},
    "headerapi": {"args": []},
    #"hiperfifo.nok": {"args": []},
    "href_extractor": {"args": []},
    "hsts-preload": {"args": []},
    "htmltidy": {"args": []},
    "htmltitle": {"args": []},
    "http-options": {"args": []},
    "http-post": {"args": []},
    "http2-download": {"args": []},
    "http2-pushinmemory": {"args": []},
    "http2-serverpush": {"args": []},
    "http2-upload": {"args": []},
    "http3-present": {"args": []},
    "http3": {"args": []},
    "httpcustomheader": {"args": []},
    "httpput-postfields": {"args": []},
    "httpput": {"args": []},
    "https": {"args": []},
    "imap-append": {"args": []},
    "imap-authzid": {"args": []},
    "imap-copy": {"args": []},
    "imap-create": {"args": []},
    "imap-delete": {"args": []},
    "imap-examine": {"args": []},
    "imap-fetch": {"args": []},
    "imap-list": {"args": []},
    "imap-lsub": {"args": []},
    "imap-multi": {"args": []},
    "imap-noop": {"args": []},
    "imap-search": {"args": []},
    #"imap-ssl": {"args": []},
    "imap-store": {"args": []},
    "imap-tls": {"args": []},
    "interface": {"args": []},
    "ipv6": {"args": []},
    "keepalive": {"args": []},
    "localport": {"args": []},
    "maxconnects": {"args": []},
    "multi-app": {"args": []},
    "multi-debugcallback": {"args": []},
    "multi-double": {"args": []},
    #"multi-event.nok": {"args": []},
    "multi-formadd": {"args": []},
    "multi-legacy": {"args": []},
    "multi-post": {"args": []},
    "multi-single": {"args": []},
    #"multi-uv.nok": {"args": []},
    #"multithread": {"args": []},
    "netrc": {"args": []},
    "parseurl": {"args": []},
    "persistent": {"args": []},
    "pop3-authzid": {"args": []},
    "pop3-dele": {"args": []},
    "pop3-list": {"args": []},
    "pop3-multi": {"args": []},
    "pop3-noop": {"args": []},
    "pop3-retr": {"args": []},
    #"pop3-ssl": {"args": []},
    "pop3-stat": {"args": []},
    "pop3-tls": {"args": []},
    "pop3-top": {"args": []},
    "pop3-uidl": {"args": []},
    "post-callback": {"args": []},
    "postinmemory": {"args": []},
    "postit2-formadd": {"args": []},
    "postit2": {"args": []},
    "progressfunc": {"args": []},
    "protofeats": {"args": []},
    "range": {"args": []},
    "resolve": {"args": []},
    "rtsp-options": {"args": []},
    "sendrecv": {"args": []},
    "sepheaders": {"args": []},
    "sessioninfo": {"args": []},
    "sftpget": {"args": []},
    "sftpuploadresume": {"args": []},
    "shared-connection-cache": {"args": []},
    "simple": {"args": []},
    "simplepost": {"args": []},
    "simplessl": {"args": []},
    #"smooth-gtk-thread.nok": {"args": []},
    "smtp-authzid": {"args": []},
    "smtp-expn": {"args": []},
    "smtp-mail": {"args": []},
    "smtp-mime": {"args": []},
    "smtp-multi": {"args": []},
    "smtp-ssl": {"args": []},
    "smtp-tls": {"args": []},
    "smtp-vrfy": {"args": []},
    "sslbackend": {"args": []},
    "synctime": {"args": []},
    "threaded-ssl": {"args": []},
    "unixsocket": {"args": []},
    "url2file": {"args": []},
    "urlapi": {"args": []},
    "usercertinmem": {"args": []},
    "websocket-cb": {"args": []},
    "websocket": {"args": []},
    "xmlstream": {"args": []},
}


class ExamplesTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rep_path = test_dir/"_result_examples_.txt"
        cls.rep = cls.rep_path.open("wt", newline="")
        cls.lock = threading.Lock()

    @classmethod
    def tearDownClass(cls):
        cls.rep.close()
        with cls.rep_path.open("rt", newline="") as rep:
            rep_lines = rep.readlines()
        with cls.rep_path.open("wt", newline="") as rep:
            rep.writelines(natsorted(set(rep_lines)))

    def setUp(self):
        self.lock.acquire()

    def tearDown(self):
        self.lock.release()

    def _test(self, test_name):
        defs  = tests[test_name].get("defs",  [])
        exits = tests[test_name].get("exits", [0])
        py_path = (test_dir.parent/"examples"/test_name.partition(".")[0]).with_suffix(".py")
        sys.argv = [None] + examples[test_name]["args"]
        try:
            res = 0
            runpy.run_path(py_path, run_name="__main__",
                           init_globals={define: 1 for define in defs})
        except SystemExit as exc:
            res = exc.code
        print(f"Example: {test_name}:",
              "OK" if res in exits else f"ERROR: {res}",
              file=self.rep)
        self.rep.flush()

TestCase = ExamplesTestCase

unittest_name = lambda name: "test_" + name.replace(".", "_")

for test_name in examples:
    setattr(TestCase, unittest_name(test_name),
            lambda self, _test_name=test_name: self._test(_test_name))


if __name__.rpartition(".")[-1] == "__main__":
    main_test = TestCase()
    TestCase.setUpClass()
    for test_name in examples:
        getattr(TestCase, unittest_name(test_name))(main_test)
    TestCase.tearDownClass()
    sys.stderr.flush()
    sys.stdout.flush()
    print("\nFINISH all examples")
