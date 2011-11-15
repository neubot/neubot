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

''' Regression test for neubot/bittorrent/sched.py '''

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.bittorrent.sched import _sched_piece

# pylint: disable=R0904
class TestSchedPiece(unittest.TestCase):

    ''' Tests BitTorrent pieces scheduler '''

    def test_checks_parameters(self):
        ''' Make sure it raises RuntimeError if passed invalid parameters '''
        idx = (i for i in xrange(64))
        sched = _sched_piece(idx, 19, 16, 81)
        self.assertRaises(RuntimeError, next, sched)

    def test_works_well(self):
        ''' Make sure that _sched_piece() works well '''

        idx = (i for i in xrange(64))
        sched = _sched_piece(idx, 19, 16, 8)

        self.assertEquals(next(sched), (0, 0, 8))
        self.assertEquals(next(sched), (0, 8, 8))
        self.assertEquals(next(sched), (1, 0, 3))

if __name__ == '__main__':
    unittest.main()
