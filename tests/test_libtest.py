# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

import unittest
import threading
import sys, pathlib
test_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(test_dir/"libtest"))

from natsort import natsorted

import libcurl as lcurl
from curl_test import (
    TEST_ERR_MAJOR_BAD,    # lcurl.CURLE_RESERVED126
    TEST_ERR_RUNS_FOREVER, # lcurl.CURLE_RESERVED125
    TEST_ERR_EASY_INIT,    # lcurl.CURLE_RESERVED124
    TEST_ERR_MULTI,        # lcurl.CURLE_RESERVED123
    TEST_ERR_NUM_HANDLES,  # lcurl.CURLE_RESERVED122
    TEST_ERR_SELECT,       # lcurl.CURLE_RESERVED121
    TEST_ERR_SUCCESS,      # lcurl.CURLE_RESERVED120
    TEST_ERR_FAILURE,      # lcurl.CURLE_RESERVED119
    TEST_ERR_USAGE,        # lcurl.CURLE_RESERVED118
    TEST_ERR_FOPEN,        # lcurl.CURLE_RESERVED117
    TEST_ERR_FSTAT,        # lcurl.CURLE_RESERVED116
    TEST_ERR_BAD_TIMEOUT,  # lcurl.CURLE_RESERVED115
)

inp_dir = test_dir/"inp_dir"
out_dir = test_dir/"out_dir"
log_dir = test_dir/"log_dir"

