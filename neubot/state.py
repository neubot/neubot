# neubot/state.py

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

''' State of the test '''

import os
import logging

from neubot.notify import NOTIFIER
from neubot import utils

STATES = ( "idle", "rendezvous", "negotiate", "test", "collect" )
STATECHANGE = "statechange"

class State(object):
    ''' State of the test '''

    def __init__(self, publish=NOTIFIER.publish, time=utils.T):
        self.publish = publish
        self.time = time

        self.current = ""
        self.events = {}
        self.tsnap = self.time()

        self.update("since", utils.timestamp())
        self.update("pid", os.getpid())

    def dictionarize(self):
        ''' Transforms the state to a dictionary '''
        return {
                "events": self.events,
                "current": self.current,
                "t": self.tsnap,
               }

    def update(self, name, event=None, publish=True):
        ''' Updates test state '''
        if not event:
            event = {}

        if name in STATES:
            self.current = name
        self.tsnap = self.time()
        self.events[name] = event

        logging.debug("state: %s %s", name, event)

        if publish:
            self.publish(STATECHANGE, self.tsnap)

STATE = State()
