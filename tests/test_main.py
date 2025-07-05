# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

import unittest
import time
import sys, pathlib
test_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(test_dir/"libtest"))

import libcurl as lcurl
import _tutil as tutil

print()


class MainTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_main(self):
        self.assertTrue(lcurl.CURL_AT_LEAST_VERSION(7,81,0))

    def test_tv(self):
        before: lcurl.timeval = tutil.tvnow()
        time.sleep(6.5)
        after: lcurl.timeval = tutil.tvnow()
        exec_time:      int   = tutil.tvdiff(after, before)       # milliseconds
        exec_time_secs: float = tutil.tvdiff_secs(after, before)  # seconds (float)
        self.assertEqual(exec_time // 10,           650)
        self.assertEqual(int(exec_time_secs * 100), 650)
