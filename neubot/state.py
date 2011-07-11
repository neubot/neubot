# neubot/state.py

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

import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, ".")

from neubot.notify import NOTIFIER
from neubot import utils

# states of neubot
STATES = [ "idle", "rendezvous", "negotiate", "test", "collect" ]

# name of 'state changed' notification
STATECHANGE = "statechange"

class State(object):
    def __init__(self):
        self.current = ""
        self.events = {}
        self.t = utils.T()

        self.update("since", utils.timestamp())
        self.update("pid", os.getpid())

    def dictionarize(self):
        return vars(self)

    def update(self, name, event=None, publish=True):
        if not event:
            event = {}

        if name in STATES:
            self.current = name
        self.t = utils.T()
        self.events[name] = event

        if publish:
            NOTIFIER.publish(STATECHANGE, self.t)

STATE = State()

if __name__ == "__main__":
    import pprint

    STATE.update("update", {"version": "0.4.1",
      "uri": "http://www.example.com/"})
    STATE.update("idle")
    pprint.pprint(STATE.dictionarize())

    STATE.update("rendezvous")
    pprint.pprint(STATE.dictionarize())

    STATE.update("rendezvous", {"status": "failed"})
    pprint.pprint(STATE.dictionarize())

    STATE.update("idle")
    pprint.pprint(STATE.dictionarize())

    STATE.update("rendezvous")
    pprint.pprint(STATE.dictionarize())

    STATE.update("negotiate", {"queue_pos": 3, "queue_len": 7})
    pprint.pprint(STATE.dictionarize())

    STATE.update("negotiate", {"queue_pos": 2, "queue_len": 8})
    pprint.pprint(STATE.dictionarize())

    STATE.update("negotiate", {"queue_pos": 1, "queue_len": 7})
    pprint.pprint(STATE.dictionarize())

    STATE.update("speedtest_latency", {"avg": 0.013, "unit": "s"})
    pprint.pprint(STATE.dictionarize())

    STATE.update("speedtest_download", {"avg": 6.94, "unit": "Mbit/s"})
    pprint.pprint(STATE.dictionarize())

    STATE.update("speedtest_upload", {"avg": 0.97, "unit": "Mbit/s"})
    pprint.pprint(STATE.dictionarize())

    STATE.update("collect")
    pprint.pprint(STATE.dictionarize())

    STATE.update("idle")
    pprint.pprint(STATE.dictionarize())
