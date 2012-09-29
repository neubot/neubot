# neubot/connector.py

#
# Copyright (c) 2010-2012 Simone Basso <bassosimone@gmail.com>,
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

''' Pollable socket connector '''

# Adapted from neubot/net/stream.py
# Python3-ready: yes

import collections

from neubot.pollable import Pollable
from neubot.poller import POLLER

from neubot import utils_net
from neubot import utils

class Connector(Pollable):

    ''' Pollable socket connector '''

    def __init__(self, parent, endpoint, prefer_ipv6, sslconfig, extra):
        Pollable.__init__(self)

        self.epnts = collections.deque()
        self.parent = parent
        self.prefer_ipv6 = prefer_ipv6
        self.sslconfig = sslconfig
        self.extra = extra
        self.sock = None
        self.timestamp = 0
        self.watchdog = 10

        # For logging purpose, save original endpoint
        self.endpoint = endpoint

        if " " in endpoint[0]:
            for address in endpoint[0].split():
                tmp = (address.strip(), endpoint[1])
                self.epnts.append(tmp)
        else:
            self.epnts.append(endpoint)

        self._connect()

    def __repr__(self):
        return str(self.endpoint)

    def _connection_failed(self):
        ''' Failed to connect first available epnt '''
        if self.sock:
            POLLER.unset_writable(self)
            self.sock = None  # MUST be below unset_writable()
        self.epnts.popleft()
        if not self.epnts:
            self.parent.handle_connect_error(self)
            return
        self._connect()

    def _connect(self):
        ''' Connect first available epnt '''
        sock = utils_net.connect(self.epnts[0], self.prefer_ipv6)
        if sock:
            self.sock = sock
            self.timestamp = utils.ticks()
            POLLER.set_writable(self)
        else:
            self._connection_failed()

    def fileno(self):
        return self.sock.fileno()

    def handle_write(self):
        POLLER.unset_writable(self)

        if not utils_net.isconnected(self.endpoint, self.sock):
            self._connection_failed()
            return

        self.parent.handle_connect(self, self.sock,
               (utils.ticks() - self.timestamp),
               self.sslconfig, self.extra)

    def handle_close(self):
        self._connection_failed()