tests = {
    "lib500":    {"args": ["http://example.com", out_dir/"lib500.txt"]},
    "lib585":    {"args": ["http://example.com", out_dir/"lib585.txt"]},
    "lib501":    {"args": ["http://example.com"]},
    "lib502":    {"args": ["http://example.com"]},
    "lib503":    {"args": ["http://example.com"]},
    "lib504":    {"args": ["http://example.com"]},
    "lib505.1":  {"args": ["http://example.com", inp_dir/"uploadthis.txt"]},
    "lib505.2":  {"args": ["http://example.com", inp_dir/"_non_existent_"], "exits": [TEST_ERR_MAJOR_BAD]},
    "lib505.3":  {"args": ["http://example.com", inp_dir/"_zero_sized_"], "exits": [TEST_ERR_MAJOR_BAD]},
    "lib505.4":  {"args": ["http://example.com"], "exits": [TEST_ERR_USAGE]},
    "lib506":    {"args": ["http://example.com", inp_dir/"cookie_jar506"]},
    "lib507":    {"args": ["http://example.com"]},
    "lib508":    {"args": ["http://example.com"]},
    "lib509":    {"args": ["http://example.com"]},
    "lib510":    {"args": ["http://example.com"]},
    "lib565.1":  {"args": ["http://example.com"]},
    "lib565.2":  {"args": ["http://example.com", None]},
    "lib511":    {"args": ["http://example.com"]},
    "lib512":    {"args": ["http://example.com"]},
    "lib513":    {"args": ["http://example.com"]},
    "lib514":    {"args": ["http://example.com"]},
    "lib515":    {"args": ["http://example.com"]},
    "lib516":    {"args": ["http://example.com"]},
    "lib517":    {"args": ["http://example.com"]},
    "lib518":    {"args": ["http://example.com"]},
    "lib519":    {"args": ["http://example.com"]},
    "lib520":    {"args": ["http://example.com"]},
    "lib521":    {"args": ["http://example.com", "80"]},
    "lib523":    {"args": ["http://example.com", "xxx:yyy"]},
    "lib524":    {"args": ["http://example.com"]},
    "lib525.1":  {"args": ["http://example.com", inp_dir/"uploadthis.txt"]},
    "lib525.2":  {"args": ["http://example.com", inp_dir/"_non_existent_"], "exits": [TEST_ERR_FOPEN]},
    "lib525.3":  {"args": ["http://example.com"], "exits": [TEST_ERR_USAGE]},
    "lib529.1":  {"args": ["http://example.com", inp_dir/"uploadthis.txt"]},
    "lib529.2":  {"args": ["http://example.com", inp_dir/"_non_existent_"], "exits": [TEST_ERR_FOPEN]},
    "lib529.3":  {"args": ["http://example.com"], "exits": [TEST_ERR_USAGE]},
    "lib526":    {"args": ["http://example.com"]},
    "lib527":    {"args": ["http://example.com"]},
    #select_test_"lib530": {"args": ["http://example.com"]},  # NOK !
    "lib532":    {"args": ["http://example.com"]},
    "lib533":    {"args": ["http://example.com", "http://httpstat.us"]},
    "lib536":    {"args": ["http://example.com", "http://example.com", "example.com"]},
    "lib537":    {"args": ["http://example.com"]},
    "lib539":    {"args": ["http://example.com", "http://example.com/0001"]},
    "lib540":    {"args": ["http://example.com", "http://httpstat.us"]},
    "lib541.1":  {"args": ["http://example.com", inp_dir/"uploadthis.txt"]},
    "lib541.2":  {"args": ["http://example.com"], "exits": [TEST_ERR_USAGE]},
    "lib541.3":  {"args": ["http://example.com", inp_dir/"_non_existent_"], "exits": [TEST_ERR_MAJOR_BAD]},
    "lib541.4":  {"args": ["http://example.com", inp_dir/"_zero_sized_"], "exits": [TEST_ERR_MAJOR_BAD]},
    "lib542":    {"args": ["http://example.com"]},
    "lib543":    {"args": ["http://example.com"]},
    "lib544":    {"args": ["http://example.com"]},
    "lib545":    {"args": ["http://example.com"]},
    "lib547":    {"args": ["http://example.com"]},
    "lib548":    {"args": ["http://example.com"]},
    "lib549.1":  {"args": ["http://example.com"]},
    "lib549.2":  {"args": ["http://example.com", None, "yes"]},
    "lib552":    {"args": ["http://example.com"]},
    "lib553":    {"args": ["http://example.com"]},
    "lib554":    {"args": ["http://example.com"]},
    "lib587":    {"args": ["http://example.com"]},
    "lib555":    {"args": ["http://example.com"]},
    "lib556":    {"args": ["http://example.com"]},
    "lib696":    {"args": ["http://example.com"]},
    #"lib557":   {"args": ["http://example.com"]},  # !!! occasionally abnormal exit !!!
    "lib558":    {"args": ["http://example.com"]},
    "lib559":    {"args": ["http://example.com"]},
    "lib560":    {"args": ["https://example.com"]},
    "lib562":    {"args": ["http://example.com", "80"]},
    "lib564":    {"args": ["http://example.com"]},
    "lib566":    {"args": ["http://example.com", out_dir/"lib566.txt"]},
    "lib567":    {"args": ["http://example.com"]},
    "lib568.1":  {"args": ["http://example.com", inp_dir/"sdpf_file568"]},
    "lib568.2":  {"args": ["http://example.com", inp_dir/"_non_existent_"], "exits": [TEST_ERR_MAJOR_BAD]},
    "lib569.1":  {"args": ["http://example.com", out_dir/"sid_file569"]},
    "lib569.2":  {"args": ["http://example.com", out_dir], "exits": [TEST_ERR_MAJOR_BAD]},  # dir as _non_existent_ file
    "lib570":    {"args": ["http://example.com"]},
    #"lib571":   {"args": ["http://example.com", out_dir/"lib571.txt"]},  # !!! hungs up !!!
    "lib572.1":  {"args": ["http://example.com", inp_dir/"params_file572"]},
    "lib572.2":  {"args": ["http://example.com", inp_dir/"_non_existent_"], "exits": [TEST_ERR_MAJOR_BAD]},
    "lib573":    {"args": ["http://example.com"]},
    "lib574":    {"args": ["http://example.com"]},
    "lib575":    {"args": ["http://example.com"]},
    "lib576":    {"args": ["http://example.com"]},
    "lib578":    {"args": ["http://example.com", out_dir/"lib578.txt"]},
    "lib579.1":  {"args": ["http://example.com", out_dir/"lib579.txt"]},
    "lib579.2":  {"args": ["http://example.com", out_dir]},  # dir as _non_existent_ file
    #select_test_"lib582": {"args": ["http://example.com", inp_dir/"uploadthis.txt"]},  # NOK !
    "lib583":    {"args": ["http://example.com", None, None]},  # "curl_client_key.pub", "curl_client_key"
    "lib586":    {"args": ["http://example.com"]},
    "lib589":    {"args": ["http://example.com"]},
    "lib584":    {"args": ["http://example.com"]},
    "lib590.1":  {"args": ["http://example.com"]},
    "lib590.2":  {"args": ["http://example.com", None, None]},
    "lib591.1":  {"args": ["http://example.com", inp_dir/"uploadthis.txt", "2"]},
    "lib591.2":  {"args": ["http://example.com", inp_dir/"_non_existent_", "2"]},
    "lib597":    {"args": ["http://example.com"]},
    "lib598":    {"args": ["http://example.com"]},
    "lib599":    {"args": ["http://example.com", out_dir/"lib599.txt"]},
    "lib643":    {"args": ["http://example.com"]},
    "lib645":    {"args": ["http://example.com"]},
    "lib650":    {"args": ["http://example.com", inp_dir/"uploadthis.txt"]},
    "lib651":    {"args": ["http://example.com"]},
    "lib652":    {"args": ["http://example.com"]},
    "lib653":    {"args": ["http://example.com"]},
    "lib654":    {"args": ["http://example.com", inp_dir/"mime_file654"]},
    "lib655":    {"args": ["http://example.com"]},
    "lib658":    {"args": ["http://example.com"]},
    "lib659":    {"args": ["http://example.com"]},
    #"lib661":   {"args": ["http://example.com"]},  # !!! hungs up !!!
    "lib666":    {"args": ["http://example.com"]},
    "lib667":    {"args": ["http://example.com"]},
    "lib668":    {"args": ["http://example.com", inp_dir/"mime_file668"]},
    "lib670":    {"args": ["http://example.com"]},
    "lib671":    {"args": ["http://example.com"]},
    "lib672":    {"args": ["http://example.com"]},
    "lib673":    {"args": ["http://example.com"]},
    "lib674":    {"args": ["http://example.com"]},
    "lib676":    {"args": ["http://example.com", inp_dir/"cookies676"]},
    "lib677":    {"args": ["http://example.com"]},
    "lib678.1":  {"args": ["check"]},
    "lib678.2":  {"args": ["http://example.com"]},
    "lib678.3":  {"args": ["http://example.com"]},
    "lib678.4":  {"args": ["http://example.com", "_non_existent_"]},
    "lib694":    {"args": ["http://example.com", "http://example.com"]},
    "lib695":    {"args": ["http://example.com"]},
    "lib751":    {"args": ["https://www.example.com"]},
    #"lib1156":  {"args": ["http://example.com"]},  # !!! hungs up !!!
    "lib1301":   {"args": ["http://example.com"]},
    #"lib1308":  {"args": ["http://example.com"]},  # !!! fail !!!
    "lib1485":   {"args": ["http://example.com"]},
    "lib1500":   {"args": ["http://example.com"]},
    "lib1501":   {"args": ["http://example.com"]},
    "lib1502":   {"args": ["http://example.com", "127.0.0.1", "80"]},
    "lib1506":   {"args": ["http://example.com", "127.0.0.1", "80"]},
    "lib1507":   {"args": ["http://example.com"]},
    "lib1508":   {"args": ["http://example.com"]},
    "lib1509":   {"args": ["http://example.com"]},
    "lib1510":   {"args": ["http://example.com", "127.0.0.1", "80"]},
    "lib1511":   {"args": ["http://example.com"]},
    "lib1512":   {"args": ["http://example.com", "127.0.0.1", "80"]},
    "lib1513":   {"args": ["http://example.com"]},
    "lib1514":   {"args": ["http://example.com"]},
    "lib1539":   {"args": ["http://example.com"]},
    "lib1515":   {"args": ["http://example.com", "127.0.0.1", "80"]},
    "lib1517.1": {"args": ["check"]},
    "lib1517.2": {"args": ["http://example.com"]},
    "lib1518":   {"args": ["http://example.com"]},
    "lib1543":   {"args": ["http://example.com"]},
    "lib1520":   {"args": ["http://example.com"]},
    "lib1522":   {"args": ["http://example.com"]},
    "lib1523":   {"args": ["http://example.com"]},
    "lib1525":   {"args": ["http://example.com"]},
    "lib1526":   {"args": ["http://example.com"]},
    "lib1527":   {"args": ["http://example.com"]},
    "lib1528":   {"args": ["http://example.com"]},
    "lib1529":   {"args": ["http://example.com"]},
    "lib1530":   {"args": ["http://example.com"]},
    "lib1531":   {"args": ["http://example.com"]},
    "lib1532":   {"args": ["http://example.com"]},
    "lib1533":   {"args": ["http://example.com"]},
    "lib1534":   {"args": ["http://example.com"]},
    "lib1535":   {"args": ["http://example.com"]},
    "lib1536":   {"args": ["http://example.com"]},
    "lib1537":   {"args": ["http://example.com"]},
    "lib1538":   {"args": ["http://example.com"]},
    "lib1540":   {"args": ["http://example.com"]},
    "lib1541":   {"args": ["http://example.com"]},
    "lib1542":   {"args": ["http://example.com"]},
    "lib1545":   {"args": ["http://example.com"]},
    "lib1550":   {"args": ["http://example.com"]},
    "lib1551":   {"args": ["http://example.com"]},
    "lib1552.1": {"args": ["http://example.com"]},
    "lib1552.2": {"args": ["http://example.com", None]},
    "lib1553.1": {"args": ["http://example.com"]},
    "lib1553.2": {"args": ["http://example.com", None]},
    "lib1554":   {"args": ["http://example.com"]},
    "lib1555":   {"args": ["http://example.com"]},
    "lib1556":   {"args": ["http://example.com"]},
    "lib1557":   {"args": ["http://example.com"]},
    "lib1558":   {"args": ["http://example.com"]},
    "lib1559":   {"args": ["http://example.com"]},
    "lib1560":   {"args": ["http://example.com"]},
    "lib1564":   {"args": ["http://example.com"]},
    "lib1565":   {"args": ["http://example.com"]},
    "lib1567":   {"args": ["http://example.com"]},
    "lib1568":   {"args": ["http://example.com", "80"]},
    "lib1569":   {"args": ["http://example.com", "http://httpstat.us"]},
    "lib1571.1": {"args": ["http://example.com", 1571]},
    "lib1571.2": {"args": ["http://example.com", 1574]},
    "lib1571.3": {"args": ["http://example.com", 1575]},
    "lib1571.4": {"args": ["http://example.com", 1581]},
    "lib1576.1": {"args": ["http://example.com", 1576]},
    "lib1576.2": {"args": ["http://example.com", 1578]},
    "lib1591":   {"args": ["http://example.com"]},
    "lib1592":   {"args": ["http://example.com"]},
    "lib1593":   {"args": ["http://example.com"]},
    "lib1594":   {"args": ["http://example.com"]},
    "lib1597":   {"args": ["http://example.com"]},
    "lib1598":   {"args": ["http://example.com"]},
    "lib1662":   {"args": ["http://example.com"]},
    "lib1900":   {"args": ["http://example.com", log_dir/"first-hsts.txt", log_dir/"second-hsts.txt"]},
    #"lib1901":  {"args": ["http://example.com"]}, # !!! abnormal exit !!!
    "lib1903":   {"args": ["http://example.com", inp_dir/"cookies1903", inp_dir/"cookie_jar1903"]},
    #"lib1905":  {"args": ["http://example.com", inp_dir/"cookies1905"]},  # !!! hungs up !!!
    "lib1906":   {"args": ["http://example.com"]},
    "lib1907":   {"args": ["http://example.com"]},
    "lib1908":   {"args": ["http://example.com", log_dir/"altsvc-1908"]},
    "lib1910":   {"args": ["http://example.com"]},
    "lib1911":   {"args": ["http://example.com"]},
    "lib1912":   {"args": ["http://example.com"]},
    "lib1913.1": {"args": ["http://example.com"]},
    "lib1913.2": {"args": ["http://example.com", "yes"]},
    "lib1915":   {"args": ["http://example.com"]},
    "lib1916":   {"args": ["http://example.com"]},
    "lib1917":   {"args": ["http://example.com"]},
    "lib1918":   {"args": ["http://example.com"]},
    "lib1919":   {"args": ["http://example.com"]},
    "lib1933":   {"args": ["http://example.com"]},
    "lib1934":   {"args": ["http://example.com"]},
    "lib1935":   {"args": ["http://example.com"]},
    "lib1936":   {"args": ["http://example.com"]},
    "lib1937":   {"args": ["http://example.com"]},
    "lib1938":   {"args": ["http://example.com"]},
    "lib1939":   {"args": ["http://example.com"]},
    "lib1940.1": {"args": ["http://example.com"]},
    "lib1940.2": {"args": ["http://example.com", "http://httpstat.us"]},
    "lib1946":   {"args": ["http://example.com"]},
    "lib1945.1": {"args": ["http://example.com"]},
    "lib1945.2": {"args": ["http://example.com", "http://httpstat.us"]},
    "lib1947":   {"args": ["http://example.com", "http://httpstat.us"]},
    "lib1948":   {"args": ["http://example.com"]},
    "lib1955":   {"args": ["http://example.com"]},
    "lib1956":   {"args": ["http://example.com"]},
    "lib1957":   {"args": ["http://example.com"]},
    "lib1958":   {"args": ["http://example.com"]},
    "lib1959":   {"args": ["http://example.com"]},
    "lib1960.1": {"args": ["check",              "127.0.0.1", "80"]},
    "lib1960.2": {"args": ["http://example.com", "127.0.0.1", "80"]},
    "lib1964":   {"args": ["http://example.com"]},
    "lib1970.1": {"args": ["http://example.com"]},
    "lib1970.2": {"args": ["http://example.com", None, None]},
    #"lib1971":  {"args": ["http://example.com"]}, # !!! abnormal exit !!!
    "lib1972":   {"args": ["http://example.com"]},
    "lib1973":   {"args": ["http://example.com"]},
    "lib1974":   {"args": ["http://example.com"]},
    "lib1975":   {"args": ["http://example.com"]},
    "lib1977":   {"args": ["http://example.com"]},
    "lib1978.1": {"args": ["http://example.com"]},
    "lib1978.2": {"args": ["http://example.com", "example.com"]},
    "lib2301":   {"args": ["http://example.com"]},
    #"lib2302":  {"args": ["http://example.com"]}, # !!! abnormal exit !!!
    "lib2304":   {"args": ["http://example.com"]},
    "lib2306":   {"args": ["http://example.com", "http://httpstat.us"]},
    "lib2308":   {"args": ["http://example.com"]},
    "lib2309":   {"args": ["http://example.com", inp_dir/"netrc_file2309"]},
    "lib2402":   {"args": ["http://example.com", "127.0.0.1", "80"]}, # !!! quite often abnormal exit (select) !!!
    "lib2404":   {"args": ["http://example.com", "127.0.0.1", "80"]}, # !!! quite often abnormal exit (select) !!!
    "lib2405":   {"args": ["http://example.com"]},
    #"lib2502":  {"args": ["http://example.com", "127.0.0.1", "80", test_dir/"tests.c/certs/EdelCurlRoot-ca.cacert"]},
    "lib2700":   {"args": ["http://example.com"]},  # !!! fail 43 !!!
    "lib3010":   {"args": ["http://example.com"]},
    "lib3025":   {"args": ["http://example.com"]},
    "lib3026":   {"args": ["http://example.com"]},
    "lib3027":   {"args": ["http://example.com"]},
    "lib3100":   {"args": ["http://example.com"]},
    "lib3101":   {"args": ["http://example.com"]},
    "lib3102":   {"args": ["http://example.com"]},
    #"lib3103":  {"args": ["http://example.com"]},  # ??? often timeouts !!!
    #"lib3104":  {"args": ["http://example.com"]},  # ??? often timeouts !!!
    "lib3105":   {"args": ["http://example.com"]},
    #"lib3207":  {"args": ["http://example.com", "CA_info"]},  # ??? sometimes breaks !!!
    "lib3208":   {"args": ["http://example.com"]},
    "libauthretry":   {"args": ["http://example.com", "basic", "digest"]},
    "libntlmconnect": {"args": ["http://example.com", "testuser:testpass"]},
    "libprereq":      {"args": ["http://example.com"]},
}


class MainTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rep_path = test_dir/"_result_tests_.txt"
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
        test_mod = __import__(test_name.partition(".")[0],
                              {define: 1 for define in defs})
        for define in defs: setattr(test_mod, define, 1)
        try:
            res = test_mod.test(*tests[test_name]["args"])
        finally:
            for define in defs: delattr(test_mod, define)
        print(f"Test: {test_name}:",
              "OK" if res in exits else f"ERROR: {res}",
              file=self.rep)
        self.rep.flush()

TestCase = MainTestCase

unittest_name = lambda name: "test_" + name.replace(".", "_")

for test_name in tests:
    setattr(TestCase, unittest_name(test_name),
            lambda self, _test_name=test_name: self._test(_test_name))


if __name__.rpartition(".")[-1] == "__main__":
    main_test = TestCase()
    TestCase.setUpClass()
    for test_name in tests:
        getattr(TestCase, unittest_name(test_name))(main_test)
    TestCase.tearDownClass()
    sys.stderr.flush()
    sys.stdout.flush()
    print("\nFINISH all tests")
