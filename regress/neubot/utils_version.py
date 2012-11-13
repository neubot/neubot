#!/usr/bin/env python

#
# Copyright (c) 2011-2012
#     Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#     and Simone Basso <bassosimone@gmail.com>
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
 Unit test for neubot/utils_version.py
"""

import unittest
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import utils_version

class TestLibVersion(unittest.TestCase):

    """
     Tests the behavior of LibVersion
    """

    def test_compare(self):

        """
         Make sure that LibVersion.compare() behaves ad advertised
         in comparing different version numbers.
        """

        self.assertTrue(utils_version.compare("7.5.3.0", "7.5.3.0") == 0)
        self.assertTrue(utils_version.compare("7.0.0.0", "7.5.3.0") < 0)
        self.assertTrue(utils_version.compare("8.0.0.0", "7.5.3.0") > 0)
        self.assertTrue(utils_version.compare("8.0.0.0", "8.0.1.0") < 0)

        # Legacy
        self.assertTrue(utils_version.compare("0.0.0-rc3", "0.0.0-rc4") < 0)
        self.assertTrue(utils_version.compare("0.0.0-rc3", "0.0.0") < 0)

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

        # All numbers must always be there
        self.assertRaises(ValueError, utils_version.to_numeric, "8")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0.0")

        # All numbers must acutally be... numbers
        self.assertRaises(ValueError, utils_version.to_numeric, "8.xo.0.0")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0.xo.0")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0.0.xo")

        # Only one -rc is allowed
        self.assertRaises(ValueError, utils_version.to_numeric, "0.0.0-rc1-rc2")

        # We need something to chew
        self.assertRaises(ValueError, utils_version.to_numeric, " ")

        # MINOR, PATCH, RCNUM are limited to 999
        self.assertRaises(ValueError, utils_version.to_numeric, "8.1000.0.0")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0.1000.0")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0.0.1000")

        # RCNUM must be positive (legacy)
        self.assertRaises(ValueError, utils_version.to_numeric, "0-rc-1")

        # MINOR, PATCH, RCNUM must be positive
        self.assertRaises(ValueError, utils_version.to_numeric, "8.-1.0.0")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0.-1.0")
        self.assertRaises(ValueError, utils_version.to_numeric, "8.0.0.-1")

        # The "-rc" notation fails after 0.4.14
        self.assertRaises(ValueError, utils_version.to_numeric, "0.4.15-rc1")

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
        self.assertRaises(ValueError, utils_version.to_canonical, "1.000000")

    def test_double_conversion(self):

        """
         Convert from canonical to numeric and then again to canonical
         (and viceversa) to make sure that we get what is expected.
        """

        # canonical -> numeric -> canonical
        self.assertEquals(utils_version.to_canonical(
          utils_version.to_numeric("133.35.71.19")),
          "133.35.71.19")

        # Same as above but check for -rc999 (legacy check)
        self.assertEquals(utils_version.to_canonical(
          utils_version.to_numeric("0.3.71-rc999")),
          "0.3.71")

        # numeric -> canonical -> numeric
        self.assertEquals(utils_version.to_numeric(
          utils_version.to_canonical("133.035071019")),
          "133.035071019")

    def test_boundary(self):

        """
         Test behavior around 0.4.14.999 boundary
        """

        self.assertEquals(utils_version.to_canonical('0.004014998'),
          '0.4.14-rc998')
        self.assertEquals(utils_version.to_canonical('0.004014999'),
          '0.4.14')
        self.assertEquals(utils_version.to_canonical('0.004015000'),
          '0.4.15.0')
        self.assertEquals(utils_version.to_canonical('0.004015999'),
          '0.4.15.999')

        self.assertEquals(utils_version.to_numeric('0.4.14-rc998'),
          '0.004014998')
        self.assertEquals(utils_version.to_numeric('0.4.14'),
          '0.004014999')
        self.assertEquals(utils_version.to_numeric('0.4.15.0'),
          '0.004015000')
        self.assertEquals(utils_version.to_numeric('0.4.15.999'),
          '0.004015999')

if __name__ == "__main__":
    unittest.main()
