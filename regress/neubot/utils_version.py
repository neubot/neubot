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

"""
 Unit test for neubot.utils.version.py
"""

import unittest
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.utils_version import LibVersion

class TestLibVersion(unittest.TestCase):

    """
     Tests the behavior of LibVersion
    """

    def test_compare(self):

        """
         Make sure that LibVersion.compare() behaves ad advertised
         in comparing different version numbers.
        """

        self.assertTrue(LibVersion.compare("7.5.3", "7.5.3") == 0)
        self.assertTrue(LibVersion.compare("7.0", "7.5.3") < 0)
        self.assertTrue(LibVersion.compare("8.0", "7.5.3") > 0)
        self.assertTrue(LibVersion.compare("8.0.0", "8.0.1") < 0)
        self.assertTrue(LibVersion.compare("8.0.0-rc3", "8.0.0-rc4") < 0)
        self.assertTrue(LibVersion.compare("8.0.0-rc3", "8.0.0") < 0)

    def test_to_numeric_failures(self):

        """
         Make sure that LibVersion.to_numeric() raises ValueError when
         the input is not a valid and recognized version number in canonical
         representation.
        """

        #
        # TODO We need to write more tests because the current set
        # of tests does not cover all the cases.
        #

        # Minor number must always be there
        self.assertRaises(ValueError, LibVersion.to_numeric, "8")

        # Minor number must indeed be a number
        self.assertRaises(ValueError, LibVersion.to_numeric, "8.xo")

        # Only one -rc is allowed
        self.assertRaises(ValueError, LibVersion.to_numeric, "8-rc1-rc2")

        # We need something to chew
        self.assertRaises(ValueError, LibVersion.to_numeric, " ")

        # RCNUM is limited to 999
        self.assertRaises(ValueError, LibVersion.to_numeric, "8.3-rc1000")

        # RCNUM must be positive
        self.assertRaises(ValueError, LibVersion.to_numeric, "8-rc-1")

        # MINOR must be positive
        self.assertRaises(ValueError, LibVersion.to_numeric, "8.-1")

    def test_to_canonical_failures(self):

        """
         Make sure that LibVersion.to_canonical() raises ValueError when
         the input is not a valid and recognized version number in numeric
         representation.
        """

        #
        # TODO We need to write more tests because the current set
        # of tests does not cover all the cases.
        #

        # We need nine digits after the radix point
        self.assertRaises(ValueError, LibVersion.to_canonical, "1.000000")

    def test_double_conversion(self):

        """
         Convert from canonical to numeric and then again to canonical
         (and viceversa) to make sure that we get what is expected.
        """

        # canonical -> numeric -> canonical
        self.assertEquals(LibVersion.to_canonical(
          LibVersion.to_numeric("133.35.71-rc19")),
          "133.35.71-rc19")

        # Same as above but check for -rc999
        self.assertEquals(LibVersion.to_canonical(
          LibVersion.to_numeric("133.35.71-rc999")),
          "133.35.71")

        # numeric -> canonical -> numeric
        self.assertEquals(LibVersion.to_numeric(
          LibVersion.to_canonical("133.035071019")),
          "133.035071019")

if __name__ == "__main__":
    unittest.main()
