#!/usr/bin/env python

#
# Copyright (c) 2012 Simone Basso <bassosimone@gmail.com>,
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

''' Regression test for runner_tests module '''

# Formerly runner_lst.py

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.runner_tests import RunnerTests

class RegressionTest(unittest.TestCase):
    ''' Regression test for runner_tests module '''

    #
    # We have too many public methods and we know that
    # pylint: disable=R0904
    #

    def test_when_empty(self):
        ''' Check behavior is correct when empty '''
        # It should return None in both cases
        lst = RunnerTests()
        self.assertTrue(len(lst.test_to_negotiate_uri('foo')) > 10)

if __name__ == '__main__':
    unittest.main()
