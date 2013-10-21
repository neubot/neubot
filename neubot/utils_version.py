# neubot/utils_version.py

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
  This module contains class methods to switch from version number's
  *canonical* representation to *numeric* representation and viceversa.
  It also contains a method to compare two version numbers in canonical
  representation.

  A version number in canonical representation is a string and follows the
  standard numbering schema MAJOR.MINOR.PATCH.RCNUM.  MAJOR must
  be a positive integer, while MINOR, PATCH and RCNUM must be between 0
  and 999.  This is to allow for numeric representation.

  A version number in numeric representation is the string representation
  of a float.  It must have nine digits after the radix point. For example,
  `0.037001003` is the numeric representation of `0.37.1.3`.

  The general idea is that of using the canonical representation to label
  new versions to avoid user confusion.  We will use the numeric representation
  internally, for example in the results database.  The advantage, in this
  case, is that the version number can be treated as a float by statistical
  packages.  So it is possible to write rules and conditions based on the
  version number in a simple way.
"""

import getopt
import decimal
import sys
import re

# Canonical representation
LEGACY_CANONICAL_REPR = "^([0-9]+)\.([0-9]+)(\.([0-9]+))?(-rc([0-9]+))?$"
CANONICAL_REPR = "^([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)$"

# Numeric representation
NUMERIC_REPR = "^([0-9]+)\.([0-9]{3,3})([0-9]{3,3})([0-9]{3,3})$"

def check(major, minor, patch, rcnum):

    """
    Make sure that version number components are integer numbers in
    the expected range.  The @major number must be positive or zero.
    @minor, @patch and @rcnum must be between 0 and 999 included.

    Raises ValueError in case of failure.
    """

    if major < 0:
        raise ValueError("utils_version: MAJOR is negative")

    if minor < 0 or minor > 999:
        raise ValueError("utils_version: MINOR out of range(1000)")

    if patch < 0 or patch > 999:
        raise ValueError("utils_version: PATCH out of range(1000)")

    if rcnum < 0 or rcnum > 999:
        raise ValueError("utils_version: RCNUM out of range(1000)")

def to_numeric_legacy(string):

    """
    Convert version number from canonical representation to
    numeric representation.

    Raises ValueError in case of failure.
    """

    string = string.strip()

    match = re.match(LEGACY_CANONICAL_REPR, string)
    if not match:
        raise ValueError("utils_version: Invalid canonical representation")

    major = int(match.group(1))
    minor = int(match.group(2))

    if match.group(4):
        patch = int(match.group(4))
    else:
        patch = 0

    # Last legacy release is 0.4.14
    notlegacy = ((major > 0) or (major == 0 and minor > 4) or
                 (major == 0 and minor == 4 and patch > 14))
    if notlegacy:
        raise ValueError("utils_version: Invalid canonical representation")

    if match.group(6):
        rcnum = int(match.group(6))
    else:
        rcnum = 999

    check(major, minor, patch, rcnum)

    return "%d.%03d%03d%03d" % (major, minor, patch, rcnum)

def to_numeric(string):
    ''' Convert version number from canonical representation to numeric
        representation.  Raises ValueError in case of failure. '''
    string = string.strip()
    match = re.match(CANONICAL_REPR, string)
    if not match:
        return to_numeric_legacy(string)
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    rcnum = int(match.group(4))
    check(major, minor, patch, rcnum)
    return '%d.%03d%03d%03d' % (major, minor, patch, rcnum)

def to_canonical(string):

    """
    Convert version number from numeric representation to
    canonical representation.

    Raises ValueError in case of failure.
    """

    string = string.strip()

    match = re.match(NUMERIC_REPR, string)
    if not match:
        raise ValueError("utils_version: Invalid numeric representation")

    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    rcnum = int(match.group(4))

    # Last legacy release is 0.4.14
    notlegacy = ((major > 0) or (major == 0 and minor > 4) or
                 (major == 0 and minor == 4 and patch > 14))
    if notlegacy:
        vector = [str(major), ".", str(minor), ".", str(patch), ".", str(rcnum)]
        return "".join(vector)

    vector = [str(major), ".", str(minor)]
    if patch:
        vector.append(".")
        vector.append(str(patch))
    if rcnum < 999:
        vector.append("-rc")
        vector.append(str(rcnum))

    return "".join(vector)

def compare(left, right):

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

    return (decimal.Decimal(to_numeric(left)) -
           decimal.Decimal(to_numeric(right)))

CANONICAL_VERSION = '0.4.17.0'
NUMERIC_VERSION = to_numeric(CANONICAL_VERSION)
PRODUCT = 'Neubot %s' % CANONICAL_VERSION
HTTP_HEADER = 'Neubot/%s' % CANONICAL_VERSION

def main(args):
    ''' Main function '''
    try:
        options, arguments = getopt.getopt(args[1:], 'c')
    except getopt.error:
        sys.exit('usage: neubot utils_version [-c] [version...]')
    canonical = 0
    for opt in options:
        if opt[0] == '-c':
            canonical = 1

    if not arguments:
        if canonical:
            arguments = [NUMERIC_VERSION]
        else:
            arguments = [CANONICAL_VERSION]

    for argument in arguments:
        if canonical:
            sys.stdout.write('%s\n' % to_canonical(argument))
        else:
            sys.stdout.write('%s\n' % to_numeric(argument))

if __name__ == '__main__':
    main(sys.argv)
