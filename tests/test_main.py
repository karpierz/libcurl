# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

import unittest
import threading
import sys, pathlib
test_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(test_dir/"libtest"))

import libcurl

inp_dir = test_dir/"inp_dir"
out_dir = test_dir/"out_dir"
log_dir = test_dir/"log_dir"

tests = {
    "lib500": ["http://example.com", out_dir/"lib500.txt"],
    "lib501": ["http://example.com"],
    "lib502": ["http://example.com"],
    "lib503": ["http://example.com"],
    "lib504": ["http://example.com"],
    "lib505": ["http://example.com", inp_dir/"uploadthis.txt"],
    "lib506": ["http://example.com", inp_dir/"cookie_jar506"],
    "lib507": ["http://example.com"],
    "lib508": ["http://example.com"],
    "lib509": ["http://example.com"],
    "lib510": ["http://example.com"],
    "lib511": ["http://example.com"],
    "lib512": ["http://example.com"],
    "lib513": ["http://example.com"],
    "lib514": ["http://example.com"],
    "lib515": ["http://example.com"],
    "lib516": ["http://example.com"],
    "lib517": ["http://example.com"],
    "lib518": ["http://example.com"],
    "lib519": ["http://example.com"],
    "lib520": ["http://example.com"],
    "lib521": ["http://example.com", "80"],
    "lib523": ["http://example.com", "xxx:yyy"],
    "lib524": ["http://example.com"],
    "lib525": ["http://example.com", inp_dir/"uploadthis.txt"],
    "lib526": ["http://example.com"],
    #select_test_"lib530_nok": ["http://example.com"],
    "lib533": ["http://example.com", "http://httpstat.us"],
    "lib536": ["http://example.com", "http://example.com", "example.com"],
    "lib537": ["http://example.com"],
    "lib539": ["http://example.com", "http://example.com/0001"],
    "lib540": ["http://example.com", "http://httpstat.us"],
    "lib541": ["http://example.com", inp_dir/"uploadthis.txt"],
    "lib542": ["http://example.com"],
    "lib543": ["http://example.com"],
    "lib544": ["http://example.com"],
    "lib547": ["http://example.com"],
    "lib549": ["http://example.com"],
    "lib552": ["http://example.com"],
    "lib553": ["http://example.com"],
    "lib554": ["http://example.com"],
    "lib555": ["http://example.com"],
    "lib556": ["http://example.com"],
    "lib557": ["http://example.com"],
    "lib558": ["http://example.com"],
    "lib559": ["http://example.com"],
    "lib560": ["https://example.com"],
    "lib562": ["http://example.com", "80"],
    "lib564": ["http://example.com"],
    "lib566": ["http://example.com", out_dir/"lib566.txt"],
    "lib567": ["http://example.com"],
    "lib568": ["http://example.com", inp_dir/"sdpf_file568"],
    "lib569": ["http://example.com", out_dir/"sid_file569"],
    "lib570": ["http://example.com"],
    #"lib571": ["http://example.com", out_dir/"lib571.txt"],  # !!! hungs up !!!
    "lib572": ["http://example.com", inp_dir/"params_file572"],
    "lib573": ["http://example.com"],
    "lib574": ["http://example.com"],
    "lib575": ["http://example.com"],
    "lib576": ["http://example.com"],
    "lib578": ["http://example.com", out_dir/"lib578.txt"],
    "lib579": ["http://example.com", out_dir/"lib579.txt"],
    #select_test_"lib582_nok": ["http://example.com", inp_dir/"uploadthis.txt"],
    "lib583": ["http://example.com", None, None],  # "curl_client_key.pub", "curl_client_key"
    "lib586": ["http://example.com"],
    "lib589": ["http://example.com"],
    "lib590": ["http://example.com"],
    "lib591": ["http://example.com", inp_dir/"uploadthis.txt", "2"],
    "lib597": ["http://example.com"],
    "lib598": ["http://example.com"],
    "lib599": ["http://example.com", out_dir/"lib599.txt"],
    "lib643": ["http://example.com"],
    "lib650": ["http://example.com", inp_dir/"uploadthis.txt"],
    "lib651": ["http://example.com"],
    "lib652": ["http://example.com"],
    "lib653": ["http://example.com"],
    "lib654": ["http://example.com", inp_dir/"mime_file654"],
    "lib655": ["http://example.com"],
    "lib658": ["http://example.com"],
    "lib659": ["http://example.com"],
    #"lib661": ["http://example.com"],  # !!! hungs up !!!
    "lib666": ["http://example.com"],
    "lib667": ["http://example.com"],
    "lib668": ["http://example.com", inp_dir/"mime_file668"],
    "lib670": ["http://example.com"],
    "lib674": ["http://example.com"],
    "lib676": ["http://example.com", inp_dir/"cookies676"],
    "lib677": ["http://example.com"],
    "lib678": ["http://example.com"],
    "lib694": ["http://example.com", "http://example.com"],
    "lib695": ["http://example.com"],
    #"lib1156": ["http://example.com"],  # !!! hungs up !!!
    "lib1301": ["http://example.com"],
    "lib1485": ["http://example.com"],
    "lib1500": ["http://example.com"],
    "lib1501": ["http://example.com"],
    "lib1502": ["http://example.com", "127.0.0.1", "80"],
    "lib1506": ["http://example.com", "127.0.0.1", "80"],
    "lib1507": ["http://example.com"],
    "lib1508": ["http://example.com"],
    "lib1509": ["http://example.com"],
    "lib1510": ["http://example.com", "127.0.0.1", "80"],
    "lib1511": ["http://example.com"],
    "lib1512": ["http://example.com", "127.0.0.1", "80"],
    "lib1513": ["http://example.com"],
    "lib1514": ["http://example.com"],
    "lib1515": ["http://example.com", "127.0.0.1", "80"],
    "lib1517": ["http://example.com"],
    "lib1518": ["http://example.com"],
    "lib1520": ["http://example.com"],
    "lib1522": ["http://example.com"],
    "lib1523": ["http://example.com"],
    "lib1525": ["http://example.com"],
    "lib1526": ["http://example.com"],
    "lib1527": ["http://example.com"],
    "lib1528": ["http://example.com"],
    "lib1529": ["http://example.com"],
    "lib1530": ["http://example.com"],
    "lib1531": ["http://example.com"],
    "lib1532": ["http://example.com"],
    "lib1533": ["http://example.com"],
    "lib1534": ["http://example.com"],
    "lib1535": ["http://example.com"],
    "lib1536": ["http://example.com"],
    "lib1537": ["http://example.com"],
    "lib1538": ["http://example.com"],
    "lib1540": ["http://example.com"],
    "lib1541": ["http://example.com"],
    "lib1542": ["http://example.com"],
    "lib1545": ["http://example.com"],
    "lib1550": ["http://example.com"],
    "lib1551": ["http://example.com"],
    "lib1552": ["http://example.com"],
    "lib1553": ["http://example.com"],
    "lib1554": ["http://example.com"],
    "lib1555": ["http://example.com"],
    "lib1556": ["http://example.com"],
    "lib1557": ["http://example.com"],
    "lib1558": ["http://example.com"],
    "lib1559": ["http://example.com"],
    "lib1560": ["http://example.com"],
    "lib1564": ["http://example.com"],
    "lib1565": ["http://example.com"],
    "lib1567": ["http://example.com"],
    "lib1568": ["http://example.com", "80"],
    "lib1569": ["http://example.com", "http://httpstat.us"],
    "lib1591": ["http://example.com"],
    "lib1592": ["http://example.com"],
    "lib1593": ["http://example.com"],
    "lib1594": ["http://example.com"],
    "lib1597": ["http://example.com"],
    "lib1598": ["http://example.com"],
    "lib1662": ["http://example.com"],
    "lib1900": ["http://example.com", log_dir/"first-hsts.txt", log_dir/"second-hsts.txt"],
    #"lib1901": ["http://example.com"], # !!! abnormal exit !!!
    "lib1903": ["http://example.com", inp_dir/"cookies1903", inp_dir/"cookie_jar1903"],
    #"lib1905": ["http://example.com", inp_dir/"cookies1905"],  # !!! hungs up !!!
    "lib1906": ["http://example.com"],
    "lib1907": ["http://example.com"],
    "lib1908": ["http://example.com", log_dir/"altsvc-1908"],
    "lib1910": ["http://example.com"],
    "lib1911": ["http://example.com"],
    "lib1912": ["http://example.com"],
    "lib1913": ["http://example.com"],
    "lib1915": ["http://example.com"],
    "lib1916": ["http://example.com"],
    "lib1918": ["http://example.com"],
    "lib1919": ["http://example.com"],
    "lib1933": ["http://example.com"],
    "lib1934": ["http://example.com"],
    "lib1935": ["http://example.com"],
    "lib1936": ["http://example.com"],
    "lib1937": ["http://example.com"],
    "lib1938": ["http://example.com"],
    "lib1939": ["http://example.com"],
    "lib1940": ["http://example.com"],
    "lib1945": ["http://example.com"],
    "lib1947": ["http://example.com", "http://httpstat.us"],
    "lib1948": ["http://example.com"],
    "lib1955": ["http://example.com"],
    "lib1956": ["http://example.com"],
    "lib1957": ["http://example.com"],
    "lib1958": ["http://example.com"],
    "lib1959": ["http://example.com"],
    "lib1960": ["http://example.com", "127.0.0.1", "80"],
    "lib1964": ["http://example.com"],
    "lib1970": ["http://example.com"],
    "lib1971": ["http://example.com"],
    "lib1972": ["http://example.com"],
    "lib1973": ["http://example.com"],
    "lib1974": ["http://example.com"],
    "lib1975": ["http://example.com"],
    "lib1977": ["http://example.com"],
    "lib2301": ["http://example.com"],
    "lib2302": ["http://example.com"],
    "lib2304": ["http://example.com"],
    "lib2305": ["http://example.com", out_dir/"lib2305.txt"],
    "lib2306": ["http://example.com", "http://httpstat.us"],
    "lib2308": ["http://example.com"],
    "lib2309": ["http://example.com", inp_dir/"netrc_file2309"],
    "lib2310": ["http://example.com"],
    "lib2402": ["http://example.com", "127.0.0.1", "80"],
    "lib2404": ["http://example.com", "127.0.0.1", "80"],
    "lib2405": ["http://example.com"],
    "lib2502": ["http://example.com", "127.0.0.1", "80"],
    "lib3010": ["http://example.com"],
    "lib3025": ["http://example.com"],
    "lib3026": ["http://example.com"],
    "lib3027": ["http://example.com"],
    "lib3100": ["http://example.com"],
    "lib3101": ["http://example.com"],
    "lib3102": ["http://example.com"],
    #"lib3103": ["http://example.com"],  # ??? often timeouts !!!
    #"lib3104": ["http://example.com"],  # ??? often timeouts !!!
    "lib3105": ["http://example.com"],
    #"lib3207": ["http://example.com", "CA_info"],  # ??? sometimes breaks !!!
    "lib3208": ["http://example.com"],
    "libprereq":      ["http://example.com"],
    "libauthretry":   ["http://example.com", "basic", "digest"],
    "libntlmconnect": ["http://example.com", "testuser:testpass"],
}


class MainTestCase:#(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rep = (test_dir/"_results_.txt").open("wt")
        cls.lock = threading.Lock()

    @classmethod
    def tearDownClass(cls):
        cls.rep.close()

    def setUp(self):
        self.lock.acquire()

    def tearDown(self):
        self.lock.release()

    def _test(self, test_name):
        test_mod = __import__(test_name)
        res = test_mod.test(*tests[test_name])
        print("Test: {}:".format(test_name), (("ERROR: %d" % res) if res else "OK"),
              file=self.rep)
        self.rep.flush()


for test_name in tests:
    setattr(MainTestCase, "test_" + test_name,
            lambda self, _test_name=test_name: self._test(_test_name))


if __name__.rpartition(".")[-1] == "__main__":
    main_test = MainTestCase()
    MainTestCase.setUpClass()
    for test_name in tests:
        getattr(MainTestCase, "test_" + test_name)(main_test)
    MainTestCase.tearDownClass()
    sys.stderr.flush()
    sys.stdout.flush()
    print("\nFINISH all tests")
