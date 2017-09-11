#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Signature spoofing."""

import sys

__author__ = "ale5000"
__copyright__ = "Copyright (C) 2016-2017, ale5000"
__license__ = "GPLv3"


class Patch(sys.BasePatch):
    """Signature spoofing patch."""

    name = "Signature spoofing"
    version = "0.0.1"
    _patch_ver = 0

    def _initialize(self):
        pass

    def _set_files_list(self):
        self.files.append(["/system/framework", "framework.jar"])
