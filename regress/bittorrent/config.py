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

#
# Regression tests for neubot/bittorrent/config.py
#

import unittest
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.bittorrent import config

PROPERTIES = (
    'bittorrent.address',
    'bittorrent.bytes.down',
    'bittorrent.bytes.up',
    'bittorrent.daemonize',
    'bittorrent.infohash',
    'bittorrent.listen',
    'bittorrent.negotiate',
    'bittorrent.negotiate.port',
    'bittorrent.my_id',
    'bittorrent.numpieces',
    'bittorrent.piece_len',
    'bittorrent.port',
    'bittorrent.watchdog',
)

class TestPROPERTIES(unittest.TestCase):
    def runTest(self):
        """Make sure we support all and only the expected properties"""
        p = tuple(map(lambda t: t[0], config._PROPERTIES))
        self.assertEquals(p, PROPERTIES)

if __name__ == "__main__":
    unittest.main()
