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

''' Regression test for neubot/poller.py '''

import sys
import unittest

if __name__ == '__main__':
    sys.path.insert(0, '.')

from neubot.poller import Poller

class TestCheckTimeoutStream(object):
    ''' Fake stream for TestCheckTimeout '''

    def __init__(self, result, fileno):
        '''Initialize fake stream '''
        self._result = result
        self._fileno = fileno

    def fileno(self):
        ''' Return file number '''
        return self._fileno

    def handle_periodic(self, timenow):
        ''' Return True if this stream has run for too much
            time and must be pruned '''
        #
        # We want to prune all odd streams and make sure that
        # even ones are still tracked by the poller.
        #
        return self._fileno % 2

    def handle_close(self):
        ''' Invoked when this stream is closed '''
        # Tell parent class this stream has been closed
        self._result.append(self._fileno)

    def __str__(self):
        ''' String representation of this stream '''
        return "stream %d" % self._fileno

class TestCheckTimeout(unittest.TestCase):
    ''' Regression test for poller.check_timeout() '''

    def test_readable(self):
        ''' Make sure it runs when there's only readable stuff '''
        poller = Poller(1)
        result = []
        stream = TestCheckTimeoutStream(result, 1)
        poller.readset[1] = stream
        poller.check_timeout()
        self.assertEqual(result, [1])

    def test_writable(self):
        ''' Make sure it runs when there's only writable stuff '''
        poller = Poller(1)
        result = []
        stream = TestCheckTimeoutStream(result, 1)
        poller.writeset[1] = stream
        poller.check_timeout()
        self.assertEqual(result, [1])

    def test_complete(self):
        ''' Make sure it works with both readable and writable streams '''
        poller = Poller(1)
        result = []

        #
        # Insert a number of streams, make all of them readable
        # and just a subset writable.  The partial overlap is to
        # make sure that readable, writable and read-writable
        # streams are all processed correctly.
        #
        for i in range(256):
            stream = TestCheckTimeoutStream(result, i)
            poller.readset[i] = stream
            if i > 14 and i < 128:
                poller.writeset[i] = stream

        # This should close odd streams only
        poller.check_timeout()

        # Check we have closed the right streams
        self.assertEqual(sorted(result), range(1, 256, 2))

        # Make sure the readable set is consistent
        self.assertEqual(sorted(poller.readset), range(0, 256, 2))

        # Make sure the writable set is consistent
        self.assertEqual(sorted(poller.writeset), range(16, 128, 2))

if __name__ == '__main__':
    unittest.main()
