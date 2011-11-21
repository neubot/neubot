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

''' Regression tests for neubot/bittorrent/config.py '''

import unittest
import sys

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.bittorrent import config
from neubot.bittorrent import estimate

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

# pylint: disable=R0904
class TestPROPERTIES(unittest.TestCase):

    ''' Make sure we support all and only the expected properties '''

    def test_properties(self):

        ''' Make sure we support all and only the expected properties '''

        properties = tuple([ item[0] for item in config.PROPERTIES ])
        self.assertEquals(properties, PROPERTIES)

# pylint: disable=R0904
class TestFinalizeConf(unittest.TestCase):

    ''' Make sure that finalize_conf() works as expected '''

    def test_finalize_client(self):
        ''' Test finalize conf in the client case '''

        conf = {
                'bittorrent.my_id': '',
                'bittorrent.infohash': '',
                'bittorrent.bytes.down': 0,
                'bittorrent.bytes.up': 0,
                'bittorrent.listen': False,
                'bittorrent.address': '',
               }

        config.finalize_conf(conf)

        self.assertTrue(len(conf['bittorrent.my_id']), 20)
        self.assertTrue(len(conf['bittorrent.infohash']), 20)
        self.assertEqual(conf['bittorrent.bytes.down'], estimate.DOWNLOAD)
        self.assertEqual(conf['bittorrent.bytes.up'], estimate.UPLOAD)
        self.assertEqual(conf['bittorrent.address'], 'neubot.blupixel.net')

    def test_finalize_server(self):
        ''' Test finalize conf in the server case '''

        conf = {
                'bittorrent.my_id': '',
                'bittorrent.infohash': '',
                'bittorrent.bytes.down': 0,
                'bittorrent.bytes.up': 0,
                'bittorrent.listen': True,
                'bittorrent.address': '',
               }

        config.finalize_conf(conf)

        self.assertTrue(len(conf['bittorrent.my_id']), 20)
        self.assertTrue(len(conf['bittorrent.infohash']), 20)
        self.assertEqual(conf['bittorrent.bytes.down'], estimate.DOWNLOAD)
        self.assertEqual(conf['bittorrent.bytes.up'], estimate.UPLOAD)
        self.assertEqual(conf['bittorrent.address'], '0.0.0.0')

if __name__ == '__main__':
    unittest.main()
