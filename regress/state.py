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

import unittest
import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot import state

class TestState(unittest.TestCase):

    def test_update_event(self):
        """Make sure we correctly set the empty event"""
        s = state.State(publish=lambda e, t: None)
        s.update("foobar")
        self.assertEquals(s._events["foobar"], {})

    def test_publish(self):
        """Make sure we publish when requested to do so"""
        count = [-1]

        def do_publish(e, t):
            count[0] = count[0] + 1

        s = state.State(publish=do_publish)
        s.update("foobar")

        #XXX because the ctor performs two internal update()s
        self.assertEquals(count[0], 2)

    def test_dont_publish(self):
        """Make sure we DON'T publish when not requested to do so"""
        count = [-1]

        def do_publish(e, t):
            count[0] = count[0] + 1

        s = state.State(publish=do_publish)
        s.update("foobar", publish=False)

        #XXX because the ctor performs two internal update()s
        self.assertEquals(count[0], 1)

    def test_constants(self):
        """Make sure the constants have not changed"""

        self.assertEquals(state.STATES, ("idle", "rendezvous",
                                         "negotiate", "test",
                                         "collect"))

        self.assertEquals(state.STATECHANGE, "statechange")


    def test_current(self):
        """Make sure we honour current"""
        s = state.State(publish=lambda e, t: None)
        s.update("idle")
        self.assertEquals(s._current, "idle")

    def test_dictionarize(self):
        """Make sure we dictionarize to the expected format"""

        s = state.State(publish=lambda e, t: None, T=lambda: 42)
        s.update("foobar", {"a": True, "b": 1.7, "c": 13})
        s.update("since", 1234567890)
        s.update("xo")

        s.update("idle")

        self.assertEquals(s.dictionarize(), {
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
