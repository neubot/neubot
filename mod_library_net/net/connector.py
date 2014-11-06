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

from neubot.pollable import Pollable
from neubot import utils_net
from neubot import utils

class Connector(Pollable):
    """ Stream connector """

    def __init__(self, poller, parent):
        Pollable.__init__(self)
        self._poller = poller
        self._parent = parent
        self._sock = None
        self._ticks = 0.0
        self._endpoint = None
        self.watchdog = 10  # Override default specified by Pollable

    def __repr__(self):
        return "Connector(%s)" % str(self._endpoint)

    def _connection_failed(self):
        """ Invoked when the connection is failed """
        if self._sock:
            self._poller.unset_writable(self)
            self._sock = None
        self._parent.connection_failed(self, None)

    def connect(self, address, port, conf=None):  # API changed
        """ Connect to the specified endpoint """

        endpoint = (address, port)

        if not conf:
            conf = {}

        if " " in address:
            raise RuntimeError("%s: spaces in address not supported", self)

        self._endpoint = endpoint
        prefer_ipv6 = conf.get("prefer_ipv6", False)
        sock = utils_net.connect(endpoint, prefer_ipv6)
        if not sock:
            self._connection_failed()
            return

        self._sock = sock
        self._ticks = utils.ticks()
        self._poller.set_writable(self)

    def fileno(self):  # Part of the Pollable object model
        return self._sock.fileno()

    def handle_write(self):  # Part of the Pollable object model
        self._poller.unset_writable(self)

        if not utils_net.isconnected(self._endpoint, self._sock):
            self._connection_failed()
            return

        rtt = utils.ticks() - self._ticks
        self._parent.connection_made(self._sock, self._endpoint, rtt)

    def handle_close(self):
        self._connection_failed()
