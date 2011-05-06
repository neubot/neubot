#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Regression tests for neubot/config.py
#

import unittest
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.log import LOG
from neubot import config

class TestStringToKv(unittest.TestCase):
    def runTest(self):
        """Check string_to_kv behavior"""
        self.assertEquals(config.string_to_kv("    "), ())
        self.assertEquals(config.string_to_kv("# a"), ())
        self.assertEquals(config.string_to_kv("\r\n"), ())
        self.assertEquals(config.string_to_kv("foo"), ("foo", "True"))
        self.assertEquals(config.string_to_kv("foo=bar"), ("foo", "bar"))

class TestKvToString(unittest.TestCase):
    def runTest(self):
        """Check kv_to_string behavior"""
        self.assertEquals(config.kv_to_string(("a", "b")), "a=b\n")
        self.assertEquals(config.kv_to_string((3, 7)), "3=7\n")
        self.assertEquals(config.kv_to_string(("èèè", "a")), "èèè=a\n")
        self.assertEquals(config.kv_to_string((3, 7.333)), "3=7.333\n")

class TestConfigDict(unittest.TestCase):
    def testBasics(self):
        """Test some basic properties of ConfigDict"""
        d = config.ConfigDict()
        self.assertTrue(isinstance(d, dict))
        self.assertTrue(hasattr(d, "__setitem__"))
        self.assertTrue(hasattr(d, "update"))

    def testAssignment(self):
        """Make sure all ways to assign to ConfigDict are equivalent"""

        d1 = config.ConfigDict()
        for key,value in [("a", 1), ("b", 2), ("c", 3)]:
            d1[key] = value

        d2 = config.ConfigDict({"a": 1, "b": 2, "c": 3})

        d3 = config.ConfigDict()
        d3.update([("a", 1), ("b", 2), ("c", 3)])

        d4 = config.ConfigDict()
        d4.update(a=1, b=2, c=3)

        self.assertTrue(d1 == d2 == d3 == d4)

class TestCONFIG(unittest.TestCase):
    def runTest(self):
        """Check CONFIG global object behavior"""
        config.CONFIG.register_defaults({
            "default_value": "default",
            "from_database": False,
            "from_cmdline": False,
            "from_environ": False,
        })

        self.assertEquals(config.CONFIG.get("XO", 7), 7)
        self.assertFalse(config.CONFIG.get("from_database", True))

if __name__ == "__main__":
    unittest.main()
