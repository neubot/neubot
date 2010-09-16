# neubot/notify.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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
# Subscribe/publish events
#

from collections import deque
from neubot.net.pollers import sched
from neubot import log

INTERVAL = 10

RENEGOTIATE = "renegotiate"
STATECHANGE = "statechange"

class Notifier:
    def __init__(self):
        sched(INTERVAL, self.periodic)
        self.subscribers = {}

    def subscribe(self, event, func, context):
        if not self.subscribers.has_key(event):
            queue = deque()
            self.subscribers[event] = queue
        else:
            queue = self.subscribers[event]
        queue.append((func, context))

    def publish(self, event):
        if self.subscribers.has_key(event):
            queue = self.subscribers[event]
            del self.subscribers[event]
            for func, context in queue:
                func(event, context)

    def periodic(self):
        sched(INTERVAL, self.periodic)
        subscribers = self.subscribers
        self.subscribers = {}
        for event, queue in subscribers.items():
            for func, context in queue:
                func(event, context)

notifier = Notifier()
subscribe = notifier.subscribe
publish = notifier.publish
periodic = notifier.periodic
