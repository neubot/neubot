# mod_library_net/net/connector.py

#
# Copyright (c) 2010-2012, 2014
#   Nexa Center for Internet & Society, Politecnico di Torino (DAUIN)
#   Simone Basso <bassosimone@gmail.com>.
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

""" Stream connector """

import collections

from neubot.pollable import Pollable
from neubot import utils_net
from neubot import utils

class ConnectorSimple(Pollable):
    """ Stream connector """

    def __init__(self, poller, parent):
        Pollable.__init__(self)
        self._poller = poller
        self._parent = parent
        self._sock = None
        self._ticks = 0.0
        self._endpoint = None
        self.set_timeout(10)

    def __repr__(self):
        return "Connector(%s)" % str(self._endpoint)

    def _connection_failed(self):
        """ Invoked when the connection is failed """
        if self._sock:
            self._poller.unset_writable(self)
            self._sock = None
        self._parent.connection_failed(self, None)

    def connect(self, endpoint, conf=None):
        """ Connect to the specified endpoint """

        self._endpoint = endpoint

        if not conf:
            conf = {}

        if " " in self._endpoint[0]:
            raise RuntimeError("%s: spaces in address not supported", self)

        #
        # API changed: we don't check CONFIG["prefer_ipv6"] anymore.
        #
        prefer_ipv6 = conf.get("prefer_ipv6", False)
        sock = utils_net.connect(self._endpoint, prefer_ipv6)
        if not sock:
            self._connection_failed()
            return

        self._sock = sock
        self._ticks = utils.ticks()
        self._poller.set_writable(self)

    def fileno(self):  # Part of the Pollable object model
        return self._sock.fileno()

    def handle_write(self):  # Part of the Pollable object model

        if not utils_net.isconnected(self._endpoint, self._sock):
            self._connection_failed()
            return

        self._poller.unset_writable(self)
        connect_time = utils.ticks() - self._ticks
        self._parent.connection_made(self._sock, self._endpoint,
          connect_time)

    def handle_close(self):  # Part of the Pollable object model
        self._connection_failed()

    def handle_read(self):  # Part of the Pollable object model
        raise RuntimeError("Unexpected event")

class Connector(object):
    """ Connector conformant with Neubot API """

    #
    # Neubot has had the feature of trying to connect() to a list of
    # addresses, e.g., 'master.neubot.org master2.neubot.org', for
    # quite some time now. This is why this class implements that behavior.
    #

    def __init__(self, poller, parent):
        self._poller = poller
        self._parent = parent
        self._connector = None
        self._conf = {}
        self._endpoints = collections.deque()

    def connect(self, endpoint, conf=None):
        """ Connect to the specified endpoint """

        if conf:
            self._conf = conf

        for address in endpoint[0].split():
            self._endpoints.append((address, endpoint[1]))

        self._connect_next()

    def _connect_next(self):
        """ Connect the next available endpoint """
        if not self._endpoints:
            self._parent.connection_failed(self, None)
            return
        endpoint = self._endpoints.popleft()
        self._connector = ConnectorSimple(self._poller, self)
        self._connector.connect(endpoint, self._conf)

    def connection_failed(self, error):
        """ Called when the connect() attempt fails """
        self._connector = None
        self._connect_next()

    def connection_made(self, sock, endpoint, rtt):
        """ Called when the connect() attempt succeeds """
        self._connector = None
        self._parent.connection_made(sock, endpoint, rtt)

    def set_timeout(self, timeo):
        """ Set timeout """
        if self._connector:
            self._connector.set_timeout(timeo)
