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

import collections
import logging
import neubot

INTERVAL = 15

STATECHANGE = "statechange"

class Notifier:
    def __init__(self):
        neubot.net.sched(INTERVAL, self.periodic)
        self.subscribers = {}

    def subscribe(self, event, func, context):
        if not self.subscribers.has_key(event):
            queue = collections.deque()
            self.subscribers[event] = queue
        else:
            queue = self.subscribers[event]
        queue.append((func, context))

    #
    # XXX Below we surround func() with try..except and this is
    # intended to work-around the fact that the server will crash
    # if there is a pending comet response for which the client
    # has closed the connection.  The right solution is to modify
    # the existing code to deal with this new case--but, for now,
    # it is sufficient to intercept the issue here.
    # We define this problem Comet-after-close because it happens
    # when we try to send a comet response _and_ the peer has al-
    # ready closed the connection.
    #

    def publish(self, event):
        if self.subscribers.has_key(event):
            for func, context in self.subscribers[event]:
                try:
                    func(event, context)
                except:
                    logging.warning("Possible Comet-after-close problem")
                    neubot.utils.prettyprint_exception()
            del self.subscribers[event]

    def periodic(self):
        neubot.net.sched(INTERVAL, self.periodic)
        for event, queue in self.subscribers.items():
            for func, context in queue:
                try:
                    func(event, context)
                except:
                    logging.warning("Possible Comet-after-close problem")
                    neubot.utils.prettyprint_exception()
        self.subscribers = {}

notifier = Notifier()
subscribe = notifier.subscribe
publish = notifier.publish
periodic = notifier.periodic
