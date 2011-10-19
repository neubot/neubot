# neubot/utils/version.py

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
  This module contains class methods to switch from version number's
  *canonical* representation to *numeric* representation and viceversa.
  It also contains a method to compare two version numbers in canonical
  representation.

  A version number in canonical representation is a string and follows the
  standard numbering schema MAJOR.MINOR[.PATCH][-rcRCNUM].  MAJOR must
  be a positive integer, while MINOR, PATCH and RCNUM must be between 0
  and 999.  This is to allow for numeric representation.

  A version number in numeric representation is the string representation
  of a float.  It must have nine digits after the radix point. For example,
  0.037001003 is the numeric representation of 0.37.1-rc3.

  When RCNUM value is 999 it means that the target release is not a
  release candidate but a stable version.  I.e. 0.37.1 is equivalent
  to 0.37.1-rc999 and viceversa.

  The general idea is that of using the canonical representation to label
  new versions to avoid user confusion.  We will use the numeric representation
  internally, for example in the results database.  The advantage, in this
  case, is that the version number can be treated as a float by statistical
  packages.  So it is possible to write rules and conditions based on the
  version number in a simple way.
"""

import decimal
import sys
import re

# Canonical representation
CANONICAL_REPR = "^([0-9]+)\.([0-9]+)(\.([0-9]+))?(-rc([0-9]+))?$"

# Numeric representation
NUMERIC_REPR = "^([0-9]+)\.([0-9]{3,3})([0-9]{3,3})([0-9]{3,3})$"

class LibVersion(object):

    """
     This class contains class methods to switch from canonical
     representation to numeric representation and viceversa.  It also
     contains a method to compare two version numbers in canonical
     representation.
    """

    @classmethod
    def _check(cls, major, minor, patch, rcnum):

        """
        Make sure that version number components are integer numbers in
        the expected range.  The @major number must be positive or zero.
        @minor, @patch and @rcnum must be between 0 and 999 included.

        Raises ValueError in case of failure.
        """

        if major < 0:
            raise ValueError("LibVersion: MAJOR is negative")

        if minor < 0 or minor > 999:
            raise ValueError("LibVersion: MINOR out of range(1000)")

        if patch < 0 or patch > 999:
            raise ValueError("LibVersion: PATCH out of range(1000)")

        if rcnum < 0 or rcnum > 999:
            raise ValueError("LibVersion: RCNUM out of range(1000)")

    @classmethod
    def to_numeric(cls, string):

        """
        Convert version number from canonical representation to
        numeric representation.

        Raises ValueError in case of failure.
        """

        string = string.strip()

        match = re.match(CANONICAL_REPR, string)
        if not match:
            raise ValueError("LibVersion: Invalid canonical representation")

        major = int(match.group(1))
        minor = int(match.group(2))

        if match.group(4):
            patch = int(match.group(4))
        else:
            patch = 0

        if match.group(6):
            rcnum = int(match.group(6))
        else:
            rcnum = 999

        cls._check(major, minor, patch, rcnum)

        return "%d.%03d%03d%03d" % (major, minor, patch, rcnum)

    @classmethod
    def to_canonical(cls, string):

        """
        Convert version number from numeric representation to
        canonical representation.

        Raises ValueError in case of failure.
        """

        string = string.strip()

        match = re.match(NUMERIC_REPR, string)
        if not match:
            raise ValueError("LibVersion: Invalid numeric representation")

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        rcnum = int(match.group(4))

        vector = [str(major), ".", str(minor)]
        if patch:
            vector.append(".")
            vector.append(str(patch))
        if rcnum < 999:
            vector.append("-rc")
            vector.append(str(rcnum))

        return "".join(vector)

    @classmethod
    def compare(cls, left, right):

        """
        Returns a negative value if the @left version number is
        smaller than the @right one; zero if they are equal; and
        a positive value if @left is bigger.

        Raises ValueError if one of @left or @right is not in
        the expected canonical form.
        """

        #
        # Way better to use Decimal than float here: we don't need
        # to wonder about all the floating point oddities.
        #

        return (decimal.Decimal(cls.to_numeric(left)) -
               decimal.Decimal(cls.to_numeric(right)))

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        print(LibVersion.to_numeric(sys.argv[1]))
    else:
        print(LibVersion.to_numeric('0.4.3-rc2'))
