# neubot/speedtest/session.py

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

import collections
from neubot.log import LOG
from neubot.net.poller import POLLER
from neubot import utils

class SessionState(object):
    def __init__(self):
        self.active = False
        self.timestamp = 0
        self.identifier = None
        self.queuepos = 0
        self.negotiations = 0

    def __repr__(self):
        return self.identifier

class SessionTracker(object):
    def __init__(self):
        self.identifiers = {}
        self.queue = collections.deque()
        self.connections = {}
        self.task = None

    def _sample_queue_length(self):
        LOG.info("SessionTracker: queue length: %d\n" % len(self.queue))
        self.task = POLLER.sched(60, self._sample_queue_length)

    def session_active(self, identifier):
        if identifier in self.identifiers:
            session = self.identifiers[identifier]
            session.timestamp = utils.timestamp()       # XXX
            return session.active
        return False

    def session_prune(self):
        stale = []
        now = utils.timestamp()
        for session in self.queue:
            if now - session.timestamp > 30:
                stale.append(session)
        if not stale:
            return False
        for session in stale:
            self._do_remove(session)
        return True

    def session_delete(self, identifier):
        if identifier in self.identifiers:
            session = self.identifiers[identifier]
            self._do_remove(session)

    def session_negotiate(self, identifier):
        if not identifier in self.identifiers:
            session = SessionState()
            # XXX collision is not impossible but very unlikely
            session.identifier = utils.get_uuid()
            session.timestamp = utils.timestamp()
            self._do_add(session)
        else:
            session = self.identifiers[identifier]
        session.negotiations += 1
        return session

    def _do_add(self, session):
        self.identifiers[session.identifier] = session
        session.queuepos = len(self.queue)
        self.queue.append(session)
        self._do_update_queue()

    def _do_remove(self, session):
        del self.identifiers[session.identifier]
        self.queue.remove(session)
        self._do_update_queue()

    def _do_update_queue(self):

        pos = 1
        for session in self.queue:
            if pos <= 3 and not session.active:
                session.active = True
            session.queuepos = pos
            pos = pos + 1

        if not self.task:
            self.task = POLLER.sched(60, self._sample_queue_length)

    def register_connection(self, connection, identifier):
        if not connection in self.connections:
            if identifier in self.identifiers:
                self.connections[connection] = identifier

    def unregister_connection(self, connection):
        if connection in self.connections:
            identifier = self.connections[connection]
            del self.connections[connection]
            if identifier in self.identifiers:
                session = self.identifiers[identifier]
                self._do_remove(session)

TRACKER = SessionTracker()
