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

''' Regression test for runner_lst module '''

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.runner_lst import RunnerLst

class RegressionTest(unittest.TestCase):
    ''' Regression test for runner_lst module '''

    #
    # We have too many public methods and we know that
    # pylint: disable=R0904
    #

    def test_when_empty(self):
        ''' Check behavior is correct when empty '''
        # It should return None in both cases
        lst = RunnerLst()
        self.assertEqual(lst.test_to_negotiate_uri('foo'), None)
        self.assertEqual(lst.get_next_test(), None)
        self.assertEqual(lst.get_test_names(), [])

    def test_test_to_negotiate_uri(self):
        ''' Check test_to_negotiate_uri works as expected '''
        #
        # It should always return the first URI: it suck but that is
        # how it works as of now.
        #
        lst = RunnerLst()
        lst.update({'foo': ['a', 'b', 'c']})
        self.assertEqual(lst.test_to_negotiate_uri('foo'), 'a')
        self.assertEqual(lst.test_to_negotiate_uri('foo'), 'a')
        self.assertEqual(lst.test_to_negotiate_uri('foo'), 'a')

    def test_get_next_test_simple(self):
        ''' Check get_next_test() works OK when we have just one test '''
        #
        # When we have just one test it should always return that
        # test name, I know that seems silly but we need to ensure
        # it works OK because that is a special case in the code.
        #
        lst = RunnerLst()
        lst.update({'foo': ['a', 'b', 'c']})
        self.assertEqual(lst.get_next_test(), 'foo')
        self.assertEqual(lst.get_next_test(), 'foo')
        self.assertEqual(lst.get_next_test(), 'foo')

    def test_get_next_test(self):
        ''' Check get_next_test() works OK when we have more than one test '''
        #
        # When we have more than one test, it should not return the
        # same test two times in a row.  Not so clever, but that's
        # the way the current code is working.
        #
        lst = RunnerLst()
        lst.update({'foo': ['a', 'b', 'c'], 'bar': ['a', 'b', 'c']})
        nxt = lst.get_next_test()
        self.assertNotEqual(lst.get_next_test(), nxt)

    def test_get_test_names(self):
        ''' Check get_test_names() behavior '''
        lst = RunnerLst()
        self.assertEqual(lst.get_test_names(), [])
        lst.update({'foo': ['a']})
        self.assertEqual(lst.get_test_names(), ['foo'])
        lst.update({'foo': ['a'], 'bar': ['b']})
        self.assertEqual(lst.get_test_names(), ['foo', 'bar'])

if __name__ == '__main__':
    unittest.main()
