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

from dataclasses import dataclass
import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa


@dataclass
class dcheck:
    input:  str
    output: lcurl.time_t


dates = [
    dcheck("Sun, 06 Nov 1994 08:49:37 GMT", lcurl.time_t(784111777)),
    dcheck("Sunday, 06-Nov-94 08:49:37 GMT", lcurl.time_t(784111777)),
    dcheck("Sun Nov  6 08:49:37 1994", lcurl.time_t(784111777)),
    dcheck("Sun Nov  6 8:49:37 1994", lcurl.time_t(784111777)),
    dcheck("Sun Nov  6 8:9:37 1994", lcurl.time_t(784109377)),
    dcheck("Sun Nov  6 008:09:37 1994", lcurl.time_t(-1)),
    dcheck("Nov      Sun      6 8:9:7 1994", lcurl.time_t(784109347)),
    dcheck("Sun Nov  6 8:49:37 1994", lcurl.time_t(784111777)),
    dcheck("Sun Nov  6 8:9:37 1994", lcurl.time_t(784109377)),
    dcheck("Sun Nov  6 008:09:37 1994", lcurl.time_t(-1)),
    dcheck("Nov      Sun      6 8:9:7 1994", lcurl.time_t(784109347)),
    dcheck("06 Nov 1994 08:49:37 GMT", lcurl.time_t(784111777)),
    dcheck("06-Nov-94 08:49:37 GMT", lcurl.time_t(784111777)),
    dcheck("Nov  6 08:49:37 1994", lcurl.time_t(784111777)),
    dcheck("06 Nov 1994 08:49:37", lcurl.time_t(784111777)),
    dcheck("06-Nov-94 08:49:37", lcurl.time_t(784111777)),
    dcheck("1994 Nov 6 08:49:37", lcurl.time_t(784111777)),
    dcheck("GMT 08:49:37 06-Nov-94 Sunday", lcurl.time_t(784111777)),
    dcheck("94 6 Nov 08:49:37", lcurl.time_t(784111777)),
    dcheck("1994 Nov 6", lcurl.time_t(784080000)),
    dcheck("06-Nov-94", lcurl.time_t(784080000)),
    dcheck("Sun Nov 6 94", lcurl.time_t(784080000)),
    dcheck("1994.Nov.6", lcurl.time_t(784080000)),
    dcheck("Sun/Nov/6/94/GMT", lcurl.time_t(784080000)),
    dcheck("Sun, 06 Nov 1994 08:49:37 CET", lcurl.time_t(784108177)),
    dcheck("06 Nov 1994 08:49:37 EST", lcurl.time_t(784129777)),
    dcheck("Sun, 06 Nov 1994 08:49:37 UT", lcurl.time_t(784111777)),
    dcheck("Sun, 12 Sep 2004 15:05:58 -0700", lcurl.time_t(1095026758)),
    dcheck("Sat, 11 Sep 2004 21:32:11 +0200", lcurl.time_t(1094931131)),
    dcheck("20040912 15:05:58 -0700", lcurl.time_t(1095026758)),
    dcheck("20040911 +0200", lcurl.time_t(1094853600)),
    dcheck("Thu, 01-Jan-1970 00:59:59 GMT", lcurl.time_t(3599)),
    dcheck("Thu, 01-Jan-1970 01:00:00 GMT", lcurl.time_t(3600)),
    dcheck("Sat, 15-Apr-17 21:01:22 GMT", lcurl.time_t(1492290082)),
    dcheck("Thu, 19-Apr-2007 16:00:00 GMT", lcurl.time_t(1176998400)),
    dcheck("Wed, 25 Apr 2007 21:02:13 GMT", lcurl.time_t(1177534933)),
    dcheck("Thu, 19/Apr\\2007 16:00:00 GMT", lcurl.time_t(1176998400)),
    dcheck("Fri, 1 Jan 2010 01:01:50 GMT", lcurl.time_t(1262307710)),
    dcheck("Wednesday, 1-Jan-2003 00:00:00 GMT", lcurl.time_t(1041379200)),
    dcheck(", 1-Jan-2003 00:00:00 GMT", lcurl.time_t(1041379200)),
    dcheck("1-Jan-2003 00:00:00 GMT", lcurl.time_t(1041379200)),
    dcheck("1-Jan-2003 00:00:00 GMT", lcurl.time_t(1041379200)),
    dcheck("Wed,18-Apr-07 22:50:12 GMT", lcurl.time_t(1176936612)),
    dcheck("WillyWonka  , 18-Apr-07 22:50:12 GMT", lcurl.time_t(-1)),
    dcheck("WillyWonka  , 18-Apr-07 22:50:12", lcurl.time_t(-1)),
    dcheck("WillyWonka  ,  18-apr-07   22:50:12", lcurl.time_t(-1)),
    dcheck("Mon, 18-Apr-1977 22:50:13 GMT", lcurl.time_t(230251813)),
    dcheck("Mon, 18-Apr-77 22:50:13 GMT", lcurl.time_t(230251813)),
    dcheck("Sat, 15-Apr-17\"21:01:22\"GMT", lcurl.time_t(1492290082)),
    dcheck("Partyday, 18- April-07 22:50:12", lcurl.time_t(-1)),
    dcheck("Partyday, 18 - Apri-07 22:50:12", lcurl.time_t(-1)),
    dcheck("Wednes, 1-Januar-2003 00:00:00 GMT", lcurl.time_t(-1)),
    dcheck("Sat, 15-Apr-17 21:01:22", lcurl.time_t(1492290082)),
    dcheck("Sat, 15-Apr-17 21:01:22 GMT-2", lcurl.time_t(1492290082)),
    dcheck("Sat, 15-Apr-17 21:01:22 GMT BLAH", lcurl.time_t(1492290082)),
    dcheck("Sat, 15-Apr-17 21:01:22 GMT-0400", lcurl.time_t(1492290082)),
    dcheck("Sat, 15-Apr-17 21:01:22 GMT-0400 (EDT)", lcurl.time_t(1492290082)),
    dcheck("Sat, 15-Apr-17 21:01:22 DST", lcurl.time_t(-1)),
    dcheck("Sat, 15-Apr-17 21:01:22 -0400", lcurl.time_t(1492304482)),
    dcheck("Sat, 15-Apr-17 21:01:22 (hello there)", lcurl.time_t(-1)),
    dcheck("Sat, 15-Apr-17 21:01:22 11:22:33", lcurl.time_t(-1)),
    dcheck("Sat, 15-Apr-17 ::00 21:01:22", lcurl.time_t(-1)),
    dcheck("Sat, 15-Apr-17 boink:z 21:01:22", lcurl.time_t(-1)),
    dcheck("Sat, 15-Apr-17 91:22:33 21:01:22", lcurl.time_t(-1)),
    dcheck("Thu Apr 18 22:50:12 2007 GMT", lcurl.time_t(1176936612)),
    dcheck("22:50:12 Thu Apr 18 2007 GMT", lcurl.time_t(1176936612)),
    dcheck("Thu 22:50:12 Apr 18 2007 GMT", lcurl.time_t(1176936612)),
    dcheck("Thu Apr 22:50:12 18 2007 GMT", lcurl.time_t(1176936612)),
    dcheck("Thu Apr 18 22:50:12 2007 GMT", lcurl.time_t(1176936612)),
    dcheck("Thu Apr 18 2007 22:50:12 GMT", lcurl.time_t(1176936612)),
    dcheck("Thu Apr 18 2007 GMT 22:50:12", lcurl.time_t(1176936612)),

    dcheck("\"Thu Apr 18 22:50:12 2007 GMT\"",  lcurl.time_t(1176936612)),
    dcheck("-\"22:50:12 Thu Apr 18 2007 GMT\"", lcurl.time_t(1176936612)),
    dcheck("*\"Thu 22:50:12 Apr 18 2007 GMT\"", lcurl.time_t(1176936612)),
    dcheck(";\"Thu Apr 22:50:12 18 2007 GMT\"", lcurl.time_t(1176936612)),
    dcheck(".\"Thu Apr 18 22:50:12 2007 GMT\"", lcurl.time_t(1176936612)),
    dcheck("\"Thu Apr 18 2007 22:50:12 GMT\"",  lcurl.time_t(1176936612)),
    dcheck("\"Thu Apr 18 2007 GMT 22:50:12\"",  lcurl.time_t(1176936612)),

    dcheck("Sat, 15-Apr-17 21:01:22 GMT", lcurl.time_t(1492290082)),
    dcheck("15-Sat, Apr-17 21:01:22 GMT", lcurl.time_t(1492290082)),
    dcheck("15-Sat, Apr 21:01:22 GMT 17", lcurl.time_t(1492290082)),
    dcheck("15-Sat, Apr 21:01:22 GMT 2017", lcurl.time_t(1492290082)),
    dcheck("15 Apr 21:01:22 2017", lcurl.time_t(1492290082)),
    dcheck("15 17 Apr 21:01:22", lcurl.time_t(1492290082)),
    dcheck("Apr 15 17 21:01:22", lcurl.time_t(1492290082)),
    dcheck("Apr 15 21:01:22 17", lcurl.time_t(1492290082)),
    dcheck("2017 April 15 21:01:22", lcurl.time_t(-1)),
    dcheck("15 April 2017 21:01:22", lcurl.time_t(-1)),
    dcheck("98 April 17 21:01:22", lcurl.time_t(-1)),
    dcheck("Thu, 012-Aug-2008 20:49:07 GMT", lcurl.time_t(1218574147)),
    dcheck("Thu, 999999999999-Aug-2007 20:49:07 GMT", lcurl.time_t(-1)),
    dcheck("Thu, 12-Aug-2007 20:61:99999999999 GMT", lcurl.time_t(-1)),
    dcheck("IAintNoDateFool", lcurl.time_t(-1)),
    dcheck("Thu Apr 18 22:50 2007 GMT", lcurl.time_t(1176936600)),
    dcheck("20110623 12:34:56", lcurl.time_t(1308832496)),
    dcheck("20110632 12:34:56", lcurl.time_t(-1)),
    dcheck("20110623 56:34:56", lcurl.time_t(-1)),
    dcheck("20111323 12:34:56", lcurl.time_t(-1)),
    dcheck("20110623 12:34:79", lcurl.time_t(-1)),
    dcheck("Wed, 31 Dec 2008 23:59:60 GMT", lcurl.time_t(1230768000)),
    dcheck("Wed, 31 Dec 2008 23:59:61 GMT", lcurl.time_t(-1)),
    dcheck("Wed, 31 Dec 2008 24:00:00 GMT", lcurl.time_t(-1)),
    dcheck("Wed, 31 Dec 2008 23:60:59 GMT", lcurl.time_t(-1)),
    dcheck("Wed, 31 Dec 2008 23:59:61 GMT", lcurl.time_t(-1)),
    dcheck("Wed, 31 Dec 2008 24:00:00 GMT", lcurl.time_t(-1)),
    dcheck("Wed, 31 Dec 2008 23:60:59 GMT", lcurl.time_t(-1)),
    dcheck("20110623 12:3", lcurl.time_t(1308830580)),
    dcheck("20110623 1:3", lcurl.time_t(1308790980)),
    dcheck("20110623 1:30", lcurl.time_t(1308792600)),
    dcheck("20110623 12:12:3", lcurl.time_t(1308831123)),
    dcheck("20110623 01:12:3", lcurl.time_t(1308791523)),
    dcheck("20110623 01:99:30", lcurl.time_t(-1)),
    dcheck("Thu, 01-Jan-1970 00:00:00 GMT", lcurl.time_t(0)),
    dcheck("Thu, 31-Dec-1969 23:59:58 GMT", lcurl.time_t(-2)),
    dcheck("Thu, 31-Dec-1969 23:59:59 GMT", lcurl.time_t(0)),  # avoids -1 !
]
if ct.sizeof(lcurl.time_t) > 4:
    dates.append(dcheck("Sun, 06 Nov 2044 08:49:37 GMT", lcurl.time_t(2362034977)))
    dates.append(dcheck("Sun, 06 Nov 3144 08:49:37 GMT", lcurl.time_t(37074617377)))
    if not defined("HAVE_TIME_T_UNSIGNED"):
        if 0:
            # causes warning on MSVC
            dates.append(dcheck("Sun, 06 Nov 1900 08:49:37 GMT", lcurl.time_t(-2182259423)))
        dates.append(dcheck("Sun, 06 Nov 1800 08:49:37 GMT", lcurl.time_t(-5337933023)))
        dates.append(dcheck("Thu, 01-Jan-1583 00:00:00 GMT", lcurl.time_t(-12212553600)))
    # endif
    dates.append(dcheck("Thu, 01-Jan-1499 00:00:00 GMT", lcurl.time_t(-1)))
else:
    dates.append(dcheck("Sun, 06 Nov 2044 08:49:37 GMT", lcurl.time_t(-1)))
if not defined("HAVE_TIME_T_UNSIGNED"):
    dates.append(dcheck("Sun, 06 Nov 1968 08:49:37 GMT", lcurl.time_t(-36342623)))
# endif


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

    error: int = 0

    for date in dates:
        out = lcurl.getdate(date.input.encode("utf-8"), None)
        if out != date.output.value:
            print("WRONGLY %s => %ld (instead of %ld)" %
                  (date.input, out, date.output.value))
            error += 1

    return lcurl.CURLE_OK if error == 0 else lcurl.TEST_ERR_FAILURE
