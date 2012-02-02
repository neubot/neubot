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

''' Regression tests for neubot/config.py '''

import unittest
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import config

#
# pylint: disable=R0904
#

class TestStringToKv(unittest.TestCase):

    ''' Test string_to_kv behavior '''

    def test_string_to_kv(self):
        """Check string_to_kv behavior"""
        self.assertEquals(config.string_to_kv("    "), ())
        self.assertEquals(config.string_to_kv("# a"), ())
        self.assertEquals(config.string_to_kv("\r\n"), ())
        self.assertEquals(config.string_to_kv("foo"), ("foo", "True"))
        self.assertEquals(config.string_to_kv("foo=bar"), ("foo", "bar"))

class TestKvToString(unittest.TestCase):

    ''' Test kv_to_string behavior '''

    def test_kv_to_string(self):
        """Check kv_to_string behavior"""
        self.assertEquals(config.kv_to_string(("a", "b")), "a=b\n")
        self.assertEquals(config.kv_to_string((3, 7)), "3=7\n")
        self.assertEquals(config.kv_to_string(("èèè",
                             "a")), "èèè=a\n")
        self.assertEquals(config.kv_to_string((3, 7.333)), "3=7.333\n")

class TestConfigDict(unittest.TestCase):

    ''' Tests ConfigDict behavior '''

    def test_basics(self):
        """Test some basic properties of ConfigDict"""
        dictionary = config.ConfigDict()
        self.assertTrue(isinstance(dictionary, dict))
        self.assertTrue(hasattr(dictionary, "__setitem__"))
        self.assertTrue(hasattr(dictionary, "update"))

    def test_assignment(self):
        """Make sure all ways to assign to ConfigDict are equivalent"""

        dict1 = config.ConfigDict()
        for key, value in [("a", 1), ("b", 2), ("c", 3)]:
            dict1[key] = value

        dict2 = config.ConfigDict({"a": 1, "b": 2, "c": 3})

        dict3 = config.ConfigDict()
        dict3.update([("a", 1), ("b", 2), ("c", 3)])

        dict4 = config.ConfigDict()
        dict4.update(a=1, b=2, c=3)

        self.assertTrue(dict1 == dict2 == dict3 == dict4)

class TestCONFIG(unittest.TestCase):

    ''' Test the behavior of the CONFIG global object '''

    def test_config_global_object(self):
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
