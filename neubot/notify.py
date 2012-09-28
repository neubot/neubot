# neubot/notify.py

#
# Copyright (c) 2010-2012
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

''' Subscribe/publish events '''

#
# Initially an event has a timestamp of zero, and each time
# you publish an event its timestamp is updated to the current
# time, using T().
#

import collections
import logging

from neubot.poller import POLLER
from neubot import utils

INTERVAL = 60

class Notifier(object):
    ''' Notify events '''

    def __init__(self):
        self._timestamps = collections.defaultdict(int)
        self._subscribers = collections.defaultdict(list)
        self._tofire = []
        POLLER.sched(INTERVAL, self._periodic)

    def subscribe(self, event, func, context=None, periodic=False):
        ''' Subscribe to event '''
        queue = self._subscribers[event]
        queue.append((func, context))
        if periodic:
            self._tofire.append(event)

    def publish(self, event, tsnap=None):
        ''' Publish event '''
        if not tsnap:
            tsnap = utils.T()
        self._timestamps[event] = tsnap

        logging.debug("notify: publish event: %s", event)

        #
        # WARNING! Please resist the temptation of merging
        # the [] and the del into a single pop() because that
        # will not work: this is a defaultdict and so here
        # event might not be in _subscribers.
        #
        queue = self._subscribers[event]
        del self._subscribers[event]

        self._fireq(event, queue)

    def _periodic(self):
        ''' Periodically generate notification for old events '''
        POLLER.sched(INTERVAL, self._periodic)
        self._tofire, queue = [], self._tofire
        for event in queue:

            #
            # WARNING! Please resist the temptation of merging
            # the [] and the del into a single pop() because that
            # will not work: this is a defaultdict and so here
            # event might not be in _subscribers.
            #
            queue = self._subscribers[event]
            del self._subscribers[event]

            logging.debug("notify: periodically publish event: %s", event)

            self._fireq(event, queue)

    @staticmethod
    def _fireq(event, queue):
        ''' Notify all funcs in queue of event '''
        for func, context in queue:
            try:
                func(event, context)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                logging.error('notify: event func() failed', exc_info=1)

    def is_subscribed(self, event):
        ''' Returns True if the event is subscribed '''
        return event in self._subscribers

    def get_event_timestamp(self, event):
        ''' Returns the timestamp bound to an event '''
        return str(self._timestamps[event])

    def needs_publish(self, event, timestamp):
        ''' Returns True if an event needs to be published '''
        timestamp = int(timestamp)
        if timestamp < 0:
            raise ValueError("Invalid timestamp")
        return timestamp == 0 or timestamp < self._timestamps[event]

    def snap(self, dct):
        ''' Take a snapshot of this object '''
        dct['notifier'] = {'_timestamps': dict(self._timestamps),
          '_subscribers': dict(self._subscribers)}

NOTIFIER = Notifier()
