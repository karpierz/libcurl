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

import sys
import ctypes as ct

import libcurl as lcurl
from curl_test import *  # noqa


def print_err(name: bytes, exp: str):
    print("Type mismatch for CURLOPT_%s (expected %s)" %
          (name.decode("utf-8"), exp), file=sys.stderr)


@curl_test_decorator
def test(URL: str) -> lcurl.CURLcode:

  # Only test if GCC typechecking is available

  error: int = 0

  # if defined("CURLINC_TYPECHECK_GCC_H"):
  o: ct.POINTER(lcurl.easyoption) = lcurl.easy_option_next(None)
  while o:
      opt: lcurl.easyoption = o.contents
      # CURL_IGNORE_DEPRECATION(
      # Test for mismatch OR missing typecheck macros
      if lcurl.check_long_option(opt.id) != (opt.type == lcurl.CURLOT_LONG or
                                           opt.type == lcurl.CURLOT_VALUES):
          print_err(opt.name, "CURLOT_LONG or CURLOT_VALUES")
          error += 1
      if lcurl.check_off_t_option(opt.id) != (opt.type == lcurl.CURLOT_OFF_T):
          print_err(opt.name, "CURLOT_OFF_T")
          error += 1
      if lcurl.check_string_option(opt.id) != (opt.type == lcurl.CURLOT_STRING):
          print_err(opt.name, "CURLOT_STRING")
          error += 1
      if lcurl.check_slist_option(opt.id) != (opt.type == lcurl.CURLOT_SLIST):
          print_err(opt.name, "CURLOT_SLIST")
          error += 1
      if lcurl.check_cb_data_option(opt.id) != (opt.type == lcurl.CURLOT_CBPTR):
          print_err(opt.name, "CURLOT_CBPTR")
          error += 1
      # From here: only test that the type matches if macro is known
      if lcurl.check_write_cb_option(opt.id) and (opt.type != lcurl.CURLOT_FUNCTION):
          print_err(opt.name, "CURLOT_FUNCTION")
          error += 1
      if lcurl.check_conv_cb_option(opt.id) and (opt.type != lcurl.CURLOT_FUNCTION):
          print_err(opt.name, "CURLOT_FUNCTION")
          error += 1
      if lcurl.check_postfields_option(opt.id) and (opt.type != lcurl.CURLOT_OBJECT):
          print_err(opt.name, "CURLOT_OBJECT")
          error += 1
      # Todo: no gcc typecheck for lcurl.CURLOPTTYPE_BLOB types?
      # )

      o = lcurl.easy_option_next(o)
  # endif

  return lcurl.CURLE_OK if error == 0 else TEST_ERR_FAILURE
