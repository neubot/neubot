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

import asyncore
import collections
import logging

from neubot.net.poller import POLLER
from neubot.utils import T

INTERVAL = 10

class Notifier(object):
    def __init__(self):
        self._timestamps = collections.defaultdict(int)
        self._subscribers = collections.defaultdict(list)
        self._tofire = []

        POLLER.sched(INTERVAL, self._periodic)

    def subscribe(self, event, func, context=None, periodic=False):
        queue = self._subscribers[event]
        queue.append((func, context))
        if periodic:
            self._tofire.append(event)

    def publish(self, event, t=None):
        if not t:
            t = T()
        self._timestamps[event] = t

        logging.debug("* publish: %s" % event)

        #
        # WARNING! Please resist the temptation of merging
        # the [] and the del into a single pop() because that
        # will not work: this is a defaultdict and so here
        # event might not be in _subscribers.
        #
        queue = self._subscribers[event]
        del self._subscribers[event]

        self._fireq(event, queue)

    def _periodic(self, *args, **kwargs):
        POLLER.sched(INTERVAL, self._periodic)
        self._tofire, q = [], self._tofire
        for event in q:

            #
            # WARNING! Please resist the temptation of merging
            # the [] and the del into a single pop() because that
            # will not work: this is a defaultdict and so here
            # event might not be in _subscribers.
            #
            queue = self._subscribers[event]
            del self._subscribers[event]

            logging.debug("* periodic: %s" % event)

            self._fireq(event, queue)

    def _fireq(self, event, queue):
        for func, context in queue:
            try:
                func(event, context)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error(str(asyncore.compact_traceback()))

    def is_subscribed(self, event):
        return event in self._subscribers

    def get_event_timestamp(self, event):
        return str(self._timestamps[event])

    def needs_publish(self, event, timestamp):
        timestamp = int(timestamp)
        if timestamp < 0:
            raise ValueError("Invalid timestamp")
        return timestamp == 0 or timestamp < self._timestamps[event]

    def snap(self, d):
        d['notifier'] = {'_timestamps': dict(self._timestamps),
          '_subscribers': dict(self._subscribers)}

NOTIFIER = Notifier()
