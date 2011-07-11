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

import os

from neubot.notify import NOTIFIER
from neubot import utils

# states of neubot
STATES = ( "idle", "rendezvous", "negotiate", "test", "collect" )

# name of 'state changed' notification
STATECHANGE = "statechange"

class State(object):
    def __init__(self, publish=NOTIFIER.publish, T=utils.T):
        self._publish = publish
        self._T = T

        self.current = ""
        self.events = {}
        self.t = self._T()

        self.update("since", utils.timestamp())
        self.update("pid", os.getpid())

    def dictionarize(self):
        return {
                "events": self.events,
                "current": self.current,
                "t": self.t,
               }

    def update(self, name, event=None, publish=True):
        if not event:
            event = {}

        if name in STATES:
            self.current = name
        self.t = self._T()
        self.events[name] = event

        if publish:
            self._publish(STATECHANGE, self.t)

STATE = State()
