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

''' Regression test for neubot/bittorrent/btsched.py '''

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.bittorrent.bitfield import make_bitfield
from neubot.bittorrent.btsched import _sched_piece
from neubot.bittorrent.btsched import sched_idx

# pylint: disable=R0904
class TestSchedIdx(unittest.TestCase):

    ''' Tests BitTorrent index scheduler '''

    def test_check_lengths(self):
        ''' Make sure the index scheduler checks lengths '''
        bitfield = make_bitfield(17)
        peer_bitfield = make_bitfield(71)
        schedidx = sched_idx(bitfield, peer_bitfield)
        self.assertRaises(AssertionError, schedidx.next)

    def test_works_well(self):
        ''' Make sure the index scheduler works well '''
        bitfield = make_bitfield(4096)
        peer_bitfield = make_bitfield(4096)

        # Find each free slot and consider each bit inside it
        expect = []
        for index in range(len(bitfield.bits)):
            if not bitfield.bits[index] and peer_bitfield.bits[index]:
                for shift in range(8):
                    expect.append(index * 8 + shift)

        # The real code should behave in the same way, but randomly
        seen = []
        for index in sched_idx(bitfield, peer_bitfield):
            seen.append(index)
        seen = sorted(seen)

        # Let's see
        self.assertEqual(expect, seen)

# pylint: disable=R0904
class TestSchedPiece(unittest.TestCase):

    ''' Tests BitTorrent pieces scheduler '''

    def test_checks_parameters(self):
        ''' Make sure it raises RuntimeError if passed invalid parameters '''
        idx = (i for i in xrange(64))
        sched = _sched_piece(idx, 19, 16, 81)
        self.assertRaises(RuntimeError, sched.next)

    def test_works_well(self):
        ''' Make sure that _sched_piece() works well '''

        idx = (i for i in xrange(64))
        sched = _sched_piece(idx, 19, 16, 8)

        self.assertEquals(sched.next(), (0, 0, 8))
        self.assertEquals(sched.next(), (0, 8, 8))
        self.assertEquals(sched.next(), (1, 0, 3))

if __name__ == '__main__':
    unittest.main()
