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

''' Unit test for neubot/state.py '''

import unittest
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import state

class TestState(unittest.TestCase):

    ''' Unit test for state.State '''

    def test_update_event(self):
        """Make sure we correctly set the empty event"""
        thestate = state.State(publish=lambda e, t: None)
        thestate.update("foobar")
        self.assertEquals(thestate.events["foobar"], {})

    def test_publish(self):
        """Make sure we publish when requested to do so"""
        count = [-1]

        def do_publish(event, timestamp):
            ''' convenience function '''
            count[0] = count[0] + 1

        thestate = state.State(publish=do_publish)
        thestate.update("foobar")

        # Because the ctor performs two internal update()s
        self.assertEquals(count[0], 2)

    def test_dont_publish(self):
        """Make sure we DON'T publish when not requested to do so"""
        count = [-1]

        def do_publish(event, timestamp):
            ''' convenience function '''
            count[0] = count[0] + 1

        thestate = state.State(publish=do_publish)
        thestate.update("foobar", publish=False)

        self.assertEquals(count[0], 1)

    def test_constants(self):
        """Make sure the constants have not changed"""

        self.assertEquals(state.STATES, ("idle", "rendezvous",
                                         "negotiate", "test",
                                         "collect"))

        self.assertEquals(state.STATECHANGE, "statechange")

    def test_current(self):
        """Make sure we honour current"""
        thestate = state.State(publish=lambda e, t: None)
        thestate.update("idle")
        self.assertEquals(thestate.current, "idle")

    def test_dictionarize(self):
        """Make sure we dictionarize to the expected format"""

        thestate = state.State(publish=lambda e, t: None, time=lambda: 42)
        thestate.update("foobar", {"a": True, "b": 1.7, "c": 13})
        thestate.update("since", 1234567890)
        thestate.update("xo")

        thestate.update("idle")

        self.assertEquals(thestate.dictionarize(),
                                            {
                                             "current": "idle",
                                             "events": {
                                                        "since": 1234567890,
                                                        "pid": os.getpid(),
                                                        "foobar": {
                                                                   "a": True,
                                                                   "b": 1.7,
                                                                   "c": 13,
                                                                  },
                                                        "xo": {},
                                                        "idle": {},
                                                       },
                                             "t": 42,
                                            })

if __name__ == "__main__":
    unittest.main()
