# neubot/notify.py

#
# Copyright (c) 2010-2011 Simone Basso <bassosimone@gmail.com>,
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
# Subscribe/publish events
# Initially an event has a timestamp of zero, and each time
# you publish an event its timestamp is updated to the current
# time, using T().
#

import collections

from neubot.net.poller import POLLER
from neubot.utils import T
from neubot.log import LOG

INTERVAL = 10

RENEGOTIATE = "renegotiate"
STATECHANGE = "statechange"
TESTDONE = "testdone"


class Notifier:
    def __init__(self):
        POLLER.sched(INTERVAL, self.periodic)
        self.timestamps = collections.defaultdict(int)
        self.subscribers = collections.defaultdict(list)

    def subscribe(self, event, func, context):
        queue = self.subscribers[event]
        queue.append((func, context))

    def publish(self, event, t=None):
        if not t:
            t = T()
        self.timestamps[event] = t

        queue = self.subscribers[event]
        del self.subscribers[event]

        self.fireq(event, queue)

    def periodic(self):
        POLLER.sched(INTERVAL, self.periodic)

        subscribers = self.subscribers
        self.subscribers = collections.defaultdict(list)

        for event, queue in subscribers.items():
            # XXX XXX XXX
            if event == TESTDONE:
                self.subscribers[event] = queue
                continue
            self.fireq(event, queue)

    def fireq(self, event, queue):
        for func, context in queue:
            try:
                func(event, context)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                LOG.exception()

    def get_event_timestamp(self, event):
        return str(self.timestamps[event])

    def needs_publish(self, event, timestamp):
        timestamp = int(timestamp)
        if timestamp < 0:
            raise ValueError("Invalid timestamp")
        return timestamp == 0 or timestamp < self.timestamps[event]


NOTIFIER = Notifier()

### BEGIN DEPRECATED ###
notifier = NOTIFIER
subscribe = notifier.subscribe
publish = notifier.publish
periodic = notifier.periodic
get_event_timestamp = notifier.get_event_timestamp
needs_publish = notifier.needs_publish
### END DEPRECATED ###
