#!/usr/bin/env python

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

import unittest
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import utils

class TestVersioncmp(unittest.TestCase):
    def runTest(self):
        """Test the behavior of neubot.utils.versioncmp()"""
        self.assertTrue(utils.versioncmp("7.5.3", "7.5.3") == 0)
        self.assertTrue(utils.versioncmp("7", "7.5.3") < 0)
        self.assertTrue(utils.versioncmp("8", "7.5.3") > 0)
        self.assertTrue(utils.versioncmp("8.0.0.0", "8.0.0.1") < 0)
        self.assertTrue(utils.versioncmp("8.0.0-rc3", "8.0.0-rc4") < 0)
        self.assertTrue(utils.versioncmp("8.0.0-rc3", "8.0.0") < 0)
        self.assertRaises(ValueError, utils.versioncmp, "8-rc1-rc2", "8.3")
        self.assertRaises(ValueError, utils.versioncmp, "8.xo", "8.3")
        self.assertRaises(ValueError, utils.versioncmp, " ", "8.3")
        self.assertRaises(RuntimeError, utils.versioncmp,
         "8.3-rc%d" % sys.maxint, "8.3")
        self.assertRaises(RuntimeError, utils.versioncmp,
         "8.3-rc%d" % (sys.maxint + 1), "8.3")
        self.assertRaises(RuntimeError, utils.versioncmp, "8-rc-1", "8")
        self.assertRaises(RuntimeError, utils.versioncmp, "8.-1", "8")

if __name__ == "__main__":
    unittest.main()
