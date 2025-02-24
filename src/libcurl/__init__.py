# Copyright (c) 2021 Adam Karpierz
# SPDX-License-Identifier: MIT

from .__about__ import * ; del __about__  # noqa
from . import __config__ ; del __config__
from .__config__ import set_config as config

from ._curl import * ; del _curl  # noqa
